"""Authentication schemas."""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """User registration schema."""
    
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=100)
    
    @validator("username")
    def validate_username(cls, v):
        """Validate username format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must contain only letters, numbers, hyphens, and underscores")
        return v.lower()


class UserLogin(BaseModel):
    """User login schema."""
    
    username: str
    password: str


class UserResponse(BaseModel):
    """User response schema."""
    
    id: int
    username: str
    full_name: Optional[str]
    department: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response schema."""
    
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    """User update schema."""
    
    full_name: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)