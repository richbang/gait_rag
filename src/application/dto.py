"""
Application DTOs - Data Transfer Objects
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.entities import SearchResult, DocumentType, DiseaseCategory


@dataclass
class IndexDocumentRequest:
    """Request for indexing a document"""
    file_path: str
    force_reindex: bool = False


@dataclass
class IndexDocumentResponse:
    """Response from indexing a document"""
    success: bool
    document_id: str
    chunks_created: int
    message: str
    tables_found: int = 0
    pages_processed: int = 0
    processing_time: float = 0.0
    error: Optional[str] = None


@dataclass
class SearchRequest:
    """Request for searching documents"""
    query: str
    limit: int = 5
    document_types: Optional[List[DocumentType]] = None
    disease_categories: Optional[List[DiseaseCategory]] = None
    require_gait_params: bool = False
    paper_ids: Optional[List[str]] = None
    min_score: float = 0.0


@dataclass
class SearchResponse:
    """Response from searching documents"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: Optional[float] = None
    error: Optional[str] = None


@dataclass
class StatisticsResponse:
    """Response containing system statistics"""
    total_documents: int
    total_chunks: int
    text_chunks: int
    table_chunks: int
    chunks_with_gait_params: int
    documents: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class IndexDirectoryRequest:
    """Request for indexing a directory"""
    directory_path: str
    max_files: Optional[int] = None
    recursive: bool = True
    force_reindex: bool = False


@dataclass
class IndexDirectoryResponse:
    """Response from indexing a directory"""
    total_files: int
    success_count: int
    failed_count: int
    total_chunks_created: int
    failed_files: List[str]
    message: str
    processing_time: Optional[float] = None