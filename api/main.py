import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.routes import status, mode
from api.routes import actions, context
from core.config import settings
from core.pipeline import (
    Domain, ExecraPipeline, Mode, PerceptionFrame, PipelineConfig,
)

logger = logging.getLogger(__name__)

# Module-level pipeline reference.
# Set by main.py (production) or by lifespan below (standalone uvicorn).
pipeline: Optional[ExecraPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start pipeline on startup, stop it on shutdown."""
    global pipeline
    standalone = pipeline is None
    if standalone:
        logger.info("[API] standalone mode – creating pipeline")
        pipeline = ExecraPipeline(
            domain=Domain.DIGITAL,
            mode=Mode.PASSIVE,
            config=PipelineConfig(),
        )
        asyncio.create_task(pipeline.run(), name="api_pipeline")

    logger.info("Execra API starting...")
    yield

    if standalone and pipeline is not None:
        await pipeline.stop()
    logger.info("Execra API shutting down...")


app = FastAPI(
    title="Execra API",
    version="0.1.0",
    description="Execra backend API",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routes
app.include_router(status.router, prefix="/api/v1")
app.include_router(mode.router, prefix="/api/v1")
app.include_router(actions.router, prefix="/api/v1")
app.include_router(context.router, prefix="/api/v1")


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Execra is running", "version": "0.1.0"}


# Pipeline endpoints
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
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("[WS] client disconnected: %s", client)
    finally:
        pipeline.dispatcher.unregister_client(websocket)