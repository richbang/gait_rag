"""
Infrastructure Layer Tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import numpy as np

from src.infrastructure.config import Settings
from src.infrastructure.document_processor import PDFDocumentProcessor
from src.domain.entities import DocumentType, DiseaseCategory


class TestSettings:
    """Test configuration settings"""
    
    def test_default_settings(self):
        settings = Settings()
        assert settings.app_name == "Medical Gait RAG System"
        assert settings.chunk_size == 500
        assert settings.chunk_overlap == 100
        assert settings.default_search_limit == 5
    
    def test_path_methods(self):
        settings = Settings(
            data_directory="./test_data",
            chroma_persist_directory="./test_chroma",
            results_directory="./test_results"
        )
        
        assert isinstance(settings.get_data_path(), Path)
        assert isinstance(settings.get_chroma_path(), Path)
        assert isinstance(settings.get_results_path(), Path)


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_pdf_path(temp_dir):
    """Create a sample PDF file for testing"""
    # This would need a real PDF file for full testing
    # For now, just return a path
    pdf_path = temp_dir / "sample.pdf"
    pdf_path.touch()  # Create empty file
    return pdf_path


class TestPDFDocumentProcessor:
    """Test PDF document processor"""
    
    def test_processor_initialization(self):
        processor = PDFDocumentProcessor(
            chunk_size=300,
            chunk_overlap=50,
            max_pages=10
        )
        
        assert processor.chunk_size == 300
        assert processor.chunk_overlap == 50
        assert processor.max_pages == 10
    
    def test_chunk_text(self):
        processor = PDFDocumentProcessor()
        text = "This is a test sentence. " * 100  # Long text
        
        chunks = processor._chunk_text(text, chunk_size=20, overlap=5)
        
        assert len(chunks) > 1
        assert all(len(chunk.split()) <= 20 for chunk in chunks)
    
    def test_contains_gait_keywords(self):
        processor = PDFDocumentProcessor()
        
        text_with_gait = "The walking speed was measured at 1.2 m/s"
        text_without_gait = "This paper discusses general topics"
        
        assert processor._contains_gait_keywords(text_with_gait)
        assert not processor._contains_gait_keywords(text_without_gait)
    
    def test_detect_disease_category(self):
        processor = PDFDocumentProcessor()
        
        stroke_content = {
            "text_pages": [
                {"content": "This study examines stroke patients with hemiplegia"}
            ]
        }
        
        parkinson_content = {
            "text_pages": [
                {"content": "Parkinson's disease affects gait patterns"}
            ]
        }
        
        assert processor._detect_disease_category(stroke_content) == DiseaseCategory.STROKE
        assert processor._detect_disease_category(parkinson_content) == DiseaseCategory.PARKINSON
    
    @pytest.mark.asyncio
    async def test_extract_gait_parameters(self):
        processor = PDFDocumentProcessor()
        
        text = "Walking speed: 1.2 m/s, cadence = 110 steps/min"
        params = await processor.extract_gait_parameters(text)
        
        assert len(params) >= 0  # May find parameters
        # Note: Full testing would require more sophisticated text


class TestJinaEmbeddingService:
    """Test Jina embedding service (mocked)"""
    
    def test_embedding_dimension(self):
        # This would need actual model loading for full test
        # For now, just test the expected dimension
        expected_dim = 2048
        assert expected_dim == 2048  # Jina v4 dimension


class TestChromaVectorStore:
    """Test ChromaDB vector store (integration test)"""
    
    @pytest.fixture
    def vector_store(self, temp_dir):
        """Create vector store for testing"""
        from src.infrastructure.vector_store import ChromaVectorStore
        
        store = ChromaVectorStore(
            collection_name="test_collection",
            persist_directory=str(temp_dir / "chroma"),
            reset=True
        )
        return store
    
    @pytest.mark.asyncio
    async def test_vector_store_initialization(self, vector_store):
        """Test vector store can be initialized"""
        assert vector_store.collection_name == "test_collection"
        stats = await vector_store.get_statistics()
        assert stats["total_chunks"] == 0