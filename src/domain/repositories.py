"""
Domain Repository Interfaces - Abstraction for data access
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import Document, DocumentChunk, SearchResult, SearchQuery
from .value_objects import PaperId, ChunkId


class DocumentRepository(ABC):
    """Abstract repository for document persistence"""
    
    @abstractmethod
    async def save(self, document: Document) -> None:
        """Save a document"""
        pass
    
    @abstractmethod
    async def find_by_id(self, document_id: PaperId) -> Optional[Document]:
        """Find document by ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Document]:
        """Find all documents"""
        pass
    
    @abstractmethod
    async def delete(self, document_id: PaperId) -> bool:
        """Delete a document"""
        pass
    
    @abstractmethod
    async def exists(self, document_id: PaperId) -> bool:
        """Check if document exists"""
        pass


class VectorRepository(ABC):
    """Abstract repository for vector storage"""
    
    @abstractmethod
    async def index_chunk(self, chunk: DocumentChunk) -> None:
        """Index a single chunk with embedding"""
        pass
    
    @abstractmethod
    async def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Batch index multiple chunks"""
        pass
    
    @abstractmethod
    async def search(self, query: SearchQuery, query_embedding: List[float]) -> List[SearchResult]:
        """Search for similar chunks"""
        pass
    
    @abstractmethod
    async def delete_by_document(self, document_id: PaperId) -> int:
        """Delete all chunks for a document"""
        pass
    
    @abstractmethod
    async def get_chunk(self, chunk_id: ChunkId) -> Optional[DocumentChunk]:
        """Get a specific chunk by ID"""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics"""
        pass
    
    @abstractmethod
    async def clear_all(self) -> None:
        """Clear all data from repository"""
        pass