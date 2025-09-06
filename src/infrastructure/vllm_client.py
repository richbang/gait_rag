"""
vLLM Client for Answer Generation with Improved Prompt Engineering
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
        model: str = "nemotron-nano-12b",  # Changed to Nemotron model
        max_tokens: int = 8192,  # Increased for longer responses
        temperature: float = 0.6,  # Nemotron recommended temperature
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
        
        # Log the prompt for debugging
        logger.info("=" * 80)
        logger.info("LLM PROMPT:")
        logger.info("-" * 80)
        logger.info(full_prompt[:2000])  # Log first 2000 chars
        
        # Estimate token count (rough approximation: 1 token ≈ 3-4 characters for Korean/English)
        estimated_tokens = len(full_prompt) // 3
        
        if len(full_prompt) > 2000:
            logger.info(f"... (truncated, total length: {len(full_prompt)} chars, ~{estimated_tokens} tokens)")
        else:
            logger.info(f"Total length: {len(full_prompt)} chars, ~{estimated_tokens} tokens")
        
        # Warn if approaching context limit (assuming 32K context)
        if estimated_tokens > 28000:
            logger.warning(f"⚠️ Approaching context limit! Estimated tokens: {estimated_tokens}/32768")
        elif estimated_tokens > 20000:
            logger.info(f"📊 Context usage: {estimated_tokens}/32768 tokens ({estimated_tokens*100//32768}%)")
        
        logger.info("=" * 80)
        
        # Use regular completions endpoint (Nemotron and Seed-OSS support this)
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False,
            "top_p": 0.95  # Nemotron recommended setting
        }
        
        endpoint = f"{self.api_url}/completions"
        
        try:
            # Send request to vLLM server
            response = await self.client.post(endpoint, json=payload)
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
        """Construct full prompt with context using improved prompt engineering"""
        
        # Default system prompt - simple and clear
        if system_prompt is None:
            system_prompt = "You are a helpful assistant. Respond naturally in Korean."
        
        if context:
            # RAG mode with document context
            if "[이전 대화 내용]" in prompt:
                # Extract conversation history and current question
                parts = prompt.split("[현재 질문]")
                if len(parts) == 2:
                    conversation_part = parts[0].replace("[이전 대화 내용]", "").strip()
                    current_question = parts[1].strip()
                    
                    # Improved prompt template for RAG mode with history
                    full_prompt = f"""You are a medical AI assistant specializing in gait analysis. Answer in Korean.

### Previous conversation:
{conversation_part}

### Reference documents:
{context}

### User question: 
{current_question}

### Assistant response (in Korean):"""
                else:
                    # Fallback for single question with context
                    full_prompt = f"""You are a medical AI assistant specializing in gait analysis. Answer in Korean.

### Reference documents:
{context}

### User question:
{prompt}

### Assistant response (in Korean):"""
            else:
                # Single question with context, no history
                full_prompt = f"""You are a medical AI assistant specializing in gait analysis. Answer in Korean.

### Reference documents:
{context}

### User question:
{prompt}

### Assistant response (in Korean):"""
        else:
            # Direct chat mode without document context
            if "[이전 대화 내용]" in prompt:
                # Extract conversation history and current question
                parts = prompt.split("[현재 질문]")
                if len(parts) == 2:
                    conversation_part = parts[0].replace("[이전 대화 내용]", "").strip()
                    current_question = parts[1].strip()
                    
                    # Simple chat prompt with history
                    full_prompt = f"""You are a helpful assistant. Answer directly in Korean without showing your thinking process.

### Previous conversation:
{conversation_part}

### User: 
{current_question}

### Assistant (answer directly in Korean):"""
                else:
                    full_prompt = f"""You are a helpful assistant. Answer in Korean.

### User:
{prompt}

### Assistant (in Korean):"""
            else:
                full_prompt = f"""You are a helpful assistant. Answer in Korean.

### User:
{prompt}

### Assistant (in Korean):"""
        
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