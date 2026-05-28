/**
 * frontend/renderer/app.js
 * =========================
 * Main renderer — manages WebSocket connection to the Execra backend
 * and falls back to local WASM OCR when the connection drops.
 *
 * Overlay status indicator
 * ------------------------
 *   "OCR: Backend (online)"   — guidance coming from backend WebSocket
 *   "OCR: Local (offline)"    — guidance from local Tesseract.js WASM
 */

import { OCRClient } from "../utils/ocr_client.js";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const WS_URL = "ws://localhost:8000/ws/guidance";
const RECONNECT_DELAY_MS = 3000;
const OCR_WORKER_PATH = "../workers/ocr_worker.js";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let socket = null;
let isOnline = false;
let ocrClient = null;

// ---------------------------------------------------------------------------
// DOM helpers
// ---------------------------------------------------------------------------

/**
 * Update the status indicator in the overlay.
 * @param {"online"|"offline"} mode
 */
function setOCRStatus(mode) {
  const el = document.getElementById("ocr-status");
  if (!el) return;

  if (mode === "online") {
    el.textContent = "OCR: Backend (online)";
    el.className = "ocr-status ocr-status--online";
  } else {
    el.textContent = "OCR: Local (offline)";
    el.className = "ocr-status ocr-status--offline";
  }
}

/**
 * Display a guidance instruction in the overlay.
 * @param {string} text
 * @param {"backend"|"local"} source
 */
function showGuidance(text, source = "backend") {
  const el = document.getElementById("guidance-text");
  if (!el) return;
  el.textContent = text;
  el.dataset.source = source;
}

// ---------------------------------------------------------------------------
// Backend WebSocket
// ---------------------------------------------------------------------------

function connectWebSocket() {
  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    isOnline = true;
    setOCRStatus("online");
    console.log("[app] WebSocket connected");
  };

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.instruction) {
        showGuidance(msg.instruction, "backend");
      }
    } catch {
      // ignore malformed messages
    }
  };

  socket.onclose = () => {
    isOnline = false;
    setOCRStatus("offline");
    console.warn("[app] WebSocket disconnected — switching to local OCR");
    // Attempt reconnect after delay
    setTimeout(connectWebSocket, RECONNECT_DELAY_MS);
  };

  socket.onerror = (err) => {
    console.error("[app] WebSocket error:", err);
    socket.close();
  };
}

// ---------------------------------------------------------------------------
// Local OCR fallback
// ---------------------------------------------------------------------------

/**
 * Capture the current screen / canvas and run local OCR on it.
 * Called periodically when the backend WebSocket is offline.
 * @param {HTMLCanvasElement} canvas
 */
async function runLocalOCR(canvas) {
  if (isOnline || !ocrClient || !ocrClient.isReady()) return;

  const ctx = canvas.getContext("2d");
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

  try {
    const result = await ocrClient.recognize(imageData);
    if (result.text.trim()) {
      showGuidance(`[Local OCR] ${result.text.trim()}`, "local");
    }
  } catch (err) {
    console.error("[app] Local OCR error:", err);
  }
}

// ---------------------------------------------------------------------------
// Initialisation
// ---------------------------------------------------------------------------

async function init() {
  // 1. Set up overlay status indicator
  setOCRStatus("offline");

  // 2. Start OCR client (downloads language data in background)
  ocrClient = new OCRClient(OCR_WORKER_PATH);
  ocrClient
    .waitUntilReady()
    .then(() => console.log("[app] Local OCR worker ready"))
    .catch((err) => console.error("[app] Local OCR init failed:", err));

  // 3. Connect to backend WebSocket
  connectWebSocket();

  // 4. Local OCR polling loop (runs only when offline)
  const canvas = document.getElementById("screen-canvas");
  if (canvas) {
    setInterval(() => runLocalOCR(canvas), 2000);
  }
}

// Boot when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}