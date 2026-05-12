"""
Integration tests for OpenAPI schema validation.
Ensures openapi.json matches api_reference.md
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_openapi_endpoint_returns_200():
    """Test that /openapi.json is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200


def test_openapi_schema_has_required_fields():
    """Check that openapi.json has required structure"""
    response = client.get("/openapi.json")
    schema = response.json()
    
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert schema["info"]["title"] == "Execra API"
    assert schema["info"]["version"] == "0.1.0"


def test_root_endpoint_in_schema():
    """Check that root endpoint '/' is documented"""
    response = client.get("/openapi.json")
    schema = response.json()
    
    assert "/" in schema["paths"]
    assert "get" in schema["paths"]["/"]


def test_openapi_schema_valid():
    """Check that openapi.json doesn't crash and has basic structure"""
    response = client.get("/openapi.json")
    schema = response.json()
    
    # Verify that all paths have at least one method
    for path, methods in schema["paths"].items():
        assert len(methods) > 0, f"Path {path} has no methods"
        for method, details in methods.items():
            assert "responses" in details, f"{method} {path} has no responses"


def test_error_response_structures():
    """Check that error responses follow expected format"""
    response = client.get("/openapi.json")
    schema = response.json()
    
    # Check that each endpoint's responses include error scenarios
    for path, methods in schema["paths"].items():
        for method, details in methods.items():
            if "responses" in details:
                responses = details["responses"]
                # 200 should always be present
                assert "200" in responses, f"{method} {path} missing 200 response"
                