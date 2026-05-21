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
   The check is asyncio-safe: ``_connections[conn_id]`` assignment and the
   subsequent ``len()`` guard share the same synchronous execution slice
   (no ``await`` between them), so no interleaving is possible.

3. **Per-connection sliding-window rate limit** — at most
   ``settings.WS_RATE_LIMIT_MESSAGES`` messages are processed within any
   rolling window of ``settings.WS_RATE_LIMIT_WINDOW_S`` seconds.
   Connections that exceed the limit receive close code 4429 and are
   dropped.

4. **Guaranteed cleanup** — :func:`_unregister` is called from a
   ``finally`` block covering all exit paths: normal close, abnormal
   disconnect, rate-limit drop, send/receive failure, and unexpected
   exceptions.  :func:`_unregister` is idempotent so repeated calls are
   safe.

5. **Heartbeat** — when ``WS_HEARTBEAT_INTERVAL_S > 0``, a background
   task sends a periodic application-level ping to each connection.  If
   the ping fails (client has silently dropped), the stale slot is
   removed from the active registry immediately — without waiting for the
   TCP stack to time out.  Set to ``0`` to disable.

6. **Broadcast safety** — :func:`broadcast` iterates over a snapshot of
   the registry and removes any connection whose send fails, so stale
   sockets can never accumulate during a broadcast loop.

