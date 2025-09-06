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
    
    async def direct_llm_query(
        self,
        query: str,
        use_vllm: bool = True
    ) -> Dict[str, Any]:
        """
        Direct LLM query without document search (for normal chat mode).
        
        Args:
            query: User question
            use_vllm: Whether to use vLLM
            
        Returns:
            Answer without sources
        """
        try:
            # Direct LLM call without search
            payload = {
                "query": query,
                "limit": 1,  # Minimum limit to avoid error (will be ignored in direct mode)
                "use_vllm": use_vllm,
                "direct_mode": True  # Flag for direct mode
            }
            
            response = await self.client.post(
                f"{self.rag_api_url}/qa",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Clean thinking tags from response
            answer = result.get("answer", "")
            answer = self._clean_thinking_tags(answer)
            
            logger.info(f"Direct LLM query successful for: {query[:50]}...")
            return {"answer": answer, "sources": []}
            
        except Exception as e:
            logger.error(f"Direct LLM query error: {e}")
            # Fallback to simple response
            return {"answer": "죄송합니다. 응답을 생성할 수 없습니다.", "sources": []}
    
    def _clean_thinking_tags(self, text: str) -> str:
        """Remove thinking tags and other artifacts from LLM response."""
        import re
        
        # Nemotron sometimes generates content before </think> tag
        # Pattern: "answer\n</think>\n\nanswer" (duplicated answer)
        if '</think>' in text:
            # Find content before </think> and remove it along with the tag
            parts = text.split('</think>')
            if len(parts) == 2:
                # Keep only the content after </think>
                cleaned = parts[1].strip()
            else:
                cleaned = text
        else:
            cleaned = text
        
        # Remove Seed-OSS model specific thinking tags - multiple possible formats
        # Format 0: <:think> (actual format used by the model!)
        cleaned = re.sub(r'<:think>', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'</:think>', '', cleaned, flags=re.IGNORECASE)
        
        # Format 1: /seed:thinking ... /seed
        cleaned = re.sub(r'/seed:thinking.*?/seed', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'/seed:think.*?/seed', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Format 2: <seed:thinking> ... </seed:thinking>
        cleaned = re.sub(r'<seed:thinking>.*?</seed:thinking>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<seed:think>.*?</seed:think>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Format 3: <|thinking|> ... <|/thinking|> (some models use this)
        cleaned = re.sub(r'<\|thinking\|>.*?<\|/thinking\|>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<\|think\|>.*?<\|/think\|>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Format 4: [thinking] ... [/thinking]
        cleaned = re.sub(r'\[thinking\].*?\[/thinking\]', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'\[think\].*?\[/think\]', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove XML-style thinking tags if present
        cleaned = re.sub(r'<\w+:think(?:ing)?>.*?</\w+:think(?:ing)?>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<think(?:ing)?>.*?</think(?:ing)?>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove any remaining tags
        cleaned = re.sub(r'</?\w+:think(?:ing)?>', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'</?think(?:ing)?>', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'/seed:?(?:think|thinking)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'/seed', '', cleaned, flags=re.IGNORECASE)
        
        # For Seed-OSS model: Don't over-filter if thinking tags were already removed
        # Only apply language-based filtering if no tags were found
        tags_found = any([
            '/seed' in text.lower(),
            'thinking' in text.lower() and ('>' in text or '<' in text),
            '[thinking]' in text.lower()
        ])
        
        # If tags were found and removed, trust the remaining content
        if not tags_found and len(cleaned) > 500:
            # Strategy 1: Look for Korean content that seems complete
            # But don't be too aggressive - preserve the full answer
            pass  # Skip aggressive filtering
        
        # Also check for <:think> tag specifically
        if '<:think>' in text.lower():
            tags_found = True
            
        # Remove obvious English thinking patterns if not using tags
        if not tags_found:
            # Remove common English thinking patterns
            if "Got it" in cleaned or "Let me" in cleaned or "I need to" in cleaned:
                # Find the last Korean paragraph
                korean_start = cleaned.rfind('\n\n')
                if korean_start > 0 and '가-힣' in cleaned[korean_start:]:
                    cleaned = cleaned[korean_start:].strip()
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        # Remove duplicate responses (Nemotron sometimes repeats the answer)
        lines = cleaned.split('\n\n')
        if len(lines) >= 2:
            # Check if consecutive paragraphs are identical
            unique_lines = []
            prev_line = None
            for line in lines:
                if line != prev_line:
                    unique_lines.append(line)
                    prev_line = line
            cleaned = '\n\n'.join(unique_lines)
        
        return cleaned
    
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
            
            result = response.json()
            
            # Log raw answer for debugging thinking tags
            if "answer" in result:
                logger.debug(f"RAW ANSWER (first 500 chars): {result['answer'][:500]}")
                result["answer"] = self._clean_thinking_tags(result["answer"])
                logger.debug(f"CLEANED ANSWER (first 500 chars): {result['answer'][:500]}")
            
            logger.info(f"RAG QA successful for query: {query[:50]}...")
            return result
            
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