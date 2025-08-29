"""
Use Case Tests
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from src.application.use_cases import (
    IndexDocumentUseCase,
    SearchDocumentsUseCase,
    GetStatisticsUseCase,
    IndexDirectoryUseCase
)
from src.application.dto import (
    IndexDocumentRequest,
    SearchRequest,
    IndexDirectoryRequest
)
from src.domain.entities import DocumentType, DiseaseCategory


class TestIndexDocumentUseCase:
    """Test document indexing use case"""
    
    @pytest.mark.asyncio
    async def test_index_document_success(
        self,
        mock_vector_repository,
        mock_embedding_service,
        mock_document_processor,
        temp_dir
    ):
        """Test successful document indexing"""
        # Create test file
        test_file = temp_dir / "test.pdf"
        test_file.touch()
        
        # Create use case
        use_case = IndexDocumentUseCase(
            vector_repo=mock_vector_repository,
            embedding_service=mock_embedding_service,
            document_processor=mock_document_processor
        )
        
        # Execute
        request = IndexDocumentRequest(file_path=str(test_file))
        response = await use_case.execute(request)
        
        # Verify
        assert response.success
        assert response.chunks_created == 1
        mock_document_processor.extract_content.assert_called_once()
        mock_document_processor.create_chunks.assert_called_once()
        mock_embedding_service.embed_batch.assert_called_once()
        mock_vector_repository.index_chunks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_index_document_file_not_found(
        self,
        mock_vector_repository,
        mock_embedding_service,
        mock_document_processor
    ):
        """Test indexing non-existent file"""
        use_case = IndexDocumentUseCase(
            vector_repo=mock_vector_repository,
            embedding_service=mock_embedding_service,
            document_processor=mock_document_processor
        )
        
        request = IndexDocumentRequest(file_path="nonexistent.pdf")
        
        with pytest.raises(FileNotFoundError):
            await use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_index_document_invalid_extension(
        self,
        mock_vector_repository,
        mock_embedding_service,
        mock_document_processor,
        temp_dir
    ):
        """Test indexing non-PDF file"""
        # Create test file with wrong extension
        test_file = temp_dir / "test.txt"
        test_file.touch()
        
        use_case = IndexDocumentUseCase(
            vector_repo=mock_vector_repository,
            embedding_service=mock_embedding_service,
            document_processor=mock_document_processor
        )
        
        request = IndexDocumentRequest(file_path=str(test_file))
        
        with pytest.raises(ValueError):
            await use_case.execute(request)


class TestSearchDocumentsUseCase:
    """Test document search use case"""
    
    @pytest.mark.asyncio
    async def test_search_documents(
        self,
        mock_vector_repository,
        mock_embedding_service
    ):
        """Test document search"""
        use_case = SearchDocumentsUseCase(
            vector_repo=mock_vector_repository,
            embedding_service=mock_embedding_service
        )
        
        request = SearchRequest(
            query="walking speed in stroke patients",
            limit=5,
            document_types=[DocumentType.TEXT],
            disease_categories=[DiseaseCategory.STROKE]
        )
        
        response = await use_case.execute(request)
        
        assert response.query == "walking speed in stroke patients"
        assert response.total_results == 0  # Mock returns empty list
        mock_embedding_service.embed_query.assert_called_once_with(
            "walking speed in stroke patients"
        )
        mock_vector_repository.search.assert_called_once()


class TestGetStatisticsUseCase:
    """Test statistics use case"""
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, mock_vector_repository):
        """Test getting statistics"""
        use_case = GetStatisticsUseCase(vector_repo=mock_vector_repository)
        
        response = await use_case.execute()
        
        assert response.total_documents == 0
        assert response.total_chunks == 0
        mock_vector_repository.get_statistics.assert_called_once()


class TestIndexDirectoryUseCase:
    """Test directory indexing use case"""
    
    @pytest.mark.asyncio
    async def test_index_directory_empty(
        self,
        mock_vector_repository,
        temp_dir
    ):
        """Test indexing empty directory"""
        # Mock the index document use case
        mock_index_use_case = Mock()
        
        use_case = IndexDirectoryUseCase(
            index_document_use_case=mock_index_use_case,
            vector_repo=mock_vector_repository
        )
        
        request = IndexDirectoryRequest(directory_path=str(temp_dir))
        response = await use_case.execute(request)
        
        assert response.total_files == 0
        assert response.success_count == 0
        assert response.failed_count == 0
    
    @pytest.mark.asyncio
    async def test_index_directory_with_pdfs(
        self,
        mock_vector_repository,
        temp_dir
    ):
        """Test indexing directory with PDF files"""
        # Create test PDF files
        (temp_dir / "paper1.pdf").touch()
        (temp_dir / "paper2.pdf").touch()
        (temp_dir / "not_pdf.txt").touch()  # Should be ignored
        
        # Mock the index document use case
        mock_index_use_case = Mock()
        mock_index_use_case.execute = AsyncMock()
        mock_index_use_case.execute.return_value = Mock(
            success=True,
            chunks_created=5
        )
        
        use_case = IndexDirectoryUseCase(
            index_document_use_case=mock_index_use_case,
            vector_repo=mock_vector_repository
        )
        
        request = IndexDirectoryRequest(
            directory_path=str(temp_dir),
            max_files=10
        )
        response = await use_case.execute(request)
        
        assert response.total_files == 2  # Only PDFs counted
        assert response.success_count == 2
        assert response.total_chunks_created == 10  # 2 files × 5 chunks each
    
    @pytest.mark.asyncio
    async def test_index_directory_not_found(
        self,
        mock_vector_repository
    ):
        """Test indexing non-existent directory"""
        mock_index_use_case = Mock()
        
        use_case = IndexDirectoryUseCase(
            index_document_use_case=mock_index_use_case,
            vector_repo=mock_vector_repository
        )
        
        request = IndexDirectoryRequest(directory_path="/nonexistent/path")
        
        with pytest.raises(ValueError):
            await use_case.execute(request)