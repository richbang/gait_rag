"""
Domain Layer Tests
"""

import pytest
from datetime import datetime

from src.domain.entities import (
    Document, DocumentChunk, SearchResult, GaitParameter,
    DocumentType, DiseaseCategory, SearchQuery
)
from src.domain.value_objects import PaperId, ChunkId, PageNumber, Score


class TestGaitParameter:
    """Test GaitParameter entity"""
    
    def test_create_gait_parameter(self):
        param = GaitParameter(
            name="walking_speed",
            value=1.2,
            unit="m/s",
            confidence=0.9
        )
        assert param.name == "walking_speed"
        assert param.value == 1.2
        assert param.unit == "m/s"
        assert param.confidence == 0.9
    
    def test_invalid_confidence(self):
        with pytest.raises(ValueError):
            GaitParameter(
                name="speed",
                value=1.0,
                confidence=1.5  # Invalid confidence > 1
            )


class TestDocumentChunk:
    """Test DocumentChunk entity"""
    
    def test_create_chunk(self):
        chunk = DocumentChunk(
            chunk_id="paper1::chunk_0",
            document_id="paper1",
            content="This is test content",
            page_number=1,
            chunk_index=0,
            chunk_type=DocumentType.TEXT
        )
        
        assert chunk.chunk_id == "paper1::chunk_0"
        assert chunk.document_id == "paper1"
        assert chunk.get_word_count() == 4
        assert not chunk.has_gait_parameters()
    
    def test_chunk_with_gait_params(self):
        param = GaitParameter(name="speed", value=1.2, unit="m/s")
        
        chunk = DocumentChunk(
            chunk_id="paper1::chunk_0",
            document_id="paper1", 
            content="Walking speed was 1.2 m/s",
            page_number=1,
            chunk_index=0,
            chunk_type=DocumentType.TEXT,
            gait_parameters=[param]
        )
        
        assert chunk.has_gait_parameters()
        assert len(chunk.gait_parameters) == 1


class TestDocument:
    """Test Document entity"""
    
    def test_create_document(self):
        chunks = [
            DocumentChunk(
                chunk_id="paper1::chunk_0",
                document_id="paper1",
                content="Text chunk",
                page_number=1,
                chunk_index=0,
                chunk_type=DocumentType.TEXT
            ),
            DocumentChunk(
                chunk_id="paper1::chunk_1", 
                document_id="paper1",
                content="Table data",
                page_number=2,
                chunk_index=1,
                chunk_type=DocumentType.TABLE
            )
        ]
        
        doc = Document(
            document_id="paper1",
            filename="paper1.pdf",
            title="Test Paper",
            authors=["Author1", "Author2"],
            publication_year=2024,
            disease_category=DiseaseCategory.STROKE,
            chunks=chunks,
            total_pages=10
        )
        
        assert doc.get_chunk_count() == 2
        assert len(doc.get_text_chunks()) == 1
        assert len(doc.get_table_chunks()) == 1
        assert len(doc.get_chunks_with_gait_params()) == 0


class TestValueObjects:
    """Test value objects"""
    
    def test_paper_id(self):
        paper_id = PaperId("test_paper_123")
        assert str(paper_id) == "test_paper_123"
        
        with pytest.raises(ValueError):
            PaperId("")  # Empty string
    
    def test_chunk_id(self):
        chunk_id = ChunkId("paper1", 5)
        assert str(chunk_id) == "paper1::chunk_5"
        
        # Test from_string
        parsed = ChunkId.from_string("paper1::chunk_5")
        assert parsed.paper_id == "paper1"
        assert parsed.chunk_index == 5
        
        with pytest.raises(ValueError):
            ChunkId.from_string("invalid_format")
    
    def test_page_number(self):
        page = PageNumber(1)
        assert int(page) == 1
        assert str(page) == "1"
        
        with pytest.raises(ValueError):
            PageNumber(0)  # Must be positive
    
    def test_score(self):
        score = Score(0.85)
        assert float(score) == 0.85
        assert score.is_above_threshold(0.8)
        assert not score.is_above_threshold(0.9)
        
        with pytest.raises(ValueError):
            Score(1.5)  # Must be <= 1


class TestSearchQuery:
    """Test SearchQuery entity"""
    
    def test_create_search_query(self):
        query = SearchQuery(
            query_text="walking speed in stroke patients",
            limit=10,
            document_types=[DocumentType.TEXT],
            disease_categories=[DiseaseCategory.STROKE],
            require_gait_params=True,
            min_score=0.7
        )
        
        assert query.query_text == "walking speed in stroke patients"
        assert query.limit == 10
        assert query.require_gait_params
    
    def test_invalid_limit(self):
        with pytest.raises(ValueError):
            SearchQuery(
                query_text="test",
                limit=0  # Must be positive
            )
    
    def test_invalid_min_score(self):
        with pytest.raises(ValueError):
            SearchQuery(
                query_text="test",
                min_score=1.5  # Must be <= 1
            )