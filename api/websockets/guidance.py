"""
Secure WebSocket endpoint for real-time guidance delivery.

Security model
--------------
1. **Token authentication** — the caller must supply a ``token`` query
   parameter whose value matches ``settings.WS_API_TOKEN``.  Comparison
   uses ``hmac.compare_digest`` to prevent timing side-channel attacks.
   When ``WS_API_TOKEN`` is the empty string (default), authentication is
   disabled and a warning is logged; this keeps the dev environment
   zero-configuration while making the insecure state visible in logs.

2. **Global connection limit** — at most ``settings.WS_MAX_CONNECTIONS``
   concurrent connections are accepted.  New connections beyond this cap
   receive close code 4503 (server busy) immediately after the handshake.
   The check is asyncio-safe: ``_active_connections.add()`` and the
   subsequent ``len()`` guard share the same synchronous execution slice
   (no ``await`` between them), so no interleaving is possible.

3. **Per-connection sliding-window rate limit** — at most
   ``settings.WS_RATE_LIMIT_MESSAGES`` messages are processed within any
   rolling window of ``settings.WS_RATE_LIMIT_WINDOW_S`` seconds.
   Connections that exceed the limit receive close code 4429 and are
   dropped.

4. **Guaranteed cleanup** — the active-connection set and per-connection
   rate-limit state are always removed in a ``finally`` block, covering
   normal disconnects, rate-limit drops, and unexpected exceptions.

Close codes
-----------
4401 — Unauthorized (missing or invalid token)
4429 — Rate limit exceeded
4503 — Connection limit reached
1000 — Normal closure (client-initiated)

Known TODOs
-----------
- Idle-connection timeout (heartbeat / ping-pong) to reclaim slots held by
  silent clients.
- Per-IP connection limit to prevent a single host from monopolising the
  global cap.
- Starlette ``max_size`` configuration to bound incoming message size.
- Wire ``_generate_guidance()`` stub to ``IntelligenceCore.generate_guidance()``.
"""
from __future__ import annotations

import hmac
import logging
import time
from collections import deque
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Module-level security state
#
# Both structures are keyed by id(websocket) — the CPython object identity of
# the WebSocket instance, which is unique per connection for its lifetime.
#
# THREADING NOTE: asyncio is single-threaded.  All operations on these dicts
# and sets are synchronous (no await), so no locks are needed.  Do NOT add
# await calls between the guard check and the mutation of _active_connections
# without re-evaluating thread safety.
# ---------------------------------------------------------------------------

# Set of active connection IDs.  add/discard/len are all O(1).
_active_connections: set[int] = set()

# Per-connection sliding-window state: maps conn_id → deque of timestamps
# (monotonic seconds) for messages received in the current window.
_rate_state: dict[int, deque[float]] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _verify_token(token: str) -> bool:
    """
    Return ``True`` iff *token* matches ``settings.WS_API_TOKEN``.

    When the configured token is empty, authentication is disabled and a
    warning is emitted so operators can identify misconfigured deployments.

    ``hmac.compare_digest`` is used for constant-time comparison to prevent
    timing-based inference of the token value.
    """
    configured: str = settings.WS_API_TOKEN
    if not configured:
        logger.warning(
            "WS_API_TOKEN is not set — WebSocket guidance endpoint is "
            "unauthenticated. Set WS_API_TOKEN in .env for production use."
        )
        return True
    return hmac.compare_digest(configured, token)


def _check_rate_limit(conn_id: int) -> bool:
    """
    Return ``True`` iff *conn_id* is within the configured message rate.

    Applies a sliding window: timestamps older than
    ``settings.WS_RATE_LIMIT_WINDOW_S`` are evicted from the left of the
    deque before the count is checked.  If the connection is within the
    limit, the current timestamp is appended and ``True`` is returned.
    """
    now: float = time.monotonic()
    window: int = settings.WS_RATE_LIMIT_WINDOW_S
    limit: int = settings.WS_RATE_LIMIT_MESSAGES

    timestamps: deque[float] = _rate_state.setdefault(conn_id, deque())

    # Evict entries outside the window (deque is ordered oldest → newest)
    while timestamps and (now - timestamps[0]) > window:
        timestamps.popleft()

    if len(timestamps) >= limit:
        return False

    timestamps.append(now)
    return True


