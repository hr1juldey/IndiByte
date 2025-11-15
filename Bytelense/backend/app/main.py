"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.core.config import settings
from app.core.searxng_keepalive import init_keepalive, shutdown_keepalive

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

    # Start SearXNG keep-alive to prevent container from sleeping
    logger.info(f"Starting SearXNG keep-alive task (pinging every 600 seconds)")
    init_keepalive(settings.searxng_url)

    yield

    # Shutdown keep-alive task
    logger.info("Stopping SearXNG keep-alive task")
    await shutdown_keepalive()
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
    """
    Comprehensive health check endpoint.

    Returns status of all critical services:
    - Ollama (LLM models)
    - SearXNG (search)
    - Storage (profile directory)
    - OpenFoodFacts API
    """
    import httpx
    import os
    from datetime import datetime

    services = {}
    all_ok = True

    # Check Ollama
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.ollama_api_base}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                models = [m['name'] for m in data.get('models', [])]
                services['ollama'] = {
                    'status': 'connected',
                    'model_configured': settings.ollama_model,
                    'models_available': models,
                    'model_ready': settings.ollama_model in models
                }
                if settings.ollama_model not in models:
                    all_ok = False
            else:
                services['ollama'] = {'status': 'error', 'error': f'HTTP {resp.status_code}'}
                all_ok = False
    except Exception as e:
        services['ollama'] = {'status': 'unreachable', 'error': str(e)}
        all_ok = False

    # Check SearXNG (non-critical - keep-alive task handles it)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.searxng_url}/search",
                params={"q": "test", "format": "json"},
                timeout=5.0
            )
            if resp.status_code == 200:
                services['searxng'] = {'status': 'connected', 'url': settings.searxng_url}
            else:
                services['searxng'] = {'status': 'error', 'error': f'HTTP {resp.status_code}'}
                # Don't mark all_ok as False - SearXNG is non-critical
    except Exception as e:
        services['searxng'] = {'status': 'unreachable', 'error': str(e), 'note': 'Keep-alive task will wake it up'}
        # Don't mark all_ok as False - SearXNG is non-critical

    # Check Storage
    try:
        profiles_path = settings.profiles_dir
        if os.path.exists(profiles_path) and os.path.isdir(profiles_path):
            profile_count = len([f for f in os.listdir(profiles_path) if f.endswith('.json')])
            services['storage'] = {
                'status': 'ok',
                'path': profiles_path,
                'profiles_count': profile_count
            }
        else:
            services['storage'] = {'status': 'error', 'error': 'Directory not found'}
            all_ok = False
    except Exception as e:
        services['storage'] = {'status': 'error', 'error': str(e)}
        all_ok = False

    # Check OpenFoodFacts
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.openfoodfacts_api_base}/api/v0/product/737628064502.json",
                timeout=settings.openfoodfacts_timeout
            )
            if resp.status_code == 200:
                services['openfoodfacts'] = {'status': 'connected'}
            else:
                services['openfoodfacts'] = {'status': 'error', 'error': f'HTTP {resp.status_code}'}
    except Exception as e:
        services['openfoodfacts'] = {'status': 'degraded', 'error': str(e)}
        # Don't mark all_ok as False - OpenFoodFacts is not critical

    return {
        "status": "ok" if all_ok else "degraded",
        "app": settings.app_name,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services
    }


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
# Use scan_simple for initial testing (no LLM/OCR dependencies)
# Switch to 'scan' for full pipeline
from app.api import auth, scan_simple  # noqa: F401 - scan_simple registers SocketIO events

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
