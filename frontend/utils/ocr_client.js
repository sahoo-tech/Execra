/**
 * OCRClient — Promise-based interface to the browser OCR Web Worker.
 *
 * Spawns a single `ocr_worker.js` Web Worker and routes `recognize()` calls
 * to it via `postMessage`.  Each request is tracked by a UUID; the worker's
 * response resolves or rejects the corresponding Promise.
 *
 * Usage
 * -----
 *   import { OCRClient } from './utils/ocr_client.js';
 *
 *   const client = new OCRClient('/workers/ocr_worker.js');
 *   const { text, confidence } = await client.recognize(imageData);
 *   client.terminate();
 */

const DEFAULT_TIMEOUT_MS = 30_000;

export class OCRClient {
  /**
   * @param {string} workerPath  Absolute or relative URL of `ocr_worker.js`.
   * @param {object} [options]
   * @param {number} [options.timeout=30000]  Per-request timeout in milliseconds.
   */
  constructor(workerPath, { timeout = DEFAULT_TIMEOUT_MS } = {}) {
    this._timeout = timeout;
    /** @type {Map<string, { resolve: Function, reject: Function, timer: number }>} */
    this._pending = new Map();
    this._ready = false;
    this._worker = null;

    this._initWorker(workerPath);
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  /**
   * Send an image to the OCR worker for text recognition.
   *
   * Accepted `imageData` types match those supported by tesseract.js:
   * `ImageBitmap`, `Blob`, `File`, `string` (URL or data URI), `ImageData`,
   * `HTMLImageElement`, `HTMLCanvasElement`, `HTMLVideoElement`.
   *
   * For best performance with large frames, pass an `ImageBitmap` and include
   * it in the transferable list; this avoids copying the pixel buffer between
   * threads.
   *
   * @param {ImageBitmap|Blob|string|ImageData} imageData
   * @returns {Promise<{ text: string, confidence: number, words: object[] }>}
   */
  recognize(imageData) {
    return new Promise((resolve, reject) => {
      if (!this._ready || !this._worker) {
        reject(new Error('OCR worker is not available.'));
        return;
      }

      const id = this._generateId();

      const timer = setTimeout(() => {
        if (this._pending.has(id)) {
          this._pending.delete(id);
          reject(new Error(`OCR request timed out after ${this._timeout}ms.`));
        }
      }, this._timeout);

      this._pending.set(id, { resolve, reject, timer });
      this._worker.postMessage({ type: 'recognize', imageData, id });
    });
  }

  /**
   * Returns `true` if the underlying Web Worker started successfully and has
   * not been terminated.
   * @returns {boolean}
   */
  isReady() {
    return this._ready;
  }

  /**
   * Terminate the Web Worker and reject all pending recognition requests.
   * Safe to call multiple times.
   */
  terminate() {
    for (const [, { reject, timer }] of this._pending.entries()) {
      clearTimeout(timer);
      reject(new Error('OCR client terminated.'));
    }
    this._pending.clear();
    this._ready = false;

    if (this._worker) {
      this._worker.terminate();
      this._worker = null;
    }
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  /** @private */
  _initWorker(workerPath) {
    try {
      this._worker = new Worker(workerPath, { type: 'module' });
      this._worker.onmessage = (event) => this._handleMessage(event);
      this._worker.onerror = (event) => this._handleWorkerError(event);
      this._ready = true;
    } catch (err) {
      console.error('[OCRClient] Failed to spawn worker:', err);
      this._ready = false;
    }
  }

  /** @private */
  _handleMessage(event) {
    const { type, id, text, confidence, words, error } = event.data;

    if (!id || !this._pending.has(id)) return;

    const { resolve, reject, timer } = this._pending.get(id);
    clearTimeout(timer);
    this._pending.delete(id);

    if (type === 'result') {
      resolve({ text, confidence, words });
    } else if (type === 'error') {
      reject(new Error(error || 'Unknown OCR error.'));
    }
  }

  /**
   * Called when the Worker itself crashes (not a per-request error).
   * Rejects all pending requests so no Promise is left unresolved.
   * @private
   */
  _handleWorkerError(event) {
    const message =
      (event && event.message) || 'OCR worker encountered a fatal error.';

    for (const [, { reject, timer }] of this._pending.entries()) {
      clearTimeout(timer);
      reject(new Error(message));
    }
    this._pending.clear();
    this._ready = false;
  }

  /** @private */
  _generateId() {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
    return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  }
}

export default OCRClient;
