/**
 * frontend/workers/ocr_worker.js
 * ================================
 * Web Worker that runs Tesseract.js (WASM build) entirely in the browser.
 *
 * Message protocol
 * ----------------
 * IN  { type: "recognize", imageData: ImageData, id: string }
 * OUT { type: "result",    id, text, confidence, words }
 *     { type: "error",     id, error }
 *     { type: "ready" }                  ← sent once on init success
 *     { type: "init_error", error }      ← sent if init fails
 */

import { createWorker } from "tesseract.js";

let worker = null;
let ready = false;

/**
 * Initialise Tesseract worker on load.
 * Language data is cached in IndexedDB so subsequent loads are instant.
 */
async function init() {
  try {
    worker = await createWorker("eng", 1, {
      // Cache trained data in IndexedDB — persists across page reloads
      cacheMethod: "indexedDB",
      logger: () => {},   // suppress verbose progress logs in production
    });
    ready = true;
    self.postMessage({ type: "ready" });
  } catch (err) {
    self.postMessage({ type: "init_error", error: err.message });
  }
}

/**
 * Message handler — receives recognize requests from the main thread.
 */
self.onmessage = async (event) => {
  const { type, imageData, id } = event.data;

  if (type !== "recognize") return;

  if (!ready || !worker) {
    self.postMessage({
      type: "error",
      id,
      error: "OCR worker not yet initialised. Please wait for the ready event.",
    });
    return;
  }

  try {
    const { data } = await worker.recognize(imageData);

    const words = (data.words || []).map((w) => ({
      text: w.text,
      confidence: w.confidence,
      bbox: w.bbox,   // { x0, y0, x1, y1 }
    }));

    self.postMessage({
      type: "result",
      id,
      text: data.text,
      confidence: data.confidence,
      words,
    });
  } catch (err) {
    self.postMessage({
      type: "error",
      id,
      error: err.message,
    });
  }
};

// Start initialisation immediately when the worker loads
init();