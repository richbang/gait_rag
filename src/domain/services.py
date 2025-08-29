"""
Domain Services - Business logic that doesn't fit in entities
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from .entities import Document, DocumentChunk, GaitParameter


class EmbeddingService(ABC):
    """Abstract service for generating embeddings"""
    
    @abstractmethod
    async def embed_document(self, text: str) -> np.ndarray:
        """Generate embedding for document text"""
        pass
    
    @abstractmethod
    async def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for search query"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass


class DocumentProcessorService(ABC):
    """Abstract service for processing documents"""
    
    @abstractmethod
    async def extract_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from document file"""
        pass
    
    @abstractmethod
    async def create_chunks(
        self, 
        content: Dict[str, Any], 
        chunk_size: int = 500,
        overlap: int = 100
    ) -> List[DocumentChunk]:
        """Create chunks from extracted content"""
        pass
    
    @abstractmethod
    async def extract_gait_parameters(self, text: str) -> List[GaitParameter]:
        """Extract gait parameters from text"""
        pass
    
    @abstractmethod
    async def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from document"""
        pass


class ChunkingStrategy(ABC):
    """Abstract strategy for chunking documents"""
    
    @abstractmethod
    def chunk(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Chunk text according to strategy"""
        pass


class SemanticChunking(ChunkingStrategy):
    """Semantic-based chunking strategy"""
    
    def chunk(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Chunk text based on semantic boundaries"""
        # Implementation would use sentence boundaries, paragraphs, etc.
        pass


class FixedSizeChunking(ChunkingStrategy):
    """Fixed-size chunking strategy"""
    
    def chunk(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Chunk text into fixed-size windows"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks