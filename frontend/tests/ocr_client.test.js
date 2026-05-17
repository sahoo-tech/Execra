/**
 * Unit tests for OCRClient.
 *
 * The Web Worker API is not available in Jest's jsdom environment, so all
 * tests use a MockWorker that simulates the message-passing contract defined
 * by ocr_worker.js.
 */

import { OCRClient } from '../utils/ocr_client.js';

// ---------------------------------------------------------------------------
// MockWorker — simulates the Web Worker postMessage API
// ---------------------------------------------------------------------------

let mockWorkerInstance = null;

class MockWorker {
  constructor(path, options) {
    this.path = path;
    this.options = options;
    this.onmessage = null;
    this.onerror = null;
    this.terminate = jest.fn();
    this._postMessage = jest.fn();
    mockWorkerInstance = this;
  }

  postMessage(data) {
    this._postMessage(data);
  }

  /** Simulate an incoming message from the worker thread. */
  simulateMessage(data) {
    if (this.onmessage) this.onmessage({ data });
  }

  /** Simulate a fatal worker error. */
  simulateError(message) {
    if (this.onerror) this.onerror({ message });
  }
}

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  global.Worker = MockWorker;

  // Provide crypto.randomUUID in jsdom if absent.
  if (!global.crypto) {
    global.crypto = { randomUUID: () => `uuid-${Math.random()}` };
  } else if (typeof global.crypto.randomUUID !== 'function') {
    global.crypto.randomUUID = () => `uuid-${Math.random()}`;
  }

  mockWorkerInstance = null;
});

// ---------------------------------------------------------------------------
// Constructor / isReady
// ---------------------------------------------------------------------------

describe('constructor', () => {
  test('spawns a worker with the provided path and module type', () => {
    const client = new OCRClient('/workers/ocr_worker.js');

    expect(mockWorkerInstance).not.toBeNull();
    expect(mockWorkerInstance.path).toBe('/workers/ocr_worker.js');
    expect(mockWorkerInstance.options).toEqual({ type: 'module' });

    client.terminate();
  });

  test('isReady() returns true after successful construction', () => {
    const client = new OCRClient('/workers/ocr_worker.js');
    expect(client.isReady()).toBe(true);
    client.terminate();
  });

  test('isReady() returns false when Worker constructor throws', () => {
    global.Worker = function () {
      throw new Error('Worker not supported');
    };

    const client = new OCRClient('/workers/ocr_worker.js');
    expect(client.isReady()).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// recognize() — Promise resolution
// ---------------------------------------------------------------------------

describe('recognize', () => {
  test('resolves with text, confidence, and words on a successful result', async () => {
    const client = new OCRClient('/workers/ocr_worker.js');

    const recognizePromise = client.recognize('data:image/png;base64,abc');

    const [call] = mockWorkerInstance._postMessage.mock.calls;
    expect(call[0].type).toBe('recognize');
    expect(typeof call[0].id).toBe('string');
    expect(call[0].imageData).toBe('data:image/png;base64,abc');

    const { id } = call[0];

    mockWorkerInstance.simulateMessage({
      type: 'result',
      id,
      text: 'Hello World',
      confidence: 94.5,
      words: [{ text: 'Hello' }, { text: 'World' }],
    });

    const result = await recognizePromise;

    expect(result.text).toBe('Hello World');
    expect(result.confidence).toBe(94.5);
    expect(result.words).toHaveLength(2);

    client.terminate();
  });

  test('rejects when the worker sends an error response', async () => {
    const client = new OCRClient('/workers/ocr_worker.js');

    const recognizePromise = client.recognize('bad-image');

    const { id } = mockWorkerInstance._postMessage.mock.calls[0][0];

    mockWorkerInstance.simulateMessage({
      type: 'error',
      id,
      error: 'Unreadable image format.',
    });

    await expect(recognizePromise).rejects.toThrow('Unreadable image format.');

    client.terminate();
  });

  test('rejects immediately when the worker is not ready', async () => {
    global.Worker = function () {
      throw new Error('not supported');
    };

    const client = new OCRClient('/workers/ocr_worker.js');

    await expect(client.recognize('image')).rejects.toThrow(
      'OCR worker is not available.'
    );
  });

  test('handles multiple concurrent requests independently', async () => {
    const client = new OCRClient('/workers/ocr_worker.js');

    const p1 = client.recognize('frame-1');
    const p2 = client.recognize('frame-2');

    const calls = mockWorkerInstance._postMessage.mock.calls;
    const id1 = calls[0][0].id;
    const id2 = calls[1][0].id;

    expect(id1).not.toBe(id2);

    mockWorkerInstance.simulateMessage({
      type: 'result',
      id: id2,
      text: 'Second',
      confidence: 80,
      words: [],
    });

    mockWorkerInstance.simulateMessage({
      type: 'result',
      id: id1,
      text: 'First',
      confidence: 90,
      words: [],
    });

    const [r1, r2] = await Promise.all([p1, p2]);
    expect(r1.text).toBe('First');
    expect(r2.text).toBe('Second');

    client.terminate();
  });

  test('ignores messages with unknown ids', async () => {
    const client = new OCRClient('/workers/ocr_worker.js');

    const recognizePromise = client.recognize('image');

    // Send a response for an id that was never registered.
    mockWorkerInstance.simulateMessage({
      type: 'result',
      id: 'unknown-id-xyz',
      text: 'Stray',
      confidence: 50,
      words: [],
    });

    // Promise should still be pending; verify it doesn't resolve yet.
    let settled = false;
    recognizePromise.then(() => { settled = true; }).catch(() => { settled = true; });

    await new Promise((r) => setTimeout(r, 10));
    expect(settled).toBe(false);

    client.terminate();
  });
});

// ---------------------------------------------------------------------------
// Timeout handling
// ---------------------------------------------------------------------------

describe('timeout', () => {
  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  test('rejects after the configured timeout elapses', async () => {
    const client = new OCRClient('/workers/ocr_worker.js', { timeout: 5000 });

    const recognizePromise = client.recognize('slow-image');

    jest.advanceTimersByTime(5001);

    await expect(recognizePromise).rejects.toThrow(
      'OCR request timed out after 5000ms.'
    );

    client.terminate();
  });

  test('does not reject before the timeout elapses', async () => {
    const client = new OCRClient('/workers/ocr_worker.js', { timeout: 5000 });

    const recognizePromise = client.recognize('image');
    jest.advanceTimersByTime(4999);

    // Settle the promise normally so the test can exit cleanly.
    const { id } = mockWorkerInstance._postMessage.mock.calls[0][0];
    mockWorkerInstance.simulateMessage({
      type: 'result',
      id,
      text: 'OK',
      confidence: 99,
      words: [],
    });

    const result = await recognizePromise;
    expect(result.text).toBe('OK');

    client.terminate();
  });
});

// ---------------------------------------------------------------------------
// Worker fatal errors
// ---------------------------------------------------------------------------

describe('worker fatal error (onerror)', () => {
  test('rejects all pending requests when the worker crashes', async () => {
    const client = new OCRClient('/workers/ocr_worker.js');

    const p1 = client.recognize('frame-1');
    const p2 = client.recognize('frame-2');

    mockWorkerInstance.simulateError('Worker script failed to parse.');

    await expect(p1).rejects.toThrow('Worker script failed to parse.');
    await expect(p2).rejects.toThrow('Worker script failed to parse.');
  });

  test('sets isReady() to false after a fatal worker error', async () => {
    const client = new OCRClient('/workers/ocr_worker.js');

    const pending = client.recognize('frame').catch(() => {});
    mockWorkerInstance.simulateError('WASM error');
    await pending;

    expect(client.isReady()).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// terminate()
// ---------------------------------------------------------------------------

describe('terminate', () => {
  test('calls terminate on the underlying Worker', () => {
    const client = new OCRClient('/workers/ocr_worker.js');
    client.terminate();

    expect(mockWorkerInstance.terminate).toHaveBeenCalledTimes(1);
  });

  test('rejects all pending requests on termination', async () => {
    const client = new OCRClient('/workers/ocr_worker.js');

    const p1 = client.recognize('frame-1');
    const p2 = client.recognize('frame-2');

    client.terminate();

    await expect(p1).rejects.toThrow('OCR client terminated.');
    await expect(p2).rejects.toThrow('OCR client terminated.');
  });

  test('sets isReady() to false after termination', () => {
    const client = new OCRClient('/workers/ocr_worker.js');
    client.terminate();

    expect(client.isReady()).toBe(false);
  });

  test('is safe to call multiple times without throwing', () => {
    const client = new OCRClient('/workers/ocr_worker.js');

    expect(() => {
      client.terminate();
      client.terminate();
    }).not.toThrow();
  });

  test('rejects subsequent recognize() calls after termination', async () => {
    const client = new OCRClient('/workers/ocr_worker.js');
    client.terminate();

    await expect(client.recognize('image')).rejects.toThrow(
      'OCR worker is not available.'
    );
  });
});
