/**
 * frontend/overlay/preload.js
 *
 * Runs in a privileged context (Node.js + Electron APIs available) but
 * exposes ONLY a narrow, safe surface to the renderer via contextBridge.
 *
 * window.execra API exposed to renderer:
 *
 *   connect(wsUrl, token?)  — opens WebSocket; auto-reconnects on disconnect
 *   onMessage(callback)     — register a handler for incoming WS messages
 *   sendPrompt(text)        — send {"prompt": text} to the server (Active Mode)
 *   minimize()              — collapse the overlay to title bar
 *   restore()               — expand the overlay to full height
 *   closeOverlay()          — quit the application
 */

const { contextBridge, ipcRenderer } = require('electron');

// ---------------------------------------------------------------------------
// Internal WebSocket state — NOT exposed to renderer directly
// ---------------------------------------------------------------------------

let _socket       = null;
let _messageHandlers = [];
let _wsUrl        = null;
let _wsToken      = null;
let _reconnectTimer = null;
let _reconnectDelay = 1000;   // ms — doubles on each failed attempt (max 30 s)
const MAX_RECONNECT_DELAY = 30000;

/**
 * Open a WebSocket connection to `url`.
 * Reconnects automatically with exponential back-off on unexpected close.
 */
function _connect(url, token = '') {
  _wsUrl   = url;
  _wsToken = token;

  const fullUrl = token ? `${url}?token=${encodeURIComponent(token)}` : url;

  if (_socket) {
    _socket.onclose = null;   // suppress reconnect from the old socket
    _socket.close();
  }

  _socket = new WebSocket(fullUrl);

  _socket.onopen = () => {
    _reconnectDelay = 1000;   // reset back-off on successful connect
    _dispatch({ type: 'connected' });
  };

  _socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      _dispatch(data);
    } catch {
      _dispatch({ type: 'raw', data: event.data });
    }
  };

  _socket.onerror = () => {
    _dispatch({ type: 'ws_error' });
  };

  _socket.onclose = (event) => {
    // 1000 = normal (user-initiated) — do NOT reconnect
    if (event.code === 1000) {
      _dispatch({ type: 'disconnected', clean: true });
      return;
    }

    _dispatch({ type: 'disconnected', clean: false, code: event.code });

    // Exponential back-off reconnect
    clearTimeout(_reconnectTimer);
    _reconnectTimer = setTimeout(() => {
      _reconnectDelay = Math.min(_reconnectDelay * 2, MAX_RECONNECT_DELAY);
      _connect(_wsUrl, _wsToken);
    }, _reconnectDelay);
  };
}

/** Dispatch a parsed message object to all registered handlers. */
function _dispatch(message) {
  _messageHandlers.forEach(cb => {
    try { cb(message); } catch { /* renderer handler must not crash preload */ }
  });
}

// ---------------------------------------------------------------------------
// contextBridge — the ONLY surface the renderer can touch
// ---------------------------------------------------------------------------

contextBridge.exposeInMainWorld('execra', {
  /**
   * Connect to the Execra guidance WebSocket.
   * @param {string} wsUrl   e.g. "ws://localhost:8000/ws/guidance"
   * @param {string} [token] optional auth token
   */
  connect(wsUrl, token = '') {
    _connect(wsUrl, token);
  },

  /**
   * Register a callback for incoming WebSocket messages.
   * The callback receives a parsed JS object.
   * @param {function} callback
   */
  onMessage(callback) {
    if (typeof callback === 'function') {
      _messageHandlers.push(callback);
    }
  },

  /**
   * Send a user prompt to the server (Active Mode).
   * @param {string} text
   */
  sendPrompt(text) {
    if (_socket && _socket.readyState === WebSocket.OPEN) {
      _socket.send(JSON.stringify({ prompt: text }));
    }
  },

  /** Collapse the overlay window to title-bar height. */
  minimize() {
    ipcRenderer.send('overlay-minimize');
  },

  /** Restore the overlay window to full height. */
  restore() {
    ipcRenderer.send('overlay-restore');
  },

  /** Quit the overlay application. */
  closeOverlay() {
    ipcRenderer.send('overlay-close');
  },
});
