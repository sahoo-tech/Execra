# Execra/api/routes/metrics.py

from fastapi import APIRouter
from core.monitoring.metrics_store import metrics_store

router = APIRouter()

@router.get("/metrics", summary="Runtime metrics snapshot")
async def get_metrics() -> dict:
    """
    Returns a point-in-time snapshot of all runtime counters and gauges.
    Safe to poll frequently — snapshot() is O(n) and lock-free for callers.
    """
    return metrics_store.snapshot()