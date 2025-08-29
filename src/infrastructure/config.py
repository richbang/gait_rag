"""
Configuration Management
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "Medical Gait RAG System"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # ChromaDB
    chroma_collection_name: str = Field(
        default="gait_papers",
        env="CHROMA_COLLECTION_NAME"
    )
    chroma_persist_directory: str = Field(
        default="./storage/chromadb",
        env="CHROMA_PERSIST_DIRECTORY"
    )
    
    # Jina Embeddings
    jina_model_name: str = Field(
        default="jinaai/jina-embeddings-v4",
        env="JINA_MODEL_NAME"
    )
    embedding_device: str = Field(
        default="cuda:5",
        env="EMBEDDING_DEVICE"
    )
    embedding_batch_size: int = Field(
        default=8,
        env="EMBEDDING_BATCH_SIZE"
    )
    
    # Document Processing
    chunk_size: int = Field(
        default=500,
        env="CHUNK_SIZE"
    )
    chunk_overlap: int = Field(
        default=100,
        env="CHUNK_OVERLAP"
    )
    max_pages_per_doc: Optional[int] = Field(
        default=None,
        env="MAX_PAGES_PER_DOC"
    )
    
    # Search
    default_search_limit: int = Field(
        default=5,
        env="DEFAULT_SEARCH_LIMIT"
    )
    min_similarity_score: float = Field(
        default=0.3,
        env="MIN_SIMILARITY_SCORE"
    )
    
    # API Server
    api_host: str = Field(
        default="0.0.0.0",
        env="API_HOST"
    )
    api_port: int = Field(
        default=8000,
        env="API_PORT"
    )
    api_workers: int = Field(
        default=1,
        env="API_WORKERS"
    )
    cors_origins: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )
    
    # Paths
    data_directory: str = Field(
        default="./data",
        env="DATA_DIRECTORY"
    )
    extracted_texts_dir: str = Field(
        default="./data/extracted_texts",
        env="EXTRACTED_TEXTS_DIR"
    )
    results_directory: str = Field(
        default="./results",
        env="RESULTS_DIRECTORY"
    )
    
    # vLLM Server Configuration (for answer generation)
    use_vllm: bool = Field(
        default=False,
        env="USE_VLLM"
    )
    vllm_api_url: str = Field(
        default="http://localhost:8000/v1",
        env="VLLM_API_URL"
    )
    vllm_model: str = Field(
        default="Seed-OSS-36B-Instruct-AWQ",
        env="VLLM_MODEL"
    )
    vllm_max_tokens: int = Field(
        default=4096,
        env="VLLM_MAX_TOKENS"
    )
    vllm_temperature: float = Field(
        default=0.1,
        env="VLLM_TEMPERATURE"
    )
    vllm_context_length: int = Field(
        default=128000,
        env="VLLM_CONTEXT_LENGTH"
    )
    
    
    # Logging
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL"
    )
    log_file: Optional[str] = Field(
        default=None,
        env="LOG_FILE"
    )
    
    # GPU Configuration
    cuda_visible_devices: Optional[str] = Field(
        default=None,
        env="CUDA_VISIBLE_DEVICES"
    )
    vllm_cuda_visible_devices: Optional[str] = Field(
        default=None,
        env="VLLM_CUDA_VISIBLE_DEVICES"
    )
    vllm_tensor_parallel_size: int = Field(
        default=2,
        env="VLLM_TENSOR_PARALLEL_SIZE"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_data_path(self) -> Path:
        """Get data directory path"""
        return Path(self.data_directory)
    
    def get_chroma_path(self) -> Path:
        """Get ChromaDB storage path"""
        return Path(self.chroma_persist_directory)
    
    def get_results_path(self) -> Path:
        """Get results directory path"""
        path = Path(self.results_directory)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def setup_gpu(self) -> None:
        """Setup GPU configuration"""
        if self.cuda_visible_devices:
            os.environ["CUDA_VISIBLE_DEVICES"] = self.cuda_visible_devices
            
    def get_device(self) -> str:
        """Get compute device based on configuration"""
        import torch
        
        if self.embedding_device == "auto":
            return "cuda:0" if torch.cuda.is_available() else "cpu"
        return self.embedding_device


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    settings.setup_gpu()
    return settings