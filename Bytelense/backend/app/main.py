"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Ollama model: {settings.ollama_model}")
    logger.info(f"Profiles directory: {settings.profiles_dir}")
    yield
    logger.info(f"Shutting down {settings.app_name}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered food scanning and nutritional analysis",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server (will be configured later)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=settings.debug,
    engineio_logger=settings.debug
)

# Wrap FastAPI app with Socket.IO
socket_app = socketio.ASGIApp(sio, app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/config")
async def get_config():
    """Client configuration endpoint."""
    return {
        "features": {
            "camera": True,
            "upload": True,
            "generative_ui": True,
            "citations": True
        },
        "limits": {
            "max_image_size_mb": settings.max_image_size_mb
        }
    }


# Import routers and WebSocket handlers
from app.api import auth, scan  # noqa: F401 - scan registers SocketIO events

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:socket_app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        loop="uvloop"
    )
