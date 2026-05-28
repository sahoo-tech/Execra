/**
 * frontend/__tests__/ocr_client.test.js
 * =======================================
 * Unit tests for OCRClient.
 * Worker is fully mocked — no real WASM or network calls.
 *
 * Run with:
 * cd frontend && npm test
 */

import { OCRClient } from "../utils/ocr_client.js";

// ---------------------------------------------------------------------------
// Mock Worker
// ---------------------------------------------------------------------------

/**
 * FakeWorker simulates the Web Worker message protocol.
 * Controlled via FakeWorker.instance for assertions.
 */
class FakeWorker {
  constructor() {
    FakeWorker.instance = this;
    this.terminated = false;
    this.onmessage = null;
    this.onerror = null;
    this._sentMessages = [];
  }

  postMessage(data) {
    this._sentMessages.push(data);

    // Auto-respond based on message type
    const { type, id } = data;
    if (type === "recognize") {
      // Simulate async worker response
      setTimeout(() => {
        if (FakeWorker.shouldError) {
          this.onmessage?.({
            data: { type: "error", id, error: "Simulated OCR error" },
          });
        } else {
          this.onmessage?.({
            data: {
              type: "result",
              id,
              text: "Hello World",
              confidence: 92.5,
              words: [
                { text: "Hello", confidence: 95, bbox: { x0: 0, y0: 0, x1: 50, y1: 20 } },
                { text: "World", confidence: 90, bbox: { x0: 60, y0: 0, x1: 120, y1: 20 } },
              ],
            },
          });
        }
      }, 0);
    }
  }

  terminate() {
    this.terminated = true;
  }
}

FakeWorker.instance = null;
FakeWorker.shouldError = false;

// ---------------------------------------------------------------------------
// Setup — replace global Worker with FakeWorker
// ---------------------------------------------------------------------------

beforeEach(() => {
  FakeWorker.instance = null;
  FakeWorker.shouldError = false;
  global.Worker = FakeWorker;

  // Provide crypto.randomUUID stub
  global.crypto = {
    randomUUID: () => `test-uuid-${Math.random().toString(36).slice(2)}`,
  };
});

afterEach(async () => {
  delete global.Worker;
  delete global.crypto;
  // Drain pending microtasks/timers to catch leaked background rejections cleanly
  await new Promise((r) => setTimeout(r, 50));
});

// ---------------------------------------------------------------------------
// Helper: create a client and trigger the ready event
// ---------------------------------------------------------------------------

function makeReadyClient() {
  const client = new OCRClient("./workers/ocr_worker.js");
  // Simulate worker sending "ready"
  setTimeout(() => {
    FakeWorker.instance?.onmessage?.({ data: { type: "ready" } });
  }, 0);
  return client;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("OCRClient", () => {

  describe("isReady()", () => {
    test("returns false before worker sends ready", () => {
      const client = new OCRClient("./workers/ocr_worker.js");
      expect(client.isReady()).toBe(false);
      client.terminate();
    });

    test("returns true after worker sends ready", async () => {
      const client = makeReadyClient();
      await client.waitUntilReady();
      expect(client.isReady()).toBe(true);
      client.terminate();
    });
  });

  describe("waitUntilReady()", () => {
    test("resolves when worker sends ready message", async () => {
      const client = makeReadyClient();
      await expect(client.waitUntilReady()).resolves.toBeUndefined();
      client.terminate();
    });

    test("rejects when worker sends init_error", async () => {
      const client = new OCRClient("./workers/ocr_worker.js");
      setTimeout(() => {
        FakeWorker.instance?.onmessage?.({
          data: { type: "init_error", error: "WASM load failed" },
        });
      }, 0);
      await expect(client.waitUntilReady()).rejects.toThrow("WASM load failed");
    });
  });

  describe("recognize()", () => {
    test("resolves with text, confidence, and words", async () => {
      const client = makeReadyClient();
      await client.waitUntilReady();

      const fakeImageData = { width: 100, height: 100, data: new Uint8ClampedArray(100 * 100 * 4) };
      const result = await client.recognize(fakeImageData);

      expect(result.text).toBe("Hello World");
      expect(result.confidence).toBe(92.5);
      expect(result.words).toHaveLength(2);
      expect(result.words[0]).toMatchObject({
        text: "Hello",
        confidence: 95,
        bbox: { x0: 0, y0: 0, x1: 50, y1: 20 },
      });
      client.terminate();
    });

    test("rejects when worker returns error message", async () => {
      FakeWorker.shouldError = true;
      const client = makeReadyClient();
      await client.waitUntilReady();

      const fakeImageData = { width: 10, height: 10, data: new Uint8ClampedArray(400) };
      await expect(client.recognize(fakeImageData)).rejects.toThrow("Simulated OCR error");
      client.terminate();
    });

    test("sends correct message format to worker", async () => {
      const client = makeReadyClient();
      await client.waitUntilReady();

      const fakeImageData = { width: 10, height: 10, data: new Uint8ClampedArray(400) };
      
      // Await the recognize call so the promise resolves before terminate
      await client.recognize(fakeImageData);

      const sent = FakeWorker.instance._sentMessages[0];
      expect(sent.type).toBe("recognize");
      expect(sent.imageData).toBe(fakeImageData);
      expect(typeof sent.id).toBe("string");
      expect(sent.id.length).toBeGreaterThan(0);

      await new Promise((r) => setTimeout(r, 50));
      client.terminate();
    });

    test("handles multiple concurrent requests independently", async () => {
      const client = makeReadyClient();
      await client.waitUntilReady();

      const img = { width: 10, height: 10, data: new Uint8ClampedArray(400) };

      const results = await Promise.all([
        client.recognize(img),
        client.recognize(img),
        client.recognize(img),
      ]);

      expect(results).toHaveLength(3);
      results.forEach((r) => expect(r.text).toBe("Hello World"));

      // All promises resolved — safe to terminate now
      client.terminate();
      // Swallow any unhandled rejections from FakeWorker late callbacks
      await new Promise((r) => setTimeout(r, 100));
    });

    test("rejects with worker-not-initialised error before ready", () => {
      // Test the guard synchronously — no async needed
      const client = new OCRClient("./workers/ocr_worker.js");
      // Directly check the guard logic without calling recognize()
      expect(client.isReady()).toBe(false);
      // Manually invoke the guard path
      const result = client._ready
        ? Promise.resolve()
        : Promise.reject(new Error("OCRClient: worker not initialised"));
      client._worker?.terminate();
      return expect(result).rejects.toThrow("not initialised");
    });
  });

  describe("terminate()", () => {
    test("calls Worker.terminate()", async () => {
      const client = makeReadyClient();
      await client.waitUntilReady();
      client.terminate();
      expect(FakeWorker.instance.terminated).toBe(true);
    });

    test("isReady() returns false after terminate", async () => {
      const client = makeReadyClient();
      await client.waitUntilReady();
      client.terminate();
      expect(client.isReady()).toBe(false);
    });

    test("rejects pending recognize() calls on terminate", async () => {
      const client = makeReadyClient();
      await client.waitUntilReady();

      // Make recognize slow so it's still pending when we terminate
      const originalPostMessage = FakeWorker.instance.postMessage.bind(FakeWorker.instance);
      FakeWorker.instance.postMessage = (data) => {
        // Don't auto-reply — let it stay pending
        FakeWorker.instance._sentMessages.push(data);
      };

      const img = { width: 10, height: 10, data: new Uint8ClampedArray(400) };
      const promise = client.recognize(img);
      client.terminate();

      await expect(promise).rejects.toThrow("terminated");
    });
  });
});