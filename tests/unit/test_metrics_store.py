# Execra/tests/unit/test_metrics_store.py

import threading
from core.monitoring.metrics_store import MetricsStore   # import the CLASS, not singleton
                                                          # so each test gets a fresh instance


def make_store() -> MetricsStore:
    """Helper: fresh store for each test — avoids state leaking between tests."""
    return MetricsStore()


# ── increment ────────────────────────────────────────────────────────────────

def test_increment_default_amount():
    store = make_store()
    store.increment("frames_captured")
    assert store.snapshot()["counters"]["frames_captured"] == 1


def test_increment_custom_amount():
    store = make_store()
    store.increment("ocr_calls", 5)
    assert store.snapshot()["counters"]["ocr_calls"] == 5


def test_increment_accumulates():
    store = make_store()
    store.increment("llm_calls")
    store.increment("llm_calls")
    store.increment("llm_calls")
    assert store.snapshot()["counters"]["llm_calls"] == 3


def test_increment_unknown_key_creates_counter():
    """increment() on an unknown key should create it rather than crash."""
    store = make_store()
    store.increment("my_custom_counter", 2)
    assert store.snapshot()["counters"]["my_custom_counter"] == 2


def test_increment_thread_safe():
    """
    50 threads each increment the same counter 100 times.
    Without a lock the final value would be < 5000 due to race conditions.
    """
    store = make_store()
    threads = [
        threading.Thread(target=lambda: [store.increment("frames_captured") for _ in range(100)])
        for _ in range(50)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert store.snapshot()["counters"]["frames_captured"] == 5000


# ── set_gauge ────────────────────────────────────────────────────────────────

def test_set_gauge_creates_entry():
    store = make_store()
    store.set_gauge("current_fps", 9.87)
    assert store.snapshot()["gauges"]["current_fps"] == 9.87


def test_set_gauge_overwrites():
    store = make_store()
    store.set_gauge("current_fps", 9.87)
    store.set_gauge("current_fps", 30.0)   # overwrite
    assert store.snapshot()["gauges"]["current_fps"] == 30.0


# ── snapshot ─────────────────────────────────────────────────────────────────

def test_snapshot_is_copy_not_live_reference():
    """
    Mutating the snapshot dict must NOT affect the store's internal state.
    If snapshot() returned the live dict instead of a copy this would fail.
    """
    store = make_store()
    snap = store.snapshot()
    snap["counters"]["frames_captured"] = 9999   # tamper with the snapshot
    # The store itself must be unchanged
    assert store.snapshot()["counters"]["frames_captured"] == 0


def test_snapshot_contains_all_predefined_counters():
    store = make_store()
    snap = store.snapshot()
    expected_keys = {
        "frames_captured", "frames_forwarded", "ocr_calls",
        "llm_calls", "guidance_delivered", "errors_detected",
        "ws_connections_active",
    }
    assert expected_keys.issubset(snap["counters"].keys())