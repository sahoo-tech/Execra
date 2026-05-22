"""
api/main.py
===========
FastAPI application for Execra.

Lifecycle:
  • On startup  → initialise and start ExecraPipeline
  • On shutdown → cleanly stop the pipeline

WebSocket endpoint  /ws/guidance
  • Clients connect here to receive real-time guidance JSON.

REST endpoints:
  • GET  /health   – liveness probe
  • GET  /metrics  – pipeline runtime metrics
  • POST /frame    – inject a synthetic frame (testing / demos)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.pipeline import (
    Domain,
    ExecraPipeline,
    Mode,
    PerceptionFrame,
    PipelineConfig,
)

logger = logging.getLogger(__name__)

# Module-level pipeline reference.
# Set by main.py (production) or by lifespan below (standalone uvicorn).
pipeline: Optional[ExecraPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown lifecycle.

    When running standalone (`uvicorn api.main:app`) the pipeline is created
    here. When launched via main.py it is already injected before the server
    starts, so this block is a no-op.
    """
    global pipeline

    standalone = pipeline is None
    if standalone:
        logger.info("[API] standalone mode – creating pipeline")
        import asyncio
        pipeline = ExecraPipeline(
            domain=Domain.DIGITAL,
            mode=Mode.PASSIVE,
            config=PipelineConfig(),
        )
        asyncio.create_task(pipeline.run(), name="api_pipeline")

    yield  # --- application is running ---

    if standalone and pipeline is not None:
        await pipeline.stop()


app = FastAPI(
    title="Execra API",
    version="0.1.0",
    description="Real-time AI execution guidance system",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class FramePayload(BaseModel):
    source: str = "api"
    data: str = ""
    task_type: Optional[str] = None


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {
        "status": "ok",
        "pipeline_running": pipeline is not None and pipeline._running,
    }


@app.get("/metrics", tags=["system"])
async def metrics() -> dict:
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialised")
    return pipeline.get_metrics()


@app.post("/frame", tags=["ingestion"])
async def inject_frame(payload: FramePayload) -> dict:
    """Inject a synthetic perception frame into the pipeline."""
    if pipeline is None:
        raise HTTPException(503, "Pipeline not initialised")

    frame = PerceptionFrame(
        source=payload.source,
        data=payload.data,
        metadata={"task_type": payload.task_type or "general"},
    )
    await pipeline.perception_bus.put_frame(frame)
    return {"status": "accepted"}


@app.websocket("/ws/guidance")
async def ws_guidance(websocket: WebSocket) -> None:
    """
    Real-time guidance stream.

    Connect: ws://localhost:8000/ws/guidance

    Each message is JSON:
        {
          "instruction": "...",
          "confidence": 0.87,
          "source": "hybrid",
          "reasoning": "...",
          "mode": "safe",
          "frame_ts": 1234567890.123,
          "dispatched_at": 1234567890.456
        }
    """
    if pipeline is None:
        await websocket.close(code=1011, reason="Pipeline not ready")
        return

    await websocket.accept()
    pipeline.dispatcher.register_client(websocket)
    client = websocket.client
    logger.info("[WS] client connected: %s", client)

    try:
        while True:
            await websocket.receive_text()   # keep-alive; handle ping/control
    except WebSocketDisconnect:
        logger.info("[WS] client disconnected: %s", client)
    finally:
        pipeline.dispatcher.unregister_client(websocket)