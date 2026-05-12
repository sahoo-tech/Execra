from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import redis

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
    print("Execra API starting...")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("Execra API shutting down...")

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Execra is running",
        "version": "0.1.0"
    }

@app.get("/api/v1/health")
async def health_check(response: Response):
    """Health check endpoint for container orchestrators."""
    
    checks = {}
    healthy = True
    
    # 1. Check SQLite connectivity
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("SELECT 1")
        conn.close()
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = "error"
        healthy = False
        print(f"Database check failed: {e}")
    
    # 2. Check Redis connectivity
    try:
        r = redis.Redis(
            host="localhost", 
            port=6379, 
            decode_responses=True,
            socket_connect_timeout=2
        )
        r.ping()
        checks["redis"] = "ok"
        r.close()
    except Exception as e:
        checks["redis"] = "error"
        healthy = False
        print(f"Redis check failed: {e}")
    
    # Set status code to 503 if unhealthy
    if not healthy:
        response.status_code = 503
    
    return {"healthy": healthy, "checks": checks}

# Placeholder routers
# from api.routes import users
# app.include_router(users.router)
