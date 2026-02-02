import os
import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Load environment variables first
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print("✅ Environment variables loaded from .env")
else:
    print("⚠️  No .env file found")

# Import app modules after environment is loaded
from app.routers import rag, analytics, support, voice_support, websocket
from app.database import engine
from app.models import Base
from app.config import Settings
from app.rate_limiter import limiter, rate_limit_exceeded_handler
from app.middleware.logging import LoggingMiddleware, setup_structured_logging

# Initialize settings
settings = Settings()

# Setup structured logging
setup_structured_logging(log_level="INFO" if not settings.DEBUG else "DEBUG")

app = FastAPI(
    title="RAG-Support-Agent",
    description="Support system with RAG capabilities",
    version="1.0.0",
    debug=settings.DEBUG
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add GZip compression middleware (for responses > 1KB)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add structured logging middleware
app.add_middleware(LoggingMiddleware)

# CORS middleware - configure based on environment
allowed_origins = ["*"] if settings.DEBUG else ["http://localhost:3000", "http://localhost:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rag.router)
app.include_router(analytics.router)
app.include_router(support.router)
app.include_router(voice_support.router)
app.include_router(websocket.router)

# Original computer info models
class ScreenResolution(BaseModel):
    width: int
    height: int
    colorDepth: int

class ConnectionInfo(BaseModel):
    effectiveType: Optional[str] = None
    downlink: Optional[float] = None
    rtt: Optional[float] = None

class ComputerInfo(BaseModel):
    userAgent: str
    platform: str
    language: str
    hardwareConcurrency: Optional[int] = None
    deviceMemory: Optional[float] = None
    screenResolution: ScreenResolution
    timezone: str
    connection: Optional[ConnectionInfo] = None
    cookieEnabled: bool
    doNotTrack: Optional[str] = None
    ipAddress: Optional[str] = None

# Create tables on startup
@app.on_event("startup")
async def on_startup():
    print("🚀 Starting RAG-Support-Agent Backend...")
    print(f"📍 Debug mode: {settings.DEBUG}")
    print(f"📍 Host: {settings.HOST}:{settings.PORT}")
    print(f"📍 Database: {settings.DATABASE_URL[:50]}...")
    print(f"📍 Gemini Model: {settings.GEMINI_MODEL}")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

@app.on_event("shutdown")
async def on_shutdown():
    print("🛑 Shutting down RAG-Support-Agent Backend...")


# Original endpoint for computer info
@app.post("/api/start-chat")
async def start_chat(computer_info: ComputerInfo):
    print("Received computer info:", computer_info.dict())
    return {"status": "success", "message": "Computer info received"}

@app.get("/")
async def root():
    return {
        "message": "RAG-Support-Agent API", 
        "status": "running",
        "version": "1.0.0",
        "debug": settings.DEBUG,
        "environment": "development" if settings.DEBUG else "production"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "RAG-Support-Agent",
        "version": "1.0.0"
    }

def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = ["DATABASE_URL", "GOOGLE_PROJECT_ID"]
    missing_vars = []
    
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Optional environment variables not set: {', '.join(missing_vars)}")
    else:
        print("✅ All required environment variables are set")

if __name__ == "__main__":
    print("🔧 Validating environment...")
    validate_environment()
    
    print(f"🚀 Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
