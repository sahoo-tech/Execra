# Browser OCR Compatibility

This document covers the browser requirements, known limitations, and performance
expectations for Execra's browser-based OCR fallback system, which uses
[tesseract.js v5](https://github.com/naptha/tesseract.js) backed by WebAssembly.

---

## Supported Browsers

| Browser         | Minimum Version | Notes                                    |
|-----------------|-----------------|------------------------------------------|
| Chrome / Edge   | 80+             | Full support; best overall performance   |
| Firefox         | 114+            | Full support; module workers since 114   |
| Safari          | 15+             | Full support; nested workers since 13.1  |
| Electron        | 22+ (Chromium 108+) | Recommended deployment target        |

> **Electron / Tauri** are the primary deployment targets for Execra.  Browser
> support is listed for completeness and for web-based deployments.

---

## WebAssembly Requirements

tesseract.js v5 compiles Tesseract OCR to WebAssembly (WASM).  The following
browser capabilities are required:

| Capability             | Chrome | Firefox | Safari | Notes                          |
|------------------------|--------|---------|--------|--------------------------------|
| `WebAssembly`          | 57+    | 53+     | 11+    | Core WASM runtime              |
| `WebAssembly.Memory`   | 57+    | 53+     | 11+    | Shared memory for WASM module  |
| `SharedArrayBuffer`    | 92+    | 79+     | 15.2+  | Required for multi-threaded WASM|
| `crossOriginIsolated`  | 86+    | 79+     | 15.2+  | Required for SharedArrayBuffer |
| ES Module Workers      | 80+    | 114+    | 15+    | `new Worker(url, {type:'module'})` |

### Content Security Policy

If a CSP is in use, the following directives are required for WASM execution:

```
Content-Security-Policy:
  script-src 'self' 'wasm-unsafe-eval';
  worker-src 'self';
```

`'wasm-unsafe-eval'` is needed to allow WASM compilation inside the worker
context.  Without it, tesseract.js will fail silently with a CSP error.

### Cross-Origin Isolation (COOP / COEP)

`SharedArrayBuffer` — used by tesseract.js for multi-threaded WASM — requires
the page to be cross-origin isolated.  Add these HTTP headers on the server:

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

In Electron, cross-origin isolation is enabled via `webPreferences`:

```js
new BrowserWindow({
  webPreferences: { contextIsolation: true }
});
```

---

## Web Worker Limitations

### Nested Workers

`ocr_worker.js` runs inside a dedicated Web Worker.  tesseract.js v5 spawns its
own internal worker for WASM processing, creating a **nested worker** (worker
inside a worker).  Nested workers are supported in all target browsers:

| Browser | Nested Worker Support |
|---------|-----------------------|
| Chrome  | Yes (since v4)        |
| Firefox | Yes                   |
| Safari  | Yes (since 13.1)      |

### No DOM Access

Web Workers have no access to the DOM, `localStorage`, or `sessionStorage`.
Language data is cached via **IndexedDB**, which is available in Worker
contexts.  The `document` and `window` objects are not available inside the
worker.

### Transferable Objects

For large image frames, pass an `ImageBitmap` as `imageData` and include it in
the transfer list when calling `postMessage`.  This transfers ownership without
copying the pixel buffer, significantly reducing memory overhead:

```js
const bitmap = await createImageBitmap(blob);
worker.postMessage({ type: 'recognize', imageData: bitmap, id }, [bitmap]);
```

Note: once transferred, the original `bitmap` is neutered and cannot be reused.

---

## Offline Behavior

### Language Data Caching

On first use, tesseract.js downloads the English language model
(`eng.traineddata`, ~10 MB) from the configured CDN and stores it in
**IndexedDB**.  Subsequent page loads read the model from the local cache
without any network request, enabling fully offline operation.

Cache key: `tesseract-lang-data/eng` (managed automatically by tesseract.js).

### Fallback Trigger

`app.js` monitors the backend WebSocket connection.  The transition to local
OCR is automatic:

```
Backend connects  → setOcrStatus(true)  → "OCR: Backend (online)"
Backend drops     → setOcrStatus(false) → "OCR: Local (offline)"
                    ensureLocalOcr() spawns OCRClient if not running
Backend reconnects→ setOcrStatus(true)  → "OCR: Backend (online)"
```

The local OCR client is kept alive after the backend reconnects, so the next
disconnection incurs no cold-start delay.

### No Network Required (After First Load)

Once the language model is cached:
- `ocr_worker.js` initializes fully offline
- All recognition runs in-browser via WASM
- No external requests are made during a session

---

## Performance Expectations

All figures are approximate and vary by device, image size, and text density.

| Metric                          | Typical Value           |
|---------------------------------|-------------------------|
| First initialization (cold)     | 2–6 s (model download + WASM compile) |
| First initialization (cached)   | 0.5–1.5 s              |
| Recognition latency (full frame, 1920×1080) | 1.5–4 s   |
| Recognition latency (cropped region, 640×480) | 0.3–0.8 s |
| Memory footprint (idle worker)  | ~35–50 MB               |
| Memory footprint (during recognition) | ~80–120 MB      |

### Optimization Tips

- **Crop before sending**: pass the smallest image region that contains the
  text of interest.  A 400×200 crop processes 5–10× faster than a full frame.
- **Use `ImageBitmap`**: avoids pixel-buffer copies between threads.
- **Reuse the client**: `OCRClient` keeps a single worker alive; don't create
  a new instance per frame.
- **Throttle calls**: for continuous screen capture, call `recognize()` only
  when a meaningful frame delta is detected (the backend already does this via
  its delta-detection pipeline).

---

## Known Limitations

| Limitation                      | Detail                                        |
|---------------------------------|-----------------------------------------------|
| Single-language model by default | `ocr_worker.js` loads `eng` only.  Multi-language support requires modifying the `createWorker` call. |
| No handwriting support          | Tesseract is trained on printed text.         |
| Accuracy vs. cloud OCR          | Local WASM Tesseract is less accurate than cloud OCR APIs on complex layouts or low-contrast images. |
| Mobile browsers                 | Performance on low-end mobile devices may be unacceptably slow for real-time use. |
| Safari < 15                     | ES module workers not supported; the OCR worker will fail to initialize. |
| IE / Legacy Edge                | Not supported.                                |
