from fastapi.testclient import TestClient
from api.main import app
from core.monitoring.metrics_store import MetricsStore, metrics_store

client = TestClient(app)


def test_metrics_endpoint_returns_200():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200


def test_metrics_response_has_counters_and_gauges_keys():
    response = client.get("/api/v1/metrics")
    data = response.json()
    assert "counters" in data
    assert "gauges" in data


def test_metrics_counters_contains_all_predefined_keys():
    response = client.get("/api/v1/metrics")
    counters = response.json()["counters"]
    expected = {
        "frames_captured",
        "frames_forwarded",
        "ocr_calls",
        "llm_calls",
        "guidance_delivered",
        "errors_detected",
        "ws_connections_active",
    }
    assert expected.issubset(counters.keys())


def test_metrics_counters_are_integers():
    response = client.get("/api/v1/metrics")
    for key, val in response.json()["counters"].items():
        assert isinstance(val, int), f"Counter '{key}' is not an int: {val!r}"


def test_metrics_reflects_manual_increment():
    """Increment a counter via the store, then verify the endpoint reports it."""
    before = client.get("/api/v1/metrics").json()["counters"]["llm_calls"]
    metrics_store.increment(metrics_store.LLM_CALLS, 3)
    after = client.get("/api/v1/metrics").json()["counters"]["llm_calls"]
    assert after == before + 3


def test_metrics_reflects_gauge_set():
    """Set a gauge via the store, then verify the endpoint reports it."""
    metrics_store.set_gauge("test_fps", 42.5)
    data = client.get("/api/v1/metrics").json()
    assert data["gauges"]["test_fps"] == 42.5


def test_metrics_gauges_are_floats_or_ints():
    metrics_store.set_gauge("sanity_check", 1.0)
    gauges = client.get("/api/v1/metrics").json()["gauges"]
    for key, val in gauges.items():
        assert isinstance(val, (int, float)), f"Gauge '{key}' is not numeric: {val!r}"
