"""
PyTest Configuration and Fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from src.infrastructure.config import Settings
from src.container import Container
from src.domain.entities import DocumentChunk, DocumentType, GaitParameter


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def test_settings(temp_dir):
    """Create test settings"""
    return Settings(
        chroma_collection_name="test_collection",
        chroma_persist_directory=str(temp_dir / "chroma"),
        data_directory=str(temp_dir / "data"),
        results_directory=str(temp_dir / "results"),
        embedding_device="cpu",  # Use CPU for tests
        debug=True,
        log_level="DEBUG"
    )


@pytest.fixture
def mock_embedding_service():
    """Create mock embedding service"""
    service = Mock()
    service.embed_document = AsyncMock(return_value=np.random.rand(2048))
    service.embed_query = AsyncMock(return_value=np.random.rand(2048))
    service.embed_batch = AsyncMock(return_value=[np.random.rand(2048)])
    service.get_dimension = Mock(return_value=2048)
    return service


@pytest.fixture
def mock_document_processor():
    """Create mock document processor"""
    processor = Mock()
    
    # Mock extract_content
    processor.extract_content = AsyncMock(return_value={
        "text_pages": [
            {"page_number": 1, "content": "Sample text content"}
        ],
        "tables": [],
        "metadata": {
            "filename": "test.pdf",
            "total_pages": 1,
            "disease_category": "stroke"
        }
    })
    
    # Mock create_chunks
    processor.create_chunks = AsyncMock(return_value=[
        DocumentChunk(
            chunk_id="test::chunk_0",
            document_id="test",
            content="Sample text content",
            page_number=1,
            chunk_index=0,
            chunk_type=DocumentType.TEXT
        )
    ])
    
    return processor


@pytest.fixture
def mock_vector_repository():
    """Create mock vector repository"""
    repo = Mock()
    repo.index_chunk = AsyncMock()
    repo.index_chunks = AsyncMock()
    repo.search = AsyncMock(return_value=[])
    repo.get_statistics = AsyncMock(return_value={
        "total_chunks": 0,
        "total_documents": 0,
        "text_chunks": 0,
        "table_chunks": 0,
        "chunks_with_gait_params": 0,
        "documents": []
    })
    repo.delete_by_document = AsyncMock(return_value=0)
    repo.clear_all = AsyncMock()
    return repo


@pytest.fixture
def sample_document_chunk():
    """Create sample document chunk"""
    return DocumentChunk(
        chunk_id="paper1::chunk_0",
        document_id="paper1",
        content="Walking speed was measured at 1.2 m/s in stroke patients.",
        page_number=1,
        chunk_index=0,
        chunk_type=DocumentType.TEXT,
        gait_parameters=[
            GaitParameter(name="walking_speed", value=1.2, unit="m/s")
        ]
    )


@pytest.fixture
def test_container(
    test_settings,
    mock_embedding_service,
    mock_document_processor,
    mock_vector_repository
):
    """Create test container with mocked dependencies"""
    container = Container(test_settings)
    
    # Replace with mocks
    container._embedding_service = mock_embedding_service
    container._document_processor = mock_document_processor
    container._vector_repo = mock_vector_repository
    
    return container