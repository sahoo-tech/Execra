import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import status, mode
from api.routes import actions, context
from api.websockets import guidance as ws_guidance

from core.config import settings

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


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Execra API shutting down...")


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Execra is running", "version": "0.1.0"}


# Routes

app.include_router(status.router, prefix="/api/v1")
app.include_router(mode.router, prefix="/api/v1")


# from api.routes import users
# app.include_router(users.router)

# Action log and session context endpoints
app.include_router(actions.router, prefix="/api/v1")
app.include_router(context.router, prefix="/api/v1")

# WebSocket endpoints (no prefix — WS routes use the path as-is)
app.include_router(ws_guidance.router)