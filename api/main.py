import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import actions, context, mode, status, suppression
from api.websockets import guidance as ws_guidance
from core.config import settings
from core.errors import handle_exception
from core.hybrid.action_logger import action_logger

logger = logging.getLogger(__name__)

app = FastAPI(title="Execra API", version="0.1.0", description="Execra backend API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # Restore persisted action history and undo state from SQLite.
    await action_logger.load()
    from api.websockets.router import broadcast_action_log
    action_logger.register_callback(broadcast_action_log)
    logger.info("Execra API starting...")


@app.on_event("shutdown")
async def shutdown_event():
    from api.websockets.router import broadcast_action_log
    action_logger.unregister_callback(broadcast_action_log)
    logger.info("Execra API shutting down...")


@app.get("/")
def read_root():
    try:
        return {"status": "success", "data": {"message": "Execra is running", "version": "0.1.0"}}
    except Exception as e:
        return handle_exception(e)


try:
    app.include_router(status.router, prefix="/api/v1")
    app.include_router(mode.router, prefix="/api/v1")
    app.include_router(actions.router, prefix="/api/v1")
    app.include_router(context.router, prefix="/api/v1")
except Exception as e:
    handle_exception(e)

app.include_router(ws_guidance.router)
app.include_router(suppression.router, prefix="/api/v1")
