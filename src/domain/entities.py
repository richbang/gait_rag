"""
Domain Entities - Core business objects
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    """Document content type enumeration"""
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    MIXED = "mixed"


class DiseaseCategory(Enum):
    """Medical condition categories for gait analysis"""
    STROKE = "stroke"
    PARKINSON = "parkinson"
    ARTHRITIS = "arthritis"
    SCOLIOSIS = "scoliosis"
    OTHER = "other"


@dataclass(frozen=True)
class GaitParameter:
    """Gait analysis parameter entity"""
    name: str
    value: float
    unit: Optional[str] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    confidence: Optional[float] = None
    
    def __post_init__(self):
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")


@dataclass
class DocumentChunk:
    """Document chunk entity representing a segment of content"""
    chunk_id: str
    document_id: str
    content: str
    page_number: int
    chunk_index: int
    chunk_type: DocumentType
    metadata: Dict[str, Any] = field(default_factory=dict)
    gait_parameters: List[GaitParameter] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    
    def has_gait_parameters(self) -> bool:
        """Check if chunk contains gait parameters"""
        return len(self.gait_parameters) > 0
    
    def get_word_count(self) -> int:
        """Get word count of the content"""
        return len(self.content.split())


@dataclass
class Document:
    """Document entity representing a research paper"""
    document_id: str
    filename: str
    title: Optional[str]
    authors: List[str]
    publication_year: Optional[int]
    disease_category: DiseaseCategory
    chunks: List[DocumentChunk]
    total_pages: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    indexed_at: Optional[datetime] = None
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks"""
        return len(self.chunks)
    
    def get_text_chunks(self) -> List[DocumentChunk]:
        """Get only text type chunks"""
        return [c for c in self.chunks if c.chunk_type == DocumentType.TEXT]
    
    def get_table_chunks(self) -> List[DocumentChunk]:
        """Get only table type chunks"""
        return [c for c in self.chunks if c.chunk_type == DocumentType.TABLE]
    
    def get_chunks_with_gait_params(self) -> List[DocumentChunk]:
        """Get chunks containing gait parameters"""
        return [c for c in self.chunks if c.has_gait_parameters()]


@dataclass
class SearchResult:
    """Search result entity"""
    chunk: DocumentChunk
    score: float
    document_metadata: Dict[str, Any]
    highlights: Optional[List[str]] = None
    
    def __post_init__(self):
        if not 0 <= self.score <= 1:
            raise ValueError("Score must be between 0 and 1")


@dataclass
class SearchQuery:
    """Search query entity with filtering options"""
    query_text: str
    limit: int = 5
    document_types: Optional[List[DocumentType]] = None
    disease_categories: Optional[List[DiseaseCategory]] = None
    require_gait_params: bool = False
    paper_ids: Optional[List[str]] = None
    min_score: float = 0.0
    
    def __post_init__(self):
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if not 0 <= self.min_score <= 1:
            raise ValueError("Min score must be between 0 and 1")