async def _reject(websocket: WebSocket, code: int, reason: str) -> None:
    """
    Accept and immediately close a WebSocket with *code* and *reason*.

    Accepting before closing ensures the WS close frame (and its code) is
    delivered to the client rather than an HTTP 403 with no WS context.
    Errors during the close call (e.g., transport already gone) are silenced
    so the caller's ``finally`` block always runs.
    """
    try:
        await websocket.accept()
        await websocket.close(code=code, reason=reason)
    except Exception:
        pass  # transport may already be closed; close code already sent


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/ws/guidance")
async def guidance_ws(
    websocket: WebSocket,
    token: str = "",
) -> None:
    """
    Secure WebSocket endpoint for streaming guidance to clients.

    Clients connect with ``ws[s]://<host>/ws/guidance?token=<WS_API_TOKEN>``.

    Message protocol (JSON)
    -----------------------
    Client → Server::

        {"prompt": "<user prompt or code snippet>"}

    Server → Client (success)::

        {"guidance": "<generated guidance text>"}

    Server → Client (error)::

        {"error": "<human-readable error description>"}

    The connection is dropped with an appropriate close code if any security
    check fails.  See module docstring for close code semantics.
    """
    conn_id = id(websocket)

    # ------------------------------------------------------------------
    # Step 1 — Authentication
    #
    # Verified before touching the connection counter so a rejected client
    # never occupies a connection slot.
    # ------------------------------------------------------------------
    if not _verify_token(token):
        logger.warning(
            "WebSocket guidance: rejected — invalid token (remote=%s)",
            websocket.client,
        )
        await _reject(websocket, code=4401, reason="Unauthorized")
        return

    # ------------------------------------------------------------------
    # Step 2 — Global connection limit
    #
    # ASYNCIO-SAFETY: add() and the len() guard are both synchronous.
    # No await appears between them, so no other coroutine can observe a
    # partial state.  Do not insert any await here.
    # ------------------------------------------------------------------
    _active_connections.add(conn_id)
    if len(_active_connections) > settings.WS_MAX_CONNECTIONS:
        _active_connections.discard(conn_id)
        logger.warning(
            "WebSocket guidance: rejected — connection limit reached "
            "(%d/%d, remote=%s)",
            len(_active_connections),
            settings.WS_MAX_CONNECTIONS,
            websocket.client,
        )
        await _reject(websocket, code=4503, reason="Too many connections")
        return

    # ------------------------------------------------------------------
    # Step 3 — Accept and run the message loop
    # ------------------------------------------------------------------
    try:
        await websocket.accept()
        logger.info(
            "WebSocket guidance: connection accepted "
            "(remote=%s, active=%d/%d)",
            websocket.client,
            len(_active_connections),
            settings.WS_MAX_CONNECTIONS,
        )

        while True:
            # --------------------------------------------------------
            # Rate-limit check happens before each receive so that a
            # burst of queued messages cannot bypass it.
            # --------------------------------------------------------
            if not _check_rate_limit(conn_id):
                logger.warning(
                    "WebSocket guidance: rate limit exceeded "
                    "(remote=%s, limit=%d msg/%ds)",
                    websocket.client,
                    settings.WS_RATE_LIMIT_MESSAGES,
                    settings.WS_RATE_LIMIT_WINDOW_S,
                )
                await websocket.close(code=4429, reason="Rate limit exceeded")
                break

            # --------------------------------------------------------
            # Receive the next message from the client.
            # receive_json() raises WebSocketDisconnect on client close.
            # --------------------------------------------------------
            data: Any = await websocket.receive_json()
            prompt: str = data.get("prompt", "").strip()

            if not prompt:
                await websocket.send_json(
                    {"error": "Missing required field: 'prompt'"}
                )
                continue

            # --------------------------------------------------------
            # TODO: replace stub with IntelligenceCore.generate_guidance()
            #
            # from core.intelligence.debate_engine import IntelligenceCore
            # guidance = await intelligence_core.generate_guidance(
            #     prompt=prompt,
            #     trust_score=float(data.get("trust_score", 1.0)),
            # )
            # --------------------------------------------------------
            guidance: str = (
                f"[guidance stub] echoing prompt ({len(prompt)} chars)"
            )

            await websocket.send_json({"guidance": guidance})

    except WebSocketDisconnect:
        logger.info(
            "WebSocket guidance: client disconnected (remote=%s)",
            websocket.client,
        )
    except Exception:
        logger.exception(
            "WebSocket guidance: unexpected error (remote=%s)",
            websocket.client,
        )
    finally:
        # Always release the connection slot and rate-limit state regardless
        # of how the coroutine exits (normal close, exception, rate limit).
        _active_connections.discard(conn_id)
        _rate_state.pop(conn_id, None)
        logger.debug(
            "WebSocket guidance: connection cleaned up (active=%d)",
            len(_active_connections),
        )
