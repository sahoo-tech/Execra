"""
tests/unit/test_exceptions.py

Unit tests for core/exceptions.py.

Verifies that:
- ExecraAPIError stores the correct code, message, and status_code.
- execra_error_handler returns the project's standard error envelope.
- validation_error_handler transforms Pydantic errors into the same format.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from core.exceptions import (
    ExecraAPIError,
    execra_error_handler,
    validation_error_handler,
)
from fastapi.exceptions import RequestValidationError


# ---------------------------------------------------------------------------
# Test ExecraAPIError
# ---------------------------------------------------------------------------

class TestExecraAPIError:
    def test_stores_code(self):
        err = ExecraAPIError(code="INVALID_MODE", message="Bad mode", status_code=400)
        assert err.code == "INVALID_MODE"

    def test_stores_message(self):
        err = ExecraAPIError(code="X", message="Something went wrong", status_code=500)
        assert err.message == "Something went wrong"

    def test_default_status_code(self):
        err = ExecraAPIError(code="X", message="test")
        assert err.status_code == 400

    def test_custom_status_code(self):
        err = ExecraAPIError(code="X", message="test", status_code=404)
        assert err.status_code == 404

    def test_is_exception(self):
        err = ExecraAPIError(code="X", message="test")
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# Test handlers via a real FastAPI test client
# ---------------------------------------------------------------------------

class TestHandlersIntegration:
    """
    Creates a minimal FastAPI app with the custom handlers registered,
    then fires requests to trigger both ExecraAPIError and validation errors.
    """

    @pytest.fixture
    def client(self):
        app = FastAPI()
        app.add_exception_handler(ExecraAPIError, execra_error_handler)
        app.add_exception_handler(RequestValidationError, validation_error_handler)

        class DummyBody(BaseModel):
            name: str = Field(..., min_length=1)

        @app.post("/test-validation")
        async def test_validation(body: DummyBody):
            return {"ok": True}

        @app.get("/test-custom-error")
        async def test_custom_error():
            raise ExecraAPIError(
                code="INVALID_MODE",
                message="Unknown mode value provided.",
                status_code=400,
            )

        @app.get("/test-not-found")
        async def test_not_found():
            raise ExecraAPIError(
                code="CONTEXT_NOT_FOUND",
                message="No active session context found.",
                status_code=404,
            )

        return TestClient(app)

    def test_custom_error_returns_correct_format(self, client):
        resp = client.get("/test-custom-error")
        assert resp.status_code == 400
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_MODE"
        assert data["error"]["status"] == 400

    def test_custom_error_404(self, client):
        resp = client.get("/test-not-found")
        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "CONTEXT_NOT_FOUND"
        assert data["error"]["status"] == 404

    def test_validation_error_returns_execra_format(self, client):
        # Send empty body to trigger Pydantic validation error
        resp = client.post("/test-validation", json={})
        assert resp.status_code == 400
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["status"] == 400
        assert "name" in data["error"]["message"].lower()

    def test_validation_error_wrong_type(self, client):
        resp = client.post("/test-validation", json={"name": 12345})
        # Pydantic v2 with min_length rejects non-string types
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_valid_request_passes(self, client):
        resp = client.post("/test-validation", json={"name": "Aditya"})
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
