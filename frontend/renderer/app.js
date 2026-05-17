/**
 * Execra renderer — main entry point for the browser overlay.
 *
 * Connects to the backend guidance WebSocket at ws://localhost:8000/ws/guidance.
 * When the backend is reachable, OCR is performed server-side and the status
 * indicator shows "OCR: Backend (online)".
 *
 * If the WebSocket connection drops, the app automatically activates the local
 * browser OCR worker so that text recognition continues offline.  The status
 * indicator switches to "OCR: Local (offline)" until the backend reconnects.
 *
 * This module deliberately avoids touching any unrelated UI components.
 * The only DOM elements it owns are:
 *   #ocr-status     — the OCR status indicator span
 *   #guidance-panel — the step-by-step guidance panel
 */

import { OCRClient } from '../utils/ocr_client.js';

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const BACKEND_WS_URL = 'ws://localhost:8000/ws/guidance';
const OCR_WORKER_PATH = new URL('../workers/ocr_worker.js', import.meta.url).href;
const RECONNECT_DELAY_MS = 3000;

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------

const ocrStatusEl = document.getElementById('ocr-status');
const guidancePanelEl = document.getElementById('guidance-panel');

// ---------------------------------------------------------------------------
// Module state
// ---------------------------------------------------------------------------

/** @type {WebSocket | null} */
let socket = null;

/** @type {OCRClient | null} */
let ocrClient = null;

let isBackendOnline = false;

// ---------------------------------------------------------------------------
// OCR status indicator
// ---------------------------------------------------------------------------

/**
 * Update the visible OCR status chip.
 * @param {boolean} online  `true` → backend active; `false` → local fallback.
 */
function setOcrStatus(online) {
  isBackendOnline = online;
  if (!ocrStatusEl) return;
  ocrStatusEl.textContent = online ? 'OCR: Backend (online)' : 'OCR: Local (offline)';
  ocrStatusEl.dataset.status = online ? 'online' : 'offline';
}

// ---------------------------------------------------------------------------
// Local OCR fallback
// ---------------------------------------------------------------------------

/**
 * Ensure the local OCR worker is running.  Creates it lazily on first call;
 * recreates it if it was previously terminated.
 */
function ensureLocalOcr() {
  if (!ocrClient || !ocrClient.isReady()) {
    ocrClient = new OCRClient(OCR_WORKER_PATH);
  }
}

/**
 * Run text recognition using the local browser OCR worker.
 *
 * @param {ImageBitmap|Blob|string|ImageData} imageData
 * @returns {Promise<string>}  The recognized text.
 */
export async function runLocalOcr(imageData) {
  ensureLocalOcr();
  const { text } = await ocrClient.recognize(imageData);
  return text;
}

// ---------------------------------------------------------------------------
// Backend WebSocket
// ---------------------------------------------------------------------------

/**
 * Open the WebSocket connection to the Execra backend.
 * Sets the OCR status to online on success; falls back to local OCR and
 * schedules a reconnect on failure or disconnection.
 */
export function connectBackend() {
  try {
    socket = new WebSocket(BACKEND_WS_URL);
  } catch {
    handleBackendDown();
    return;
  }

  socket.onopen = () => {
    setOcrStatus(true);
  };

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      handleServerMessage(msg);
    } catch {
      // Non-JSON frames are silently ignored.
    }
  };

  socket.onclose = () => {
    handleBackendDown();
    scheduleReconnect();
  };

  socket.onerror = () => {
    // onerror always precedes onclose; the status update happens there.
  };
}

/** @private */
function handleBackendDown() {
  setOcrStatus(false);
  ensureLocalOcr();
}

/** @private */
function scheduleReconnect() {
  setTimeout(() => {
    if (!isBackendOnline) connectBackend();
  }, RECONNECT_DELAY_MS);
}

// ---------------------------------------------------------------------------
// Server message handling
// ---------------------------------------------------------------------------

/** @private */
function handleServerMessage(msg) {
  if (msg.event === 'guidance' && msg.payload) {
    renderGuidance(msg.payload);
  }
}

/** @private */
function renderGuidance(payload) {
  if (!guidancePanelEl) return;

  const { instruction = '', confidence = 0, step, total_steps } = payload;
  const pct = Math.round(confidence * 100);
  const stepLabel =
    step != null && total_steps != null ? `Step ${step} of ${total_steps}` : '';

  guidancePanelEl.innerHTML = `
    <p class="guidance-instruction">${escapeHtml(instruction)}</p>
    ${stepLabel ? `<span class="guidance-step">${escapeHtml(stepLabel)}</span>` : ''}
    <span class="guidance-confidence">Confidence: ${pct}%</span>
  `;
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

/** @private */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

// Show offline state immediately; connectBackend() updates it to online if
// the WebSocket handshake succeeds.
setOcrStatus(false);
connectBackend();