Close codes
-----------
4401 — Unauthorized (missing or invalid token)
4429 — Rate limit exceeded
4503 — Connection limit reached
1000 — Normal closure (client-initiated)
1006 — Abnormal closure (network error / no close frame)
"""
from __future__ import annotations

import asyncio
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
# Module-level connection registry
#
# Keyed by id(websocket) — CPython object identity, unique per connection for
# its lifetime.  Storing the WebSocket object (not just the ID) enables
# broadcast and heartbeat without a separate lookup structure.
#
# ASYNCIO NOTE: all mutations are synchronous (no await between guard and
# mutation), so no locks are required.  Do NOT insert await calls between
# the len() guard and the registry assignment in guidance_ws without
# re-evaluating this invariant.
# ---------------------------------------------------------------------------

# Maps conn_id → WebSocket.  Replaces the former set[int]; the dict retains
# O(1) lookup while giving access to the socket object for send/ping.
_connections: dict[int, WebSocket] = {}

# Per-connection sliding-window rate-limit state.
_rate_state: dict[int, deque[float]] = {}


# ---------------------------------------------------------------------------
# Connection lifecycle helpers
# ---------------------------------------------------------------------------

def _unregister(conn_id: int) -> None:
    """
    Remove *conn_id* from the active registry and its rate-limit state.

    Idempotent — safe to call multiple times with the same *conn_id*;
    uses ``dict.pop(..., None)`` so it never raises KeyError.
    Called from the ``finally`` block of :func:`guidance_ws` and, for
    early stale detection, from :func:`_heartbeat` when a ping fails.
    """
    _connections.pop(conn_id, None)
    _rate_state.pop(conn_id, None)


# ---------------------------------------------------------------------------
# Broadcast with stale-connection cleanup
# ---------------------------------------------------------------------------

async def broadcast(message: dict[str, Any]) -> None:
    """
    Send *message* as JSON to every currently registered connection.

    Iterates over a **snapshot** of the registry so that removals during the
    loop do not mutate the collection being iterated.  Any connection whose
    ``send_json`` raises is unregistered immediately after the loop, ensuring
    failed sockets are never left in the active set.

    Args:
        message: A JSON-serialisable dict to send to all clients.
    """
    stale: list[int] = []
    # Iterate over a copy so _unregister() calls during the loop are safe.
    for conn_id, ws in list(_connections.items()):
        try:
            await ws.send_json(message)
        except Exception:
            logger.debug(
                "WebSocket broadcast: send failed for conn %d — queued for removal",
                conn_id,
            )
            stale.append(conn_id)

    for conn_id in stale:
        _unregister(conn_id)

    if stale:
        logger.info(
            "WebSocket broadcast: removed %d stale connection(s) (active=%d)",
            len(stale),
            len(_connections),
        )


# ---------------------------------------------------------------------------
# Heartbeat — proactive stale-connection detection
# ---------------------------------------------------------------------------

async def _heartbeat(conn_id: int, websocket: WebSocket, interval: int) -> None:
    """
    Send a periodic application-level ping to detect silent disconnects.

    Every *interval* seconds the task sends ``{"type": "ping"}`` to the
    client.  If the send raises for any reason (broken pipe, connection reset,
    peer closed without a WS close frame) the stale slot is unregistered
    immediately via :func:`_unregister` and the task exits.

    The connection slot is freed as soon as the ping fails — the server does
    not wait for the TCP stack to time out (which can take several minutes
    under default OS keep-alive settings).

    The task exits cleanly if *conn_id* is no longer in :data:`_connections`
    (i.e., the main receive loop already cleaned up), so there is no
    double-removal race.

    Cancelled by the ``finally`` block of :func:`guidance_ws` on all exit
    paths.
    """
    while True:
        await asyncio.sleep(interval)
        if conn_id not in _connections:
            # Main loop already cleaned up; nothing more to do.
            return
        try:
            await websocket.send_json({"type": "ping"})
        except Exception:
            logger.debug(
                "WebSocket heartbeat: ping failed for conn %d — freeing slot immediately",
                conn_id,
            )
            _unregister(conn_id)
            return


# ---------------------------------------------------------------------------
# Internal helpers (authentication, rate limiting, rejection)
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

    # Evict entries outside the window (deque is ordered oldest → newest).
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

    Server → Client (heartbeat, informational — clients may ignore)::

        {"type": "ping"}

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
    # ASYNCIO-SAFETY: dict assignment and the len() guard are both
    # synchronous.  No await appears between them, so no other coroutine
    # can observe a partial state.  Do not insert any await here.
    # ------------------------------------------------------------------
    _connections[conn_id] = websocket
    if len(_connections) > settings.WS_MAX_CONNECTIONS:
        _unregister(conn_id)
        logger.warning(
            "WebSocket guidance: rejected — connection limit reached "
            "(%d/%d, remote=%s)",
            len(_connections),
            settings.WS_MAX_CONNECTIONS,
            websocket.client,
        )
        await _reject(websocket, code=4503, reason="Too many connections")
        return

    # ------------------------------------------------------------------
    # Step 3 — Accept and run the message loop
    # ------------------------------------------------------------------
    heartbeat_task: asyncio.Task[None] | None = None

    try:
        await websocket.accept()
        logger.info(
            "WebSocket guidance: connection accepted "
            "(remote=%s, active=%d/%d)",
            websocket.client,
            len(_connections),
            settings.WS_MAX_CONNECTIONS,
        )

        # Start the heartbeat only when the feature is enabled.
        interval: int = settings.WS_HEARTBEAT_INTERVAL_S
        if interval > 0:
            heartbeat_task = asyncio.create_task(
                _heartbeat(conn_id, websocket, interval),
                name=f"ws-heartbeat-{conn_id}",
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
            # Receive the next message.
            # Starlette raises WebSocketDisconnect on a clean close frame
            # and RuntimeError when the socket is in an invalid/closed
            # state (e.g., peer dropped the connection without a close
            # frame and we try to receive after the disconnect message).
            # Both are treated as client-initiated disconnects here.
            # --------------------------------------------------------
            try:
                data: Any = await websocket.receive_json()
            except WebSocketDisconnect:
                raise
            except RuntimeError as exc:
                # Map abnormal-close RuntimeError to a normal disconnect
                # so it surfaces as INFO rather than ERROR in logs.
                logger.info(
                    "WebSocket guidance: connection closed abnormally "
                    "(remote=%s — %s)",
                    websocket.client,
                    exc,
                )
                raise WebSocketDisconnect(code=1006) from exc

            prompt: str = data.get("prompt", "").strip()

            if not prompt:
                try:
                    await websocket.send_json(
                        {"error": "Missing required field: 'prompt'"}
                    )
                except Exception:
                    # Send failed — client likely disconnected.
                    break
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

            try:
                await websocket.send_json({"guidance": guidance})
            except Exception:
                # Send failed after a successful receive — client dropped
                # between the receive and the reply.  Exit the loop; the
                # finally block will clean up the slot.
                logger.debug(
                    "WebSocket guidance: send failed (remote=%s) — closing",
                    websocket.client,
                )
                break

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
        # Cancel the heartbeat task first so it cannot race with _unregister.
        if heartbeat_task is not None:
            heartbeat_task.cancel()

        # _unregister is idempotent: safe even if the heartbeat already
        # removed the conn_id when it detected a failed ping.
        _unregister(conn_id)
        logger.debug(
            "WebSocket guidance: connection cleaned up (active=%d)",
            len(_connections),
        )
