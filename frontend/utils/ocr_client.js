/**
 * frontend/utils/ocr_client.js
 * ==============================
 * Promise-based wrapper around the OCR Web Worker.
 *
 * Usage
 * -----
 *   const client = new OCRClient();
 *   await client.waitUntilReady();
 *   const result = await client.recognize(imageData);
 *   client.terminate();
 */

/**
 * @typedef {Object} OCRWord
 * @property {string} text
 * @property {number} confidence  0–100
 * @property {{ x0: number, y0: number, x1: number, y1: number }} bbox
 */

/**
 * @typedef {Object} OCRResult
 * @property {string}    text        Full page text
 * @property {number}    confidence  Overall confidence 0–100
 * @property {OCRWord[]} words       Per-word detail
 */

export class OCRClient {
  /**
   * @param {string} [workerPath] - URL/path to ocr_worker.js
   *                                Defaults to "./workers/ocr_worker.js"
   */
  constructor(workerPath = "./workers/ocr_worker.js") {
    /** @type {Worker|null} */
    this._worker = null;

    /** @type {boolean} */
    this._ready = false;

    /** @type {Promise<void>} */
    this._readyPromise = null;

    /** @type {Map<string, {resolve: Function, reject: Function}>} */
    this._pending = new Map();

    this._readyPromise = this._init(workerPath);
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  /**
   * Returns true once the worker has finished downloading language data.
   * @returns {boolean}
   */
  isReady() {
    return this._ready;
  }

  /**
   * Returns a Promise that resolves when the worker is ready.
   * @returns {Promise<void>}
   */
  waitUntilReady() {
    return this._readyPromise;
  }

  /**
   * Send an ImageData object to the OCR worker and return the result.
   * @param {ImageData} imageData
   * @returns {Promise<OCRResult>}
   */
  recognize(imageData) {
    if (!this._worker) {
      return Promise.reject(new Error("OCRClient: worker not initialised"));
    }

    const id = this._uuid();

    return new Promise((resolve, reject) => {
      this._pending.set(id, { resolve, reject });
      this._worker.postMessage({ type: "recognize", imageData, id });
    });
  }

  /**
   * Shut down the Web Worker and clean up all pending promises.
   */
  terminate() {
    if (this._worker) {
      this._worker.terminate();
      this._worker = null;
    }
    this._ready = false;

    // Reject any in-flight requests
    for (const [id, { reject }] of this._pending) {
      reject(new Error("OCRClient: worker terminated"));
    }
    this._pending.clear();
  }

  // ------------------------------------------------------------------
  // Private helpers
  // ------------------------------------------------------------------

  /**
   * Spin up the worker and return a promise that resolves on "ready".
   * @param {string} workerPath
   * @returns {Promise<void>}
   */
  _init(workerPath) {
    return new Promise((resolve, reject) => {
      try {
        // type: "module" required because ocr_worker.js uses ES import
        this._worker = new Worker(workerPath, { type: "module" });
      } catch (err) {
        reject(err);
        return;
      }

      this._worker.onmessage = (event) => {
        this._handleMessage(event.data, resolve, reject);
      };

      this._worker.onerror = (err) => {
        reject(new Error(`OCR Worker error: ${err.message}`));
      };
    });
  }

  /**
   * Route incoming worker messages to the correct handler.
   */
  _handleMessage(data, readyResolve, readyReject) {
    const { type, id } = data;

    switch (type) {
      case "ready":
        this._ready = true;
        readyResolve();
        break;

      case "init_error":
        readyReject(new Error(`OCR init failed: ${data.error}`));
        break;

      case "result": {
        const pending = this._pending.get(id);
        if (pending) {
          this._pending.delete(id);
          pending.resolve({
            text: data.text,
            confidence: data.confidence,
            words: data.words,
          });
        }
        break;
      }

      case "error": {
        const pending = this._pending.get(id);
        if (pending) {
          this._pending.delete(id);
          pending.reject(new Error(data.error));
        }
        break;
      }

      default:
        break;
    }
  }

  /**
   * Generate a UUID v4 for request correlation.
   * Uses crypto.randomUUID() when available; falls back to Math.random().
   * @returns {string}
   */
  _uuid() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    // Fallback for older browsers
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
    });
  }
}