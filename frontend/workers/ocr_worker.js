/**
 * Browser OCR Web Worker — Execra offline fallback engine.
 *
 * Runs inside a dedicated Web Worker (type: "module").  Initializes a single
 * Tesseract engine instance at startup and reuses it across all recognition
 * requests to avoid repeated WASM compilation and language-data loading.
 *
 * Language data (traineddata) is cached in IndexedDB automatically by
 * tesseract.js v5 — no extra configuration required.
 *
 * Message protocol
 * ----------------
 * Incoming:
 *   { type: "recognize", imageData: <ImageBitmap|Blob|string|ImageData>, id: <string> }
 *
 * Outgoing (success):
 *   { type: "result", id, text: <string>, confidence: <number>, words: <object[]> }
 *
 * Outgoing (failure):
 *   { type: "error", id, error: <string> }
 */

import { createWorker } from 'tesseract.js';

/**
 * The single reusable Tesseract worker instance.
 * Initialized once; all recognize() calls share it.
 * @type {import('tesseract.js').Worker | null}
 */
let ocrWorker = null;

/**
 * Promise that resolves once the Tesseract engine is ready.
 * Incoming messages wait on this before calling recognize().
 */
const engineReady = createWorker('eng')
  .then((worker) => {
    ocrWorker = worker;
  })
  .catch((err) => {
    self.postMessage({
      type: 'error',
      id: null,
      error: `OCR engine initialization failed: ${err.message}`,
    });
  });

/**
 * Handle recognition requests from the main thread.
 *
 * Waits for the engine to be ready, then calls recognize() and posts the
 * result back.  Errors at any stage are caught and returned as error messages
 * so the caller's Promise is always settled.
 */
self.onmessage = async function handleMessage(event) {
  const { type, imageData, id } = event.data;

  if (type !== 'recognize') return;

  try {
    await engineReady;

    if (!ocrWorker) {
      self.postMessage({
        type: 'error',
        id,
        error: 'OCR engine is not available.',
      });
      return;
    }

    const { data } = await ocrWorker.recognize(imageData);

    self.postMessage({
      type: 'result',
      id,
      text: data.text,
      confidence: data.confidence,
      words: data.words,
    });
  } catch (err) {
    self.postMessage({
      type: 'error',
      id,
      error: err.message || 'Text recognition failed.',
    });
  }
};

/**
 * Release the Tesseract worker when this Web Worker is being unloaded.
 * Prevents lingering WASM instances from leaking memory.
 */
self.addEventListener('unload', () => {
  if (ocrWorker) {
    ocrWorker.terminate();
    ocrWorker = null;
  }
});
