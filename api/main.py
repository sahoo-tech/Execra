from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from core.config import settings

app = FastAPI(
    title="Execra API",
    version="0.1.0",
    description="Execra backend API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    print(f"Execra API v{settings.API_PORT} starting...")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("Execra API shutting down...")


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Execra is running", "version": "0.1.0"}


# Health check endpoint
@app.get("/health")
def health_check():
    """
    Returns the health status of the API and its subsystems.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "subsystems": {
            "api": "UP",
            "core": "UP"
        }
    }


# Placeholder routers
# from api.routes import users
# app.include_router(users.router)
