"""
Unit and integration tests for api/websockets/guidance.py.

Test strategy
-------------
Security-helper functions (_verify_token, _check_rate_limit) are tested
directly as pure functions.  The WebSocket endpoint is tested end-to-end
via FastAPI's TestClient.websocket_connect(), which speaks the real WebSocket
protocol through an in-process ASGI transport.

Reliability tests (TestWsReliability, TestWsBroadcast) use AsyncMock to
inject failures directly into the connection registry, verifying that the
idempotent _unregister() helper and the broadcast() snapshot-iteration
pattern keep the registry consistent under every failure mode.

Each test that touches module-level state (_connections, _rate_state) resets
that state via the autouse reset_ws_state fixture.

WebSocket close code semantics
-------------------------------
4401 — Unauthorized
4429 — Rate limit exceeded
4503 — Connection limit reached (server busy)
1000 — Normal closure
1006 — Abnormal closure (no close frame)
"""
from __future__ import annotations

import time
from collections import deque
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from api.main import app
import api.websockets.guidance as guidance_module
from api.websockets.guidance import (
    _check_rate_limit,
    _unregister,
    _verify_token,
    broadcast,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_ws_state():
    """Clear module-level connection and rate-limit state before every test."""
    guidance_module._connections.clear()
    guidance_module._rate_state.clear()
    yield
    guidance_module._connections.clear()
    guidance_module._rate_state.clear()


# ---------------------------------------------------------------------------
# _verify_token
# ---------------------------------------------------------------------------

class TestVerifyToken:
    def test_empty_configured_token_always_passes(self):
        """Empty WS_API_TOKEN disables auth — any token value is accepted."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            assert _verify_token("anything") is True
            assert _verify_token("") is True

    def test_correct_token_passes(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret-key"):
            assert _verify_token("secret-key") is True

    def test_wrong_token_rejected(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret-key"):
            assert _verify_token("wrong-key") is False

    def test_empty_token_rejected_when_configured(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret-key"):
            assert _verify_token("") is False

    def test_partial_token_rejected(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret-key"):
            assert _verify_token("secret") is False

    def test_timing_safe_comparison(self):
        """Verify that compare_digest is used (not ==) — structural inspection."""
        import inspect
        src = inspect.getsource(_verify_token)
        assert "compare_digest" in src

    def test_logs_warning_when_token_not_configured(self, caplog):
        import logging
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with caplog.at_level(logging.WARNING, logger="api.websockets.guidance"):
                _verify_token("anything")
        assert any("WS_API_TOKEN" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# _check_rate_limit
# ---------------------------------------------------------------------------

class TestCheckRateLimit:
    def test_first_message_allowed(self):
        with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 5):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", 60):
                assert _check_rate_limit(conn_id=1) is True

    def test_messages_up_to_limit_all_allowed(self):
        with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 3):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", 60):
                assert _check_rate_limit(1) is True
                assert _check_rate_limit(1) is True
                assert _check_rate_limit(1) is True

    def test_message_exceeding_limit_rejected(self):
        with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 3):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", 60):
                _check_rate_limit(1)
                _check_rate_limit(1)
                _check_rate_limit(1)
                assert _check_rate_limit(1) is False

    def test_window_expiry_resets_allowance(self):
        """Old timestamps outside the window are evicted; new messages pass."""
        conn_id = 42
        window = 1
        with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 2):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", window):
                _check_rate_limit(conn_id)
                _check_rate_limit(conn_id)
                assert _check_rate_limit(conn_id) is False

                aged = deque(t - (window + 1) for t in guidance_module._rate_state[conn_id])
                guidance_module._rate_state[conn_id] = aged

                assert _check_rate_limit(conn_id) is True

    def test_independent_connections_have_independent_limits(self):
        with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 2):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", 60):
                _check_rate_limit(conn_id=10)
                _check_rate_limit(conn_id=10)
                assert _check_rate_limit(10) is False
                assert _check_rate_limit(20) is True

    def test_rate_state_initialised_for_new_connection(self):
        conn_id = 99
        assert conn_id not in guidance_module._rate_state
        _check_rate_limit(conn_id)
        assert conn_id in guidance_module._rate_state


# ---------------------------------------------------------------------------
# WebSocket endpoint — authentication
# ---------------------------------------------------------------------------

class TestWsAuthentication:
    def test_no_token_rejected_when_configured(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret"):
            with pytest.raises(WebSocketDisconnect) as exc_info:
                with client.websocket_connect("/ws/guidance") as ws:
                    ws.receive_json()
            assert exc_info.value.code == 4401

    def test_wrong_token_rejected(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret"):
            with pytest.raises(WebSocketDisconnect) as exc_info:
                with client.websocket_connect("/ws/guidance?token=wrong") as ws:
                    ws.receive_json()
            assert exc_info.value.code == 4401

    def test_correct_token_accepted(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret"):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                with client.websocket_connect("/ws/guidance?token=secret") as ws:
                    ws.send_json({"prompt": "hello"})
                    data = ws.receive_json()
                    assert "guidance" in data

    def test_no_auth_when_token_not_configured(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                with client.websocket_connect("/ws/guidance") as ws:
                    ws.send_json({"prompt": "hello"})
                    data = ws.receive_json()
                    assert "guidance" in data

    def test_rejected_connection_does_not_occupy_slot(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret"):
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect("/ws/guidance?token=wrong") as ws:
                    ws.receive_json()
        assert len(guidance_module._connections) == 0


# ---------------------------------------------------------------------------
# WebSocket endpoint — connection limit
# ---------------------------------------------------------------------------

class TestWsConnectionLimit:
    def test_connection_within_limit_accepted(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_MAX_CONNECTIONS", 5):
                with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                    with client.websocket_connect("/ws/guidance") as ws:
                        ws.send_json({"prompt": "hi"})
                        data = ws.receive_json()
                        assert "guidance" in data

    def test_connection_at_limit_rejected(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_MAX_CONNECTIONS", 0):
                with pytest.raises(WebSocketDisconnect) as exc_info:
                    with client.websocket_connect("/ws/guidance") as ws:
                        ws.receive_json()
                assert exc_info.value.code == 4503

    def test_active_count_increments_on_connect(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                with client.websocket_connect("/ws/guidance"):
                    assert len(guidance_module._connections) == 1

    def test_active_count_decrements_on_disconnect(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                with client.websocket_connect("/ws/guidance") as ws:
                    ws.send_json({"prompt": "test"})
                    ws.receive_json()
        assert len(guidance_module._connections) == 0

    def test_limit_not_consumed_by_rejected_connection(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_MAX_CONNECTIONS", 0):
                with pytest.raises(WebSocketDisconnect):
                    with client.websocket_connect("/ws/guidance") as ws:
                        ws.receive_json()
        assert len(guidance_module._connections) == 0


# ---------------------------------------------------------------------------
# WebSocket endpoint — rate limiting
# ---------------------------------------------------------------------------

class TestWsRateLimiting:
    def test_messages_within_limit_receive_guidance(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 5):
                with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", 60):
                    with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                        with client.websocket_connect("/ws/guidance") as ws:
                            for _ in range(3):
                                ws.send_json({"prompt": "test"})
                                data = ws.receive_json()
                                assert "guidance" in data

    def test_exceeding_rate_limit_closes_connection(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 2):
                with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", 60):
                    with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                        with pytest.raises(WebSocketDisconnect) as exc_info:
                            with client.websocket_connect("/ws/guidance") as ws:
                                ws.send_json({"prompt": "msg1"})
                                ws.receive_json()
                                ws.send_json({"prompt": "msg2"})
                                ws.receive_json()
                                ws.send_json({"prompt": "msg3"})
                                ws.receive_json()
                        assert exc_info.value.code == 4429

    def test_rate_state_cleaned_up_after_disconnect(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                with client.websocket_connect("/ws/guidance") as ws:
                    ws.send_json({"prompt": "hello"})
                    ws.receive_json()
        assert len(guidance_module._rate_state) == 0


# ---------------------------------------------------------------------------
# WebSocket endpoint — message protocol
# ---------------------------------------------------------------------------

class TestWsMessageProtocol:
    def test_valid_prompt_returns_guidance_key(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                with client.websocket_connect("/ws/guidance") as ws:
                    ws.send_json({"prompt": "How do I fix this bug?"})
                    data = ws.receive_json()
                    assert "guidance" in data
                    assert isinstance(data["guidance"], str)

    def test_missing_prompt_returns_error_key(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                with client.websocket_connect("/ws/guidance") as ws:
                    ws.send_json({})
                    data = ws.receive_json()
                    assert "error" in data
                    assert "prompt" in data["error"].lower()

    def test_empty_prompt_returns_error_key(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                with client.websocket_connect("/ws/guidance") as ws:
                    ws.send_json({"prompt": "   "})
                    data = ws.receive_json()
                    assert "error" in data

    def test_multiple_messages_in_one_session(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                with client.websocket_connect("/ws/guidance") as ws:
                    for i in range(3):
                        ws.send_json({"prompt": f"question {i}"})
                        data = ws.receive_json()
                        assert "guidance" in data


# ---------------------------------------------------------------------------
# WebSocket endpoint — settings integration
# ---------------------------------------------------------------------------

class TestWsSettings:
    def test_settings_defaults_are_sane(self):
        from core.config import settings as cfg
        assert isinstance(cfg.WS_API_TOKEN, str)
        assert isinstance(cfg.WS_MAX_CONNECTIONS, int)
        assert cfg.WS_MAX_CONNECTIONS > 0
        assert isinstance(cfg.WS_RATE_LIMIT_MESSAGES, int)
        assert cfg.WS_RATE_LIMIT_MESSAGES > 0
        assert isinstance(cfg.WS_RATE_LIMIT_WINDOW_S, int)
        assert cfg.WS_RATE_LIMIT_WINDOW_S > 0
        assert isinstance(cfg.WS_HEARTBEAT_INTERVAL_S, int)
        assert cfg.WS_HEARTBEAT_INTERVAL_S >= 0

    def test_env_override_ws_max_connections(self):
        import os
        from core.config import Settings
        with patch.dict(os.environ, {"WS_MAX_CONNECTIONS": "25"}):
            s = Settings()
            assert s.WS_MAX_CONNECTIONS == 25

    def test_env_override_ws_api_token(self):
        import os
        from core.config import Settings
        with patch.dict(os.environ, {"WS_API_TOKEN": "prod-secret"}):
            s = Settings()
            assert s.WS_API_TOKEN == "prod-secret"

    def test_env_override_rate_limit_messages(self):
        import os
        from core.config import Settings
        with patch.dict(os.environ, {"WS_RATE_LIMIT_MESSAGES": "100"}):
            s = Settings()
            assert s.WS_RATE_LIMIT_MESSAGES == 100

    def test_env_override_rate_limit_window(self):
        import os
        from core.config import Settings
        with patch.dict(os.environ, {"WS_RATE_LIMIT_WINDOW_S": "30"}):
            s = Settings()
            assert s.WS_RATE_LIMIT_WINDOW_S == 30

    def test_env_override_heartbeat_interval(self):
        import os
        from core.config import Settings
        with patch.dict(os.environ, {"WS_HEARTBEAT_INTERVAL_S": "45"}):
            s = Settings()
            assert s.WS_HEARTBEAT_INTERVAL_S == 45

    def test_heartbeat_can_be_disabled_via_env(self):
        import os
        from core.config import Settings
        with patch.dict(os.environ, {"WS_HEARTBEAT_INTERVAL_S": "0"}):
            s = Settings()
            assert s.WS_HEARTBEAT_INTERVAL_S == 0


# ---------------------------------------------------------------------------
# Reliability — _unregister idempotency
# ---------------------------------------------------------------------------

class TestUnregisterIdempotency:
    def test_unregister_unknown_conn_id_does_not_raise(self):
        """Calling _unregister on a non-existent conn_id must be a no-op."""
        _unregister(99999)  # must not raise

    def test_unregister_twice_does_not_raise(self):
        """Repeated _unregister calls for the same conn_id must be safe."""
        ws = MagicMock()
        conn_id = 42
        guidance_module._connections[conn_id] = ws
        guidance_module._rate_state[conn_id] = deque([time.monotonic()])

        _unregister(conn_id)
        _unregister(conn_id)  # second call — must not raise

    def test_unregister_clears_both_registry_and_rate_state(self):
        ws = MagicMock()
        conn_id = 7
        guidance_module._connections[conn_id] = ws
        guidance_module._rate_state[conn_id] = deque([time.monotonic()])

        _unregister(conn_id)

        assert conn_id not in guidance_module._connections
        assert conn_id not in guidance_module._rate_state

    def test_unregister_only_removes_target_conn(self):
        """_unregister must not disturb other registered connections."""
        ws_a, ws_b = MagicMock(), MagicMock()
        guidance_module._connections[1] = ws_a
        guidance_module._connections[2] = ws_b

        _unregister(1)

        assert 1 not in guidance_module._connections
        assert 2 in guidance_module._connections


# ---------------------------------------------------------------------------
# Reliability — broadcast with stale connection cleanup
# ---------------------------------------------------------------------------

class TestWsBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_delivers_to_healthy_connections(self):
        """broadcast() must send the message to all live sockets."""
        ws1, ws2 = AsyncMock(), AsyncMock()
        guidance_module._connections[1] = ws1
        guidance_module._connections[2] = ws2

        await broadcast({"event": "update"})

        ws1.send_json.assert_awaited_once_with({"event": "update"})
        ws2.send_json.assert_awaited_once_with({"event": "update"})

    @pytest.mark.asyncio
    async def test_broadcast_removes_stale_connection_on_send_failure(self):
        """A send failure during broadcast must unregister the stale socket."""
        ws_good = AsyncMock()
        ws_bad = AsyncMock()
        ws_bad.send_json.side_effect = RuntimeError("connection reset")

        guidance_module._connections[10] = ws_good
        guidance_module._connections[20] = ws_bad

        await broadcast({"event": "update"})

        assert 10 in guidance_module._connections
        assert 20 not in guidance_module._connections

    @pytest.mark.asyncio
    async def test_broadcast_healthy_sockets_receive_after_stale_removal(self):
        """After removing a stale socket, healthy sockets must have received."""
        ws_good = AsyncMock()
        ws_bad = AsyncMock()
        ws_bad.send_json.side_effect = OSError("broken pipe")

        guidance_module._connections[100] = ws_good
        guidance_module._connections[200] = ws_bad

        await broadcast({"msg": "hello"})

        ws_good.send_json.assert_awaited_once_with({"msg": "hello"})

    @pytest.mark.asyncio
    async def test_broadcast_on_empty_registry_does_not_raise(self):
        """broadcast() with no connections must be a silent no-op."""
        await broadcast({"event": "empty"})  # must not raise

    @pytest.mark.asyncio
    async def test_broadcast_removes_multiple_stale_connections(self):
        """All failed connections in a broadcast must be removed."""
        ws_a, ws_b, ws_c = AsyncMock(), AsyncMock(), AsyncMock()
        ws_b.send_json.side_effect = RuntimeError("dead")
        ws_c.send_json.side_effect = RuntimeError("dead")

        guidance_module._connections[1] = ws_a
        guidance_module._connections[2] = ws_b
        guidance_module._connections[3] = ws_c

        await broadcast({"x": 1})

        assert 1 in guidance_module._connections
        assert 2 not in guidance_module._connections
        assert 3 not in guidance_module._connections

    @pytest.mark.asyncio
    async def test_broadcast_does_not_mutate_registry_during_iteration(self):
        """
        broadcast() snapshots the registry before iterating — mutations inside
        the loop must not raise RuntimeError (dict changed size during iteration).
        """
        calls: list[int] = []

        async def failing_send(msg):
            calls.append(1)
            raise RuntimeError("fail")

        ws1 = AsyncMock()
        ws1.send_json = failing_send
        guidance_module._connections[99] = ws1

        await broadcast({"x": 1})  # must complete without RuntimeError

        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_active_count_accurate_after_broadcast_cleanup(self):
        """Active count must reflect removed stale connections post-broadcast."""
        ws_good = AsyncMock()
        ws_stale = AsyncMock()
        ws_stale.send_json.side_effect = RuntimeError("gone")

        guidance_module._connections[1] = ws_good
        guidance_module._connections[2] = ws_stale

        assert len(guidance_module._connections) == 2
        await broadcast({"x": 1})
        assert len(guidance_module._connections) == 1


# ---------------------------------------------------------------------------
# Reliability — abnormal disconnect and heartbeat
# ---------------------------------------------------------------------------

class TestWsReliability:
    def test_slot_freed_after_normal_disconnect(self):
        """Connection slot must be zero after a clean close."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                with client.websocket_connect("/ws/guidance") as ws:
                    ws.send_json({"prompt": "hello"})
                    ws.receive_json()
        assert len(guidance_module._connections) == 0

    def test_slot_freed_after_rate_limit_drop(self):
        """Rate-limit drops must not leave the connection slot occupied."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 1):
                with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", 60):
                    with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                        with pytest.raises(WebSocketDisconnect):
                            with client.websocket_connect("/ws/guidance") as ws:
                                ws.send_json({"prompt": "first"})
                                ws.receive_json()
                                ws.send_json({"prompt": "second"})
                                ws.receive_json()

        assert len(guidance_module._connections) == 0

    def test_slot_freed_after_auth_rejection(self):
        """Auth rejections must never occupy a connection slot."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret"):
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect("/ws/guidance?token=bad") as ws:
                    ws.receive_json()

        assert len(guidance_module._connections) == 0

    def test_multiple_sequential_connections_leave_clean_state(self):
        """After N sequential connections, registry and rate state must be empty."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_HEARTBEAT_INTERVAL_S", 0):
                for _ in range(3):
                    with client.websocket_connect("/ws/guidance") as ws:
                        ws.send_json({"prompt": "hello"})
                        ws.receive_json()

        assert len(guidance_module._connections) == 0
        assert len(guidance_module._rate_state) == 0

    @pytest.mark.asyncio
    async def test_heartbeat_ping_failure_unregisters_stale_connection(self):
        """
        When the heartbeat cannot send a ping the stale slot must be freed
        immediately — without waiting for TCP timeout.
        """
        ws = AsyncMock()
        ws.send_json.side_effect = RuntimeError("broken pipe")

        conn_id = 555
        guidance_module._connections[conn_id] = ws

        # asyncio.sleep is replaced so the heartbeat fires immediately.
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await guidance_module._heartbeat(conn_id, ws, interval=0)

        assert conn_id not in guidance_module._connections

    @pytest.mark.asyncio
    async def test_heartbeat_exits_cleanly_when_already_unregistered(self):
        """
        If the main loop cleaned up before the heartbeat fires, the heartbeat
        must return without attempting a send on a stale socket.
        """
        ws = AsyncMock()
        conn_id = 777
        # conn_id deliberately NOT in _connections — simulates prior cleanup.

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await guidance_module._heartbeat(conn_id, ws, interval=0)

        ws.send_json.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_heartbeat_does_not_double_unregister(self):
        """
        When the heartbeat removes a stale conn_id the registry must contain
        exactly one fewer entry — not go negative or raise.
        """
        ws = AsyncMock()
        ws.send_json.side_effect = RuntimeError("dropped")

        conn_id = 321
        guidance_module._connections[conn_id] = ws

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await guidance_module._heartbeat(conn_id, ws, interval=0)

        # Calling _unregister again (simulating the finally block) must not raise.
        _unregister(conn_id)
        assert conn_id not in guidance_module._connections
