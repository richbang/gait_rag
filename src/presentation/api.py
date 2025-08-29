"""
FastAPI Application - Clean Architecture Version
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from ..container import get_container, Container
from ..infrastructure.config import Settings
from .routes import setup_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting up Medical Gait Analysis RAG API")
    container = get_container()
    
    # Warmup embedding service
    try:
        await container.embedding_service.embed_query("test query")
        logger.info("Embedding service warmed up")
    except Exception as e:
        logger.warning(f"Failed to warm up embedding service: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API")


def create_app(container: Container = None) -> FastAPI:
    """Create FastAPI application with dependency injection"""
    
    if container is None:
        container = get_container()
    
    settings = container.settings
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Medical Gait Analysis RAG System - Clean Architecture",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store container in app state
    app.state.container = container
    
    # Setup routes
    setup_routes(app)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc) if settings.debug else "An error occurred"
            }
        )
    
    return app


# Create default app instance
app = create_app()