"""
Jina Embeddings Service Implementation
"""

import torch
import numpy as np
from typing import List, Optional
import logging
import os
from transformers import AutoModel
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..domain.services import EmbeddingService

logger = logging.getLogger(__name__)


class JinaEmbeddingService(EmbeddingService):
    """Jina v4 embedding service implementation"""
    
    def __init__(  # API 체크완료: Jina embedding service init parameters correct
        self,
        model_name: str = "jinaai/jina-embeddings-v4",
        device: Optional[str] = None,
        batch_size: int = 8,
        max_length: int = 8192
    ):
        """
        Initialize Jina embedding service
        
        Args:
            model_name: HuggingFace model name
            device: Compute device (cuda:0, cuda:1, cpu, etc.)
            batch_size: Batch size for processing
            max_length: Maximum sequence length
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        
        # Set device
        if device:
            self.device = device
        else:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        # Initialize model
        self._initialize_model()
        
        # Thread pool for CPU-bound operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info(f"Jina embedding service initialized on {self.device}")
    
    def _initialize_model(self) -> None:
        """Initialize the embedding model"""
        logger.info(f"Loading Jina model: {self.model_name}")
        
        # Debug GPU availability
        import sys
        logger.info(f"Python executable: {sys.executable}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"CUDA device count: {torch.cuda.device_count()}")
            logger.info(f"Current CUDA device: {torch.cuda.current_device()}")
        else:
            logger.info(f"PyTorch version: {torch.__version__}")
            logger.info(f"CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'Not set')}")
        logger.info(f"Requested device: {self.device}")
        
        # Determine dtype based on device
        dtype = torch.float16 if self.device and "cuda" in self.device else torch.float32
        
        # Load model with trust_remote_code for Jina models
        # API 체크완료: AutoModel.from_pretrained() with trust_remote_code=True correct for Jina
        # Disable bitsandbytes quantization
        self.model = AutoModel.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=dtype,
            load_in_8bit=False,  # Explicitly disable 8-bit quantization
            load_in_4bit=False   # Explicitly disable 4-bit quantization
        )
        
        # Move to device
        if self.device and "cuda" in self.device:
            # Check if CUDA is really available
            if torch.cuda.is_available():
                # Use the specified device directly
                self.model = self.model.to(self.device)
                logger.info(f"Model moved to {self.device}")
            else:
                logger.warning(f"CUDA requested but not available, falling back to CPU")
                self.model = self.model.to("cpu")
        else:
            self.model = self.model.to("cpu")
            logger.info("Model running on CPU")
        
        self.model.eval()
        
        # Get embedding dimension
        self.dimension = 2048  # API 체크완료: Jina v4 uses 2048 dimensions correct
        
        logger.info(f"Model loaded successfully, dimension: {self.dimension}")
    
    async def embed_document(self, text: str) -> np.ndarray:
        """Generate embedding for document text"""
        return await self._embed_text(text, task_type="passage")  # API 체크완료: task_type="passage" for documents correct
    
    async def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for search query"""
        return await self._embed_text(query, task_type="query")  # API 체크완료: task_type="query" for queries correct
    
    async def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        # Process in batches
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = await self._embed_batch_texts(batch, task_type="passage")
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    async def _embed_text(self, text: str, task_type: str = "passage") -> np.ndarray:
        """Internal method to embed single text"""
        loop = asyncio.get_event_loop()
        
        def _encode():
            with torch.no_grad():
                # Use Jina's encode_text method
                embeddings = self.model.encode_text(
                    texts=[text],
                    task="retrieval",
                    prompt_name=task_type
                )
                
                # Debug logging
                logger.debug(f"encode_text output type: {type(embeddings)}")
                logger.debug(f"encode_text output: {embeddings if not torch.is_tensor(embeddings) else f'Tensor shape={embeddings.shape}, device={embeddings.device}'}")
                
                try:
                    # Check if it's a list containing tensors (Jina v4 returns list)
                    if isinstance(embeddings, list):
                        # Convert first tensor in the list to numpy
                        if len(embeddings) > 0 and torch.is_tensor(embeddings[0]):
                            result = embeddings[0].detach().cpu().numpy()
                        else:
                            result = np.array(embeddings[0])
                    elif torch.is_tensor(embeddings):
                        # Make sure it's on CPU and detached
                        result = embeddings.detach().cpu().numpy()
                    elif hasattr(embeddings, '__array__'):
                        # It might already be numpy-like
                        result = np.array(embeddings)
                    else:
                        # Last resort - try to convert directly
                        result = np.array(embeddings)
                    
                    # Ensure float32 and get first element if batch
                    result = result.astype(np.float32)
                    if len(result.shape) > 1 and result.shape[0] == 1:
                        return result[0]
                    return result
                    
                except Exception as e:
                    logger.error(f"Failed to convert embeddings: {e}")
                    logger.error(f"Embeddings type: {type(embeddings)}")
                    logger.error(f"Embeddings attributes: {dir(embeddings)}")
                    raise
        
        # Run in thread pool to avoid blocking
        embedding = await loop.run_in_executor(self.executor, _encode)
        return embedding
    
    async def _embed_batch_texts(
        self, 
        texts: List[str], 
        task_type: str = "passage"
    ) -> List[np.ndarray]:
        """Internal method to embed multiple texts"""
        loop = asyncio.get_event_loop()
        
        def _encode():
            with torch.no_grad():
                # Use Jina's encode_text method for batch
                embeddings = self.model.encode_text(
                    texts=texts,
                    task="retrieval",
                    prompt_name=task_type
                )
                
                try:
                    # Check if it's a list containing tensors (Jina v4 returns list)
                    if isinstance(embeddings, list):
                        # Convert each tensor in the list to numpy
                        result = []
                        for emb in embeddings:
                            if torch.is_tensor(emb):
                                result.append(emb.detach().cpu().numpy())
                            else:
                                result.append(np.array(emb))
                        result = np.array(result)
                    elif torch.is_tensor(embeddings):
                        # Make sure it's on CPU and detached
                        result = embeddings.detach().cpu().numpy()
                    elif hasattr(embeddings, '__array__'):
                        # It might already be numpy-like
                        result = np.array(embeddings)
                    else:
                        # Last resort - try to convert directly
                        result = np.array(embeddings)
                    
                    # Ensure float32
                    return result.astype(np.float32)
                    
                except Exception as e:
                    logger.error(f"Failed to convert batch embeddings: {e}")
                    logger.error(f"Embeddings type: {type(embeddings)}")
                    raise
        
        # Run in thread pool
        embeddings = await loop.run_in_executor(self.executor, _encode)
        return [embedding for embedding in embeddings]
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)