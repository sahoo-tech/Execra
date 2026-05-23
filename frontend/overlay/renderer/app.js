/**
 * frontend/overlay/renderer/app.js
 *
 * Renderer-side UI controller for the Execra guidance overlay.
 *
 * Responsibilities:
 *  - Connect to the Execra WebSocket guidance endpoint on page load
 *  - Handle all server event types: guidance, ping, error, connected, disconnected
 *  - Update every UI element in response to incoming GuidanceInstruction payloads
 *  - Manage minimize / expand / close lifecycle via window.execra IPC bridge
 *  - Handle Active Mode input and send prompts
 *
 * Compatible with both the current stub format {"guidance": "..."} and the
 * full GuidanceInstruction schema:
 *   { instruction, confidence, source, step, total_steps, mode, reasoning, ... }
 */

'use strict';

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const WS_URL     = 'ws://localhost:8000/ws/guidance';
const WS_TOKEN   = '';   // set if WS_API_TOKEN is configured in .env

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------

const $ = id => document.getElementById(id);

const elConnDot        = $('conn-dot');
const elModePill       = $('mode-pill');
const elBtnToggle      = $('btn-toggle');
const elBtnClose       = $('btn-close');
const elIconMinimize   = $('icon-minimize');
const elIconExpand     = $('icon-expand');
const elOverlayBody    = $('overlay-body');
const elErrorBanner    = $('error-banner');
const elErrorText      = $('error-text');
const elStepCounter    = $('step-counter');
const elSourceTags     = $('source-tags');
const elConfidenceFill = $('confidence-fill');
const elConfidencePct  = $('confidence-pct');
const elConfidenceTrack = $('confidence-track');
const elInstructionText = $('instruction-text');
const elReasoningDetails = $('reasoning-details');
const elReasoningText  = $('reasoning-text');
const elActiveWrap     = $('active-input-wrap');
const elActiveInput    = $('active-input');
const elBtnSend        = $('btn-send');
const elStatusText     = $('status-text');

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let isMinimized = false;

// ---------------------------------------------------------------------------
// WebSocket event handler
// ---------------------------------------------------------------------------

/**
 * Dispatch an incoming WS message to the appropriate UI handler.
 * Handles both the stub format and the full GuidanceInstruction schema.
 *
 * @param {object} msg - Parsed JSON from the WebSocket
 */
function handleMessage(msg) {
  // Internal connection lifecycle events (from preload.js)
  if (msg.type === 'connected') {
    setConnectionState('connected');
    return;
  }
  if (msg.type === 'disconnected') {
    setConnectionState(msg.clean ? 'disconnected' : 'reconnecting');
    setStatus(msg.clean ? 'Disconnected' : 'Reconnecting…');
    return;
  }
  if (msg.type === 'ws_error') {
    setConnectionState('reconnecting');
    setStatus('Connection error — retrying…');
    return;
  }
  if (msg.type === 'ping') {
    // Heartbeat from server — nothing to render
    return;
  }

  // ── Error message from server ──────────────────────────────────────────
  if (msg.error) {
    showError(msg.error);
    return;
  }

  // ── Full GuidanceInstruction payload ──────────────────────────────────
  if (msg.instruction) {
    hideError();
    renderGuidance({
      instruction: msg.instruction,
      confidence:  msg.confidence  ?? 1.0,
      source:      msg.source      ?? [],
      step:        msg.step        ?? 1,
      total_steps: msg.total_steps ?? 1,
      mode:        msg.mode        ?? 'passive',
      reasoning:   msg.reasoning   ?? '',
    });
    return;
  }

  // ── Stub format: {"guidance": "..."} ──────────────────────────────────
  if (msg.guidance) {
    hideError();
    renderGuidance({
      instruction: msg.guidance,
      confidence:  1.0,
      source:      [],
      step:        1,
      total_steps: 1,
      mode:        'passive',
      reasoning:   '',
    });
  }
}

// ---------------------------------------------------------------------------
// UI renderers
// ---------------------------------------------------------------------------

/**
 * Render a full guidance payload into all UI components.
 * @param {{ instruction, confidence, source, step, total_steps, mode, reasoning }} g
 */
function renderGuidance({ instruction, confidence, source, step, total_steps, mode, reasoning }) {
  renderInstruction(instruction);
  renderConfidence(confidence);
  renderStepCounter(step, total_steps);
  renderSourceTags(source);
  renderMode(mode);
  renderReasoning(reasoning);
  setStatus(`Updated ${new Date().toLocaleTimeString()}`);
}

/**
 * Animate the instruction text with a fade-in on change.
 * @param {string} text
 */
function renderInstruction(text) {
  elInstructionText.classList.remove('fade-in');
  // Trigger reflow to restart animation
  void elInstructionText.offsetWidth;
  elInstructionText.textContent = text;
  elInstructionText.classList.add('fade-in');
}

/**
 * Update the confidence bar colour and width.
 * Green ≥85%, Orange 65–84%, Red <65%.
 * @param {number} score - 0.0 to 1.0
 */
