from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import init_db

app = FastAPI(
    title="Execra API",
    version="0.1.0",
    description="Execra backend API",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only — restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize the SQLite database tables on server start."""
    await init_db()


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources on server shutdown."""


# Root endpoint
@app.get("/")
def read_root() -> dict:
    return {
        "message": "Execra is running",
        "version": "0.1.0",
    }

# Placeholder routers (uncomment as modules are implemented)
# from api.routes import status, mode, actions
# app.include_router(status.router, prefix="/api/v1")
# app.include_router(mode.router, prefix="/api/v1")
# app.include_router(actions.router, prefix="/api/v1")