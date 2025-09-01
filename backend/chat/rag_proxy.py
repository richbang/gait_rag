"""RAG API proxy service."""

import httpx
from typing import Optional, Dict, Any, List
from loguru import logger
from core.config import get_settings

settings = get_settings()


class RAGProxyService:
    """Proxy service for RAG API."""
    
    def __init__(self):
        """Initialize RAG proxy service."""
        self.rag_api_url = "http://localhost:8001"  # RAG API on port 8001
        self.vllm_url = "http://localhost:8000"     # vLLM on port 8000
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def search_documents(
        self,
        query: str,
        limit: int = 5,
        document_types: Optional[List[str]] = None,
        disease_categories: Optional[List[str]] = None,
        min_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Search documents via RAG API.
        
        Args:
            query: Search query
            limit: Maximum number of results
            document_types: Filter by document types
            disease_categories: Filter by disease categories
            min_score: Minimum similarity score
            
        Returns:
            Search results
        """
        try:
            payload = {
                "query": query,
                "limit": limit,
                "min_score": min_score
            }
            
            if document_types:
                payload["document_types"] = document_types
            
            if disease_categories:
                payload["disease_categories"] = disease_categories
            
            response = await self.client.post(
                f"{self.rag_api_url}/search",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"RAG search successful for query: {query[:50]}...")
            return response.json()
            
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            raise
    
    async def question_answer(
        self,
        query: str,
        limit: int = 5,
        use_vllm: bool = True,
        document_types: Optional[List[str]] = None,
        disease_categories: Optional[List[str]] = None,
        min_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Question answering via RAG API with vLLM.
        
        Args:
            query: Question
            limit: Maximum number of source documents
            use_vllm: Whether to use vLLM for answer generation
            document_types: Filter by document types
            disease_categories: Filter by disease categories
            min_score: Minimum similarity score
            
        Returns:
            Answer and sources
        """
        try:
            payload = {
                "query": query,
                "limit": limit,
                "use_vllm": use_vllm,
                "min_score": min_score
            }
            
            if document_types:
                payload["document_types"] = document_types
            
            if disease_categories:
                payload["disease_categories"] = disease_categories
            
            response = await self.client.post(
                f"{self.rag_api_url}/qa",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"RAG QA successful for query: {query[:50]}...")
            return response.json()
            
        except Exception as e:
            logger.error(f"RAG QA error: {e}")
            raise
    
    async def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """
        Get document metadata.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document metadata
        """
        try:
            response = await self.client.get(
                f"{self.rag_api_url}/document/metadata",
                params={"document_id": document_id}
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Get document metadata error: {e}")
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()