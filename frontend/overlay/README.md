# Execra Guidance Overlay

An always-on-top, semi-transparent Electron.js desktop overlay that displays
Execra's real-time guidance over the user's screen while they work.

---

## Prerequisites

- **Node.js ≥ 18** — [nodejs.org](https://nodejs.org)
- **Execra backend running** — `uvicorn api.main:app --reload` (from project root)

---

## Quick Start

```bash
# 1. Navigate to this directory
cd frontend/overlay

# 2. Install dependencies (only needed once)
npm install

# 3. Launch the overlay
npm start

# Dev mode (opens DevTools automatically)
npm run dev
```

---

## Files

```
frontend/overlay/
├── main.js              # Electron main process — BrowserWindow config & IPC
├── preload.js           # contextBridge — exposes window.execra to renderer
├── package.json         # npm config
├── .gitignore
└── renderer/
    ├── index.html       # Overlay HTML shell
    ├── app.js           # UI logic — WebSocket events, rendering, controls
    └── styles.css       # Glassmorphism dark theme
```

---

## WebSocket Configuration

By default the overlay connects to `ws://localhost:8000/ws/guidance` with no auth token
(matches the backend's default dev configuration where `WS_API_TOKEN` is empty).

To change the URL or add a token, edit the top of `renderer/app.js`:

```js
const WS_URL   = 'ws://localhost:8000/ws/guidance';
const WS_TOKEN = '';   // set to your WS_API_TOKEN value if configured
```

---

## UI Components

| Component | Description |
|---|---|
| **Mode pill** | Shows PASSIVE / ACTIVE / MIXED — updates from each guidance payload |
| **Connection dot** | Green = connected, Red = disconnected, Orange = reconnecting |
| **Confidence bar** | Green ≥85%, Orange 65–84%, Red <65% |
| **Step counter** | "Step N of M" from guidance payload |
| **Source tags** | LLM · Rule Engine · Trace pill badges |
| **Instruction card** | Animated fade-in on each new instruction |
| **Reasoning** | Collapsible — shown when `reasoning` field is non-empty |
| **Error banner** | Red alert with severity icon on `error` messages |
| **Active Mode input** | Shown only in ACTIVE / MIXED mode; sends `{"prompt": "..."}` |
| **Minimize / Expand** | Collapses window to title bar only |

---

## Reconnection

The overlay reconnects automatically with **exponential back-off** (1 s → 2 s → 4 s … up to 30 s)
if the WebSocket drops unexpectedly. A normal close (code 1000) does not trigger reconnection.

---

## Security

- `contextIsolation: true` and `nodeIntegration: false` — renderer is fully sandboxed
- Only the `window.execra` API (defined in `preload.js` via `contextBridge`) is
  accessible to renderer code — no direct Node.js or Electron API exposure
- Content Security Policy in `index.html` restricts resource origins
