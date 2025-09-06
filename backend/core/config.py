"""Configuration management."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "sqlite:///./gait_rag.db"
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24
    
    # RAG API
    rag_api_url: str = "http://localhost:8000"
    
    # Redis (Optional)
    redis_url: Optional[str] = None
    
    # Application
    app_name: str = "Medical Gait RAG WebUI"
    app_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    """Get cached settings."""
    return Settings()
