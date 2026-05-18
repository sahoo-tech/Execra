import threading
from typing import Dict, Union



class MetricsStore:
    """
    thread safe singleton for runtime counters and gauges.
    counters go up to (increment) and gauges can be set to any float.
    """

    FRAMES_CAPTURED = "frames_captured"
    FRAMES_FORWARDED = "frames_forwarded"
    OCR_CALLS = "ocr_calls"
    LLM_CALLS = "llm_calls"
    GUIDANCE_DELIVERED = "guidance_delivered"
    ERRORS_DETECTED = "errors_detected"
    WS_CONNECTIONS_ACTIVE = "ws_connections_active"

    def __init__(self)->None:
        self._lock = threading.Lock()
        self._counters: Dict[str,int] = {
            self.FRAMES_CAPTURED: 0,
            self.FRAMES_FORWARDED: 0,
            self.OCR_CALLS: 0,
            self.LLM_CALLS: 0,
            self.GUIDANCE_DELIVERED: 0,
            self.ERRORS_DETECTED: 0,
            self.WS_CONNECTIONS_ACTIVE: 0,
        }

        self._gauges: Dict[str,float]={}

    def increment(self, key: str, amount: int = 1) -> None:
        """Atomically add 'amount' to a counter. Creates the key if missing."""
        with self._lock:   # 'with' releases the lock even if an exception occurs
            self._counters[key] = self._counters.get(key, 0) + amount

    def set_gauge(self, key: str, value: float) -> None:
        """Set a gauge to an exact float value. Creates the key if missing."""
        with self._lock:
            self._gauges[key] = value

    def snapshot(self) -> dict:
        """Returns a copy of all current counters and gauges for reporting."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }


metrics_store = MetricsStore()