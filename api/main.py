from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Placeholder routers
# from api.routes import users
# app.include_router(users.router)