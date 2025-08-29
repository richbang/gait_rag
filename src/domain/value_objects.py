"""
Domain Value Objects - Immutable domain concepts
"""

from dataclasses import dataclass
from typing import Any
import re


@dataclass(frozen=True)
class PaperId:
    """Paper ID value object"""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Paper ID must be a non-empty string")
        # Remove special characters that might cause issues
        if not re.match(r'^[\w\-_.]+$', self.value):
            raise ValueError("Paper ID contains invalid characters")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ChunkId:
    """Chunk ID value object"""
    paper_id: str
    chunk_index: int
    
    def __post_init__(self):
        if not self.paper_id:
            raise ValueError("Paper ID is required")
        if self.chunk_index < 0:
            raise ValueError("Chunk index must be non-negative")
    
    def __str__(self) -> str:
        return f"{self.paper_id}::chunk_{self.chunk_index}"
    
    @classmethod
    def from_string(cls, chunk_id: str) -> 'ChunkId':
        """Create ChunkId from string format"""
        parts = chunk_id.split('::chunk_')
        if len(parts) != 2:
            raise ValueError(f"Invalid chunk ID format: {chunk_id}")
        return cls(paper_id=parts[0], chunk_index=int(parts[1]))


@dataclass(frozen=True)
class PageNumber:
    """Page number value object"""
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Page number must be positive")
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True)
class Score:
    """Similarity score value object"""
    value: float
    
    def __post_init__(self):
        if not 0 <= self.value <= 1:
            raise ValueError("Score must be between 0 and 1")
    
    def __float__(self) -> float:
        return self.value
    
    def __str__(self) -> str:
        return f"{self.value:.4f}"
    
    def is_above_threshold(self, threshold: float) -> bool:
        """Check if score is above given threshold"""
        return self.value >= threshold


@dataclass(frozen=True)
class Embedding:
    """Embedding vector value object"""
    vector: tuple  # Using tuple for immutability
    dimension: int
    
    def __post_init__(self):
        if len(self.vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(self.vector)}")
    
    def to_list(self) -> list:
        """Convert to list for serialization"""
        return list(self.vector)
    
    @classmethod
    def from_list(cls, vector: list, expected_dim: int = 2048) -> 'Embedding':
        """Create embedding from list"""
        return cls(vector=tuple(vector), dimension=expected_dim)