function renderConfidence(score) {
  const pct = Math.round(score * 100);
  elConfidenceFill.style.width = `${pct}%`;

  elConfidenceFill.classList.remove('high', 'medium', 'low');
  let cls, color;
  if (pct >= 85) {
    cls = 'high';
    color = '#22c55e';
  } else if (pct >= 65) {
    cls = 'medium';
    color = '#f97316';
  } else {
    cls = 'low';
    color = '#ef4444';
  }
  elConfidenceFill.classList.add(cls);

  elConfidencePct.textContent = `${pct}%`;
  elConfidencePct.style.color = color;
  elConfidenceTrack.setAttribute('aria-valuenow', pct);
}

/**
 * Update the "Step N of M" counter.
 * @param {number} step
 * @param {number} total
 */
function renderStepCounter(step, total) {
  elStepCounter.textContent = `Step ${step} of ${total}`;
}

/**
 * Render source tag pills (LLM, Rule Engine, Trace, or custom).
 * @param {string[]} sources
 */
function renderSourceTags(sources) {
  elSourceTags.innerHTML = '';
  if (!Array.isArray(sources) || sources.length === 0) return;

  sources.forEach(src => {
    const pill = document.createElement('span');
    pill.className = 'source-tag';

    const lc = src.toLowerCase();
    if (lc === 'llm') {
      pill.classList.add('tag-llm');
      pill.textContent = 'LLM';
    } else if (lc.includes('rule')) {
      pill.classList.add('tag-rule');
      pill.textContent = 'Rule Engine';
    } else if (lc.includes('trace') || lc.includes('execution')) {
      pill.classList.add('tag-trace');
      pill.textContent = 'Trace';
    } else {
      pill.classList.add('tag-other');
      pill.textContent = src;
    }

    elSourceTags.appendChild(pill);
  });
}

/**
 * Update the mode pill and show/hide the Active Mode input.
 * @param {'passive'|'active'|'mixed'|'safe'|'expert'} mode
 */
function renderMode(mode) {
  // Normalise backend 'safe'→'passive', 'expert'→'active'
  const normalised = mode === 'safe' ? 'passive' : mode === 'expert' ? 'active' : mode;

  elModePill.className = `mode-pill mode-${normalised}`;
  elModePill.textContent = normalised.toUpperCase();

  // Show Active Mode input only in active or mixed mode
  const showInput = normalised === 'active' || normalised === 'mixed';
  elActiveWrap.style.display = showInput ? 'flex' : 'none';
}

/**
 * Show reasoning section if text is non-empty.
 * @param {string} text
 */
function renderReasoning(text) {
  if (text && text.trim()) {
    elReasoningText.textContent = text;
    elReasoningDetails.style.display = 'block';
  } else {
    elReasoningDetails.style.display = 'none';
  }
}

// ---------------------------------------------------------------------------
// Error helpers
// ---------------------------------------------------------------------------

function showError(message) {
  elErrorText.textContent = message;
  elErrorBanner.style.display = 'flex';
}

function hideError() {
  elErrorBanner.style.display = 'none';
  elErrorText.textContent = '';
}

// ---------------------------------------------------------------------------
// Connection status helpers
// ---------------------------------------------------------------------------

/**
 * @param {'connected'|'disconnected'|'reconnecting'} state
 */
function setConnectionState(state) {
  elConnDot.className = `conn-dot conn-${state}`;
  elConnDot.title = {
    connected:    'Connected to Execra',
    disconnected: 'Disconnected',
    reconnecting: 'Reconnecting…',
  }[state] ?? state;
}

function setStatus(text) {
  elStatusText.textContent = text;
}

// ---------------------------------------------------------------------------
// Minimize / Expand toggle
// ---------------------------------------------------------------------------

function toggleMinimize() {
  isMinimized = !isMinimized;

  if (isMinimized) {
    elOverlayBody.style.display = 'none';
    elIconMinimize.style.display = 'none';
    elIconExpand.style.display   = 'block';
    elBtnToggle.setAttribute('aria-label', 'Expand overlay');
    window.execra.minimize();
  } else {
    elOverlayBody.style.display = '';
    elIconMinimize.style.display = 'block';
    elIconExpand.style.display   = 'none';
    elBtnToggle.setAttribute('aria-label', 'Minimize overlay');
    window.execra.restore();
  }
}

// ---------------------------------------------------------------------------
// Active Mode: send prompt on button click or Enter key
// ---------------------------------------------------------------------------

function sendPrompt() {
  const text = elActiveInput.value.trim();
  if (!text) return;
  window.execra.sendPrompt(text);
  elActiveInput.value = '';
  elActiveInput.focus();
}

elBtnSend.addEventListener('click', sendPrompt);

elActiveInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendPrompt();
  }
});

// ---------------------------------------------------------------------------
// Title bar controls
// ---------------------------------------------------------------------------

elBtnToggle.addEventListener('click', toggleMinimize);

elBtnClose.addEventListener('click', () => {
  window.execra.closeOverlay();
});

// ---------------------------------------------------------------------------
// Bootstrap: connect to WebSocket and register message handler
// ---------------------------------------------------------------------------

setStatus('Connecting…');
setConnectionState('reconnecting');

window.execra.onMessage(handleMessage);
window.execra.connect(WS_URL, WS_TOKEN);
