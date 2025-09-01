"""Chat schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConversationCreate(BaseModel):
    """Conversation creation schema."""
    
    title: Optional[str] = Field(None, max_length=255)


class ConversationResponse(BaseModel):
    """Conversation response schema."""
    
    id: int
    user_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Message creation schema."""
    
    content: str = Field(..., min_length=1)
    use_vllm: bool = Field(default=True)
    search_limit: int = Field(default=5, ge=1, le=20)
    document_types: Optional[List[str]] = None
    disease_categories: Optional[List[str]] = None
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class MessageResponse(BaseModel):
    """Message response schema."""
    
    id: int
    conversation_id: int
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationWithMessages(BaseModel):
    """Conversation with messages schema."""
    
    id: int
    user_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Search request schema."""
    
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    document_types: Optional[List[str]] = None
    disease_categories: Optional[List[str]] = None
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class QARequest(BaseModel):
    """Question-answer request schema."""
    
    query: str = Field(..., min_length=1)
    conversation_id: Optional[int] = None
    use_vllm: bool = Field(default=True)
    limit: int = Field(default=5, ge=1, le=20)
    document_types: Optional[List[str]] = None
    disease_categories: Optional[List[str]] = None
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)