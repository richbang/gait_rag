"""
vLLM Client for Answer Generation
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)


class VLLMClient:
    """Client for vLLM server interaction"""
    
    def __init__(
        self,
        api_url: str = "http://localhost:8000/v1",
        model: str = "Seed-OSS-36B-Instruct-AWQ",
        max_tokens: int = 4096,
        temperature: float = 0.1,
        timeout: int = 60
    ):
        """
        Initialize vLLM client
        
        Args:
            api_url: vLLM server endpoint
            model: Model name as served by vLLM
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        
        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(timeout=timeout)
        
        logger.info(f"vLLM client initialized for {api_url} with model {model}")
    
    async def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate answer using vLLM
        
        Args:
            prompt: User query/prompt
            context: Retrieved context from RAG
            system_prompt: System instructions
            
        Returns:
            Generated text response
        """
        # Construct full prompt
        full_prompt = self._construct_prompt(prompt, context, system_prompt)
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        try:
            # Send request to vLLM server
            response = await self.client.post(
                f"{self.api_url}/completions",
                json=payload
            )
            response.raise_for_status()
            
            # Extract generated text
            result = response.json()
            generated_text = result["choices"][0]["text"]
            
            return generated_text.strip()
            
        except httpx.HTTPError as e:
            logger.error(f"vLLM request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in vLLM generation: {e}")
            raise
    
    async def generate_with_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate using chat completion API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": False
        }
        
        try:
            response = await self.client.post(
                f"{self.api_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except httpx.HTTPError as e:
            logger.error(f"vLLM chat request failed: {e}")
            raise
    
    def _construct_prompt(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Construct full prompt with context"""
        
        if system_prompt is None:
            system_prompt = (
                "You are a medical research assistant specializing in gait analysis. "
                "Answer questions based on the provided research paper context. "
                "Be accurate, concise, and cite specific findings when relevant."
            )
        
        if context:
            full_prompt = f"""System: {system_prompt}

Context from research papers:
{context}

Question: {prompt}

Answer: """
        else:
            full_prompt = f"""System: {system_prompt}

Question: {prompt}

Answer: """
        
        return full_prompt
    
    async def health_check(self) -> bool:
        """Check if vLLM server is accessible"""
        try:
            response = await self.client.get(f"{self.api_url}/models")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"vLLM health check failed: {e}")
            return False
    
    async def close(self):
        """Close HTTP client connection"""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()