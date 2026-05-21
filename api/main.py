import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import status, mode
from api.routes import actions, context
from api.websockets import guidance as ws_guidance

from core.config import settings
from core.errors import handle_exception  # ✅ NEW

from api.routes import suppression

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


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Execra API starting...")
    from api.websockets.router import broadcast_action_log
    from core.hybrid.action_logger import action_logger
    action_logger.register_callback(broadcast_action_log)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Execra API shutting down...")
    from api.websockets.router import broadcast_action_log
    from core.hybrid.action_logger import action_logger
    action_logger.unregister_callback(broadcast_action_log)


# Root endpoint
@app.get("/")
def read_root():
    try:
        return {
            "status": "success",
            "data": {
                "message": "Execra is running",
                "version": "0.1.0"
            }
        }
    except Exception as e:
        return handle_exception(e)


# Routes (wrapped safely)

try:
    app.include_router(status.router, prefix="/api/v1")
    app.include_router(mode.router, prefix="/api/v1")
    app.include_router(actions.router, prefix="/api/v1")
    app.include_router(context.router, prefix="/api/v1")

except Exception as e:
    handle_exception(e)


# Action log and session context endpoints
app.include_router(actions.router, prefix="/api/v1")
app.include_router(context.router, prefix="/api/v1")

# WebSocket endpoints (no prefix — WS routes use the path as-is)
app.include_router(ws_guidance.router)

# Alert suppression endpoints 
app.include_router(suppression.router, prefix="/api/v1")