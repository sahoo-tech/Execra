import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.mode import router as mode_router
from api.routes.status import router as status_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.start_time = time.time()
    print("Execra API starting...")
    try:
        yield
    finally:
        print("Execra API shutting down...")


app = FastAPI(
    title="Execra API",
    version="0.1.0",
    description="Execra backend API",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Execra is running",
        "version": "0.1.0"
    }

app.include_router(status_router, prefix="/api/v1")
app.include_router(mode_router, prefix="/api/v1")