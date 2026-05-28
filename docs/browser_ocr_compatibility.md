# Browser Compatibility — WebAssembly OCR Worker

## Overview

The Execra OCR worker uses `tesseract.js@5` which compiles Tesseract OCR to
WebAssembly. It runs entirely in the browser inside a Web Worker with no
backend call required.

## Compatibility Matrix

| Browser         | Min Version | Web Workers | WASM  | IndexedDB Cache | Status       |
|:----------------|:-----------:|:-----------:|:-----:|:---------------:|:------------:|
| Chrome          | 88+         | ✅           | ✅    | ✅               | ✅ Supported  |
| Edge (Chromium) | 88+         | ✅           | ✅    | ✅               | ✅ Supported  |
| Firefox         | 79+         | ✅           | ✅    | ✅               | ✅ Supported  |
| Safari          | 15.2+       | ✅           | ✅    | ✅               | ✅ Supported  |
| Opera           | 74+         | ✅           | ✅    | ✅               | ✅ Supported  |
| IE 11           | —           | ❌           | ❌    | ❌               | ❌ Unsupported|

## Required Browser APIs

| API                    | Used for                              | Chrome | Firefox | Edge  | Safari |
|:-----------------------|:--------------------------------------|:------:|:-------:|:-----:|:------:|
| `Worker` (ES Module)   | Running OCR off the main thread       | 80+    | 114+    | 80+   | 15+    |
| `WebAssembly`          | Executing compiled Tesseract binary   | 57+    | 52+     | 16+   | 11+    |
| `IndexedDB`            | Caching language data (~4 MB)         | 24+    | 16+     | 12+   | 7+     |
| `ImageData`            | Passing frame pixels to worker        | All    | All     | All   | All    |
| `crypto.randomUUID()`  | Request correlation IDs               | 92+    | 95+     | 92+   | 15.4+  |

> **Note:** `crypto.randomUUID()` is not available in Firefox < 95 or Safari < 15.4.
> `ocr_client.js` includes a `Math.random()`-based fallback UUID generator.

## Performance Expectations

Tested on a modern laptop (Apple M2 / Intel Core i7-12th gen, 16 GB RAM):

| Image Size  | Cold Start (first load) | Warm (cached WASM) |
|:------------|:-----------------------:|:------------------:|
| 1920×1080   | 1200–1800 ms            | 400–700 ms         |
| 1280×720    | 800–1200 ms             | 200–400 ms         |
| 640×480     | 400–700 ms              | 100–200 ms         |

**Target SLA: ≤ 800 ms on 1920×1080 (warm cache).** Cold start exceeds this
due to WASM compilation; subsequent calls meet the target.

## IndexedDB Cache Behaviour

On first run, tesseract.js downloads ~4 MB of English language data and stores
it in IndexedDB under the key `tesseract-lang-data`. All subsequent page loads
skip the download entirely, reducing initialisation from ~1.5 s to ~150 ms.

Users on incognito / private browsing mode will re-download on every session
because IndexedDB is cleared on tab close.

## Fallback Strategy

`frontend/renderer/app.js` implements automatic fallback:

1. App starts → tries to connect backend WebSocket (`ws://localhost:8000/ws/guidance`)
2. If WebSocket connects → guidance comes from the backend; overlay shows
   `"OCR: Backend (online)"`
3. If WebSocket drops → app polls local OCR every 2 seconds; overlay shows
   `"OCR: Local (offline)"`
4. If WebSocket reconnects → immediately switches back to backend mode

## Known Limitations

- Web Worker ES Module (`type: "module"`) requires a server context — does not
  work via `file://` protocol. Use `npx serve` or any local HTTP server.
- Firefox < 114 does not support ES Module Workers; use a bundler (Vite/Webpack)
  to produce a classic worker bundle for broader Firefox support.
- WASM execution is blocked by strict Content Security Policies that disallow
  `'wasm-unsafe-eval'`. Add this directive to your CSP if needed.