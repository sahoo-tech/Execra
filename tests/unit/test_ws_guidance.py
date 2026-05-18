"""
Unit and integration tests for api/websockets/guidance.py.

Test strategy
-------------
Security-helper functions (_verify_token, _check_rate_limit) are tested
directly as pure functions.  The WebSocket endpoint is tested end-to-end
via FastAPI's TestClient.websocket_connect() context manager, which speaks
the real WebSocket protocol through an in-process ASGI transport.

Each test that touches module-level state (_active_connections, _rate_state)
resets that state in a fixture to prevent cross-test contamination.

WebSocket close code semantics
-------------------------------
4401 — Unauthorized
4429 — Rate limit exceeded
4503 — Connection limit reached (server busy)
1000 — Normal closure
"""
from __future__ import annotations

import time
from collections import deque
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from api.main import app
import api.websockets.guidance as guidance_module
from api.websockets.guidance import _check_rate_limit, _verify_token

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_ws_state():
    """Clear module-level connection and rate-limit state before every test."""
    guidance_module._active_connections.clear()
    guidance_module._rate_state.clear()
    yield
    guidance_module._active_connections.clear()
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
        """Verify that compare_digest is used (not ==) by checking the module
        uses hmac.compare_digest — structural test via source inspection."""
        import inspect
        import hmac as _hmac
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
        window = 1  # 1 second window for fast test
        with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 2):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", window):
                # Fill the window
                _check_rate_limit(conn_id)
                _check_rate_limit(conn_id)
                assert _check_rate_limit(conn_id) is False  # limit hit

                # Simulate time passing beyond the window
                old_timestamps = guidance_module._rate_state[conn_id]
                # Artificially age all timestamps so they fall outside the window
                aged = deque(t - (window + 1) for t in old_timestamps)
                guidance_module._rate_state[conn_id] = aged

                # Now messages should be allowed again
                assert _check_rate_limit(conn_id) is True

    def test_independent_connections_have_independent_limits(self):
        with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 2):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", 60):
                _check_rate_limit(conn_id=10)
                _check_rate_limit(conn_id=10)
                # conn_id 10 is now at limit
                assert _check_rate_limit(10) is False
                # conn_id 20 is untouched
                assert _check_rate_limit(20) is True

    def test_rate_state_initialised_for_new_connection(self):
        """_rate_state should get an entry on first call."""
        conn_id = 99
        assert conn_id not in guidance_module._rate_state
        _check_rate_limit(conn_id)
        assert conn_id in guidance_module._rate_state


# ---------------------------------------------------------------------------
# WebSocket endpoint — authentication
# ---------------------------------------------------------------------------

class TestWsAuthentication:
    def test_no_token_rejected_when_configured(self):
        """Connecting without a token is rejected with code 4401."""
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
        """A correct token allows the connection to proceed normally."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret"):
            with client.websocket_connect("/ws/guidance?token=secret") as ws:
                ws.send_json({"prompt": "hello"})
                data = ws.receive_json()
                assert "guidance" in data

    def test_no_auth_when_token_not_configured(self):
        """Empty WS_API_TOKEN allows any connection (dev mode)."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with client.websocket_connect("/ws/guidance") as ws:
                ws.send_json({"prompt": "hello"})
                data = ws.receive_json()
                assert "guidance" in data

    def test_rejected_connection_does_not_occupy_slot(self):
        """Auth failure must not increment the active connection count."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", "secret"):
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect("/ws/guidance?token=wrong") as ws:
                    ws.receive_json()
        assert len(guidance_module._active_connections) == 0


# ---------------------------------------------------------------------------
# WebSocket endpoint — connection limit
# ---------------------------------------------------------------------------

class TestWsConnectionLimit:
    def test_connection_within_limit_accepted(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_MAX_CONNECTIONS", 5):
                with client.websocket_connect("/ws/guidance") as ws:
                    ws.send_json({"prompt": "hi"})
                    data = ws.receive_json()
                    assert "guidance" in data

    def test_connection_at_limit_rejected(self):
        """A new connection when the cap is reached receives code 4503."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_MAX_CONNECTIONS", 0):
                with pytest.raises(WebSocketDisconnect) as exc_info:
                    with client.websocket_connect("/ws/guidance") as ws:
                        ws.receive_json()
                assert exc_info.value.code == 4503

    def test_active_count_increments_on_connect(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with client.websocket_connect("/ws/guidance"):
                assert len(guidance_module._active_connections) == 1

    def test_active_count_decrements_on_disconnect(self):
        """Connection slot must be released after the session ends."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with client.websocket_connect("/ws/guidance") as ws:
                ws.send_json({"prompt": "test"})
                ws.receive_json()
        # After the context manager exits the connection is cleaned up
        assert len(guidance_module._active_connections) == 0

    def test_limit_not_consumed_by_rejected_connection(self):
        """Rejected connections (limit=0) must not permanently fill the slot."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_MAX_CONNECTIONS", 0):
                # Rejected attempt
                with pytest.raises(WebSocketDisconnect):
                    with client.websocket_connect("/ws/guidance") as ws:
                        ws.receive_json()
            # Cap restored to default; slot count must be 0
            assert len(guidance_module._active_connections) == 0


# ---------------------------------------------------------------------------
# WebSocket endpoint — rate limiting
# ---------------------------------------------------------------------------

class TestWsRateLimiting:
    def test_messages_within_limit_receive_guidance(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 5):
                with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", 60):
                    with client.websocket_connect("/ws/guidance") as ws:
                        for _ in range(3):
                            ws.send_json({"prompt": "test"})
                            data = ws.receive_json()
                            assert "guidance" in data

    def test_exceeding_rate_limit_closes_connection(self):
        """After the rate limit is exhausted the server closes with 4429."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with patch.object(guidance_module.settings, "WS_RATE_LIMIT_MESSAGES", 2):
                with patch.object(guidance_module.settings, "WS_RATE_LIMIT_WINDOW_S", 60):
                    with pytest.raises(WebSocketDisconnect) as exc_info:
                        with client.websocket_connect("/ws/guidance") as ws:
                            # Consume the full allowance
                            ws.send_json({"prompt": "msg1"})
                            ws.receive_json()
                            ws.send_json({"prompt": "msg2"})
                            ws.receive_json()
                            # Next receive_json triggers the rate-limit path:
                            # the server checks before reading and closes 4429
                            ws.send_json({"prompt": "msg3"})
                            ws.receive_json()  # should raise
                    assert exc_info.value.code == 4429

    def test_rate_state_cleaned_up_after_disconnect(self):
        """_rate_state entry must be removed when the connection ends."""
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
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
            with client.websocket_connect("/ws/guidance") as ws:
                ws.send_json({"prompt": "How do I fix this bug?"})
                data = ws.receive_json()
                assert "guidance" in data
                assert isinstance(data["guidance"], str)

    def test_missing_prompt_returns_error_key(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with client.websocket_connect("/ws/guidance") as ws:
                ws.send_json({})
                data = ws.receive_json()
                assert "error" in data
                assert "prompt" in data["error"].lower()

    def test_empty_prompt_returns_error_key(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
            with client.websocket_connect("/ws/guidance") as ws:
                ws.send_json({"prompt": "   "})
                data = ws.receive_json()
                assert "error" in data

    def test_multiple_messages_in_one_session(self):
        with patch.object(guidance_module.settings, "WS_API_TOKEN", ""):
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
        """Default settings values must be present on the settings object."""
        from core.config import settings as cfg
        assert isinstance(cfg.WS_API_TOKEN, str)
        assert isinstance(cfg.WS_MAX_CONNECTIONS, int)
        assert cfg.WS_MAX_CONNECTIONS > 0
        assert isinstance(cfg.WS_RATE_LIMIT_MESSAGES, int)
        assert cfg.WS_RATE_LIMIT_MESSAGES > 0
        assert isinstance(cfg.WS_RATE_LIMIT_WINDOW_S, int)
        assert cfg.WS_RATE_LIMIT_WINDOW_S > 0

    def test_env_override_ws_max_connections(self):
        """WS_MAX_CONNECTIONS must be overridable via environment variable."""
        import os
        from unittest.mock import patch as _patch
        from core.config import Settings
        with _patch.dict(os.environ, {"WS_MAX_CONNECTIONS": "25"}):
            s = Settings()
            assert s.WS_MAX_CONNECTIONS == 25

    def test_env_override_ws_api_token(self):
        import os
        from unittest.mock import patch as _patch
        from core.config import Settings
        with _patch.dict(os.environ, {"WS_API_TOKEN": "prod-secret"}):
            s = Settings()
            assert s.WS_API_TOKEN == "prod-secret"

    def test_env_override_rate_limit_messages(self):
        import os
        from unittest.mock import patch as _patch
        from core.config import Settings
        with _patch.dict(os.environ, {"WS_RATE_LIMIT_MESSAGES": "100"}):
            s = Settings()
            assert s.WS_RATE_LIMIT_MESSAGES == 100

    def test_env_override_rate_limit_window(self):
        import os
        from unittest.mock import patch as _patch
        from core.config import Settings
        with _patch.dict(os.environ, {"WS_RATE_LIMIT_WINDOW_S": "30"}):
            s = Settings()
            assert s.WS_RATE_LIMIT_WINDOW_S == 30
