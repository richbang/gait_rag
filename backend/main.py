"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from core.config import get_settings
from core.logging import setup_logging
from core.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware, limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from database.session import init_db

# Import routers
from auth.router import router as auth_router
from chat.router import router as chat_router

settings = get_settings()

# Setup logging
setup_logging(settings.log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")
    
    yield
    logger.info("Shutting down application")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# Add custom middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Medical Gait RAG WebUI API",
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/api/v1/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=settings.environment == "development"
    )
