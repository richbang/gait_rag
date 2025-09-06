"""Main FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import time

from core.config import get_settings
from core.logging import setup_logging
from core.middleware import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from database.session import init_db

# Import routers
from auth.router import router as auth_router
from auth.admin_router import router as admin_router
from chat.router import router as chat_router
from rag.routes import router as rag_router

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

# Configure CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
    return response

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(rag_router)


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
