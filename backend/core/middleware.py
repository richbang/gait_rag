"""Middleware components for the application."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
from typing import Callable


# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


class ErrorHandlingMiddleware:
    """Global error handling middleware."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}")
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
            await response(scope, receive, send)


class RequestLoggingMiddleware:
    """Request/Response logging middleware."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                logger.info(
                    f"{scope['method']} {scope['path']} "
                    f"- {message['status']} - {duration:.3f}s"
                )
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after": 60
        }
    )
    response.headers["Retry-After"] = "60"
    return response


class APIResponse:
    """Unified API response format."""
    
    @staticmethod
    def success(data=None, message: str = "Success", meta: dict = None):
        """Create success response."""
        response = {
            "status": "success",
            "message": message,
            "data": data
        }
        if meta:
            response["meta"] = meta
        return response
    
    @staticmethod
    def error(message: str = "Error", code: int = 400, details: dict = None):
        """Create error response."""
        response = {
            "status": "error",
            "message": message,
            "code": code
        }
        if details:
            response["details"] = details
        return response
    
    @staticmethod
    def paginated(
        data: list,
        page: int,
        per_page: int,
        total: int,
        message: str = "Success"
    ):
        """Create paginated response."""
        total_pages = (total + per_page - 1) // per_page
        return {
            "status": "success",
            "message": message,
            "data": data,
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }