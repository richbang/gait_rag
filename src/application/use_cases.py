"""
Application Use Cases - Business Logic
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from tqdm.asyncio import tqdm

from ..domain.entities import Document, DocumentChunk, SearchQuery, DiseaseCategory
from ..domain.repositories import VectorRepository, DocumentRepository
from ..domain.services import EmbeddingService, DocumentProcessorService
from ..domain.value_objects import PaperId
from .dto import (
    IndexDocumentRequest, IndexDocumentResponse,
    SearchRequest, SearchResponse,
    StatisticsResponse, IndexDirectoryRequest, 
    IndexDirectoryResponse
)

logger = logging.getLogger(__name__)


class IndexDocumentUseCase:
    """Use case for indexing a single document"""
    
    def __init__(
        self,
        vector_repo: VectorRepository,
        embedding_service: EmbeddingService,
        document_processor: DocumentProcessorService
    ):
        self.vector_repo = vector_repo
        self.embedding_service = embedding_service
        self.document_processor = document_processor
    
    async def execute(self, request: IndexDocumentRequest) -> IndexDocumentResponse:
        """Index a single document"""
        start_time = datetime.now()
        file_path = Path(request.file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.suffix.lower() == '.pdf':
            raise ValueError(f"Only PDF files are supported, got: {file_path.suffix}")
        
        try:
            # PDF에서 콘텐츠 추출
            logger.info(f"Processing: {file_path.name}")
            content = await self.document_processor.extract_content(file_path)
            
            # 텍스트를 청크로 분할 (overlap 포함)
            chunks = await self.document_processor.create_chunks(content)
            
            if not chunks:
                logger.warning(f"No chunks extracted from {file_path.name}")
                return IndexDocumentResponse(
                    success=False,
                    document_id="",
                    chunks_created=0,
                    message=f"No content extracted from {file_path.name}"
                )
            
            # 각 청크에 대한 임베딩 생성 (Jina Embeddings v4 사용)
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.embed_batch(texts)
            
            # 청크에 임베딩 벡터 추가
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding.tolist()
            
            # 문서 ID 생성 (data/ 디렉토리 기준 상대 경로 사용)
            # 중복 인덱싱 방지를 위해 파일 경로를 고유 ID로 사용
            file_path_str = str(file_path)
            if "data/" in file_path_str:
                document_id = file_path_str.split("data/", 1)[1]
            else:
                document_id = file_path_str
            
            document = Document(
                document_id=document_id,
                filename=file_path.name,
                title=content["metadata"].get("title"),
                authors=content["metadata"].get("authors", []),
                publication_year=content["metadata"].get("year_hint"),
                disease_category=content["metadata"].get(
                    "disease_category",
                    DiseaseCategory.OTHER
                ),
                chunks=chunks,
                total_pages=content["metadata"]["total_pages"],
                metadata=content["metadata"],
                indexed_at=datetime.now()
            )
            
            # ChromaDB에 청크 인덱싱
            await self.vector_repo.index_chunks(chunks)
            
            # 처리 시간 계산
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Successfully indexed {file_path.name}: "
                f"{len(chunks)} chunks in {processing_time:.2f}s"
            )
            
            return IndexDocumentResponse(
                success=True,
                document_id=document_id,
                chunks_created=len(chunks),
                tables_found=len(content.get("tables", [])),
                pages_processed=len(content.get("text_pages", [])),
                processing_time=processing_time,
                message=f"Successfully indexed {file_path.name}"
            )
            
        except Exception as e:
            logger.error(f"Error indexing {file_path.name}: {str(e)}")
            return IndexDocumentResponse(
                success=False,
                document_id="",
                chunks_created=0,
                message=f"Error indexing {file_path.name}: {str(e)}"
            )


class SearchDocumentsUseCase:
    """Use case for searching documents"""
    
    def __init__(
        self,
        vector_repo: VectorRepository,
        embedding_service: EmbeddingService
    ):
        self.vector_repo = vector_repo
        self.embedding_service = embedding_service
    
    async def execute(self, request: SearchRequest) -> SearchResponse:
        """Search for documents matching query"""
        try:
            # 쿼리를 임베딩으로 변환 (검색용)
            query_embedding = await self.embedding_service.embed_query(request.query)
            
            # 검색 쿼리 엔티티 생성
            search_query = SearchQuery(
                query_text=request.query,
                limit=request.limit,
                document_types=request.document_types,
                disease_categories=request.disease_categories,
                require_gait_params=request.require_gait_params,
                paper_ids=request.paper_ids,
                min_score=request.min_score
            )
            
            # Search in vector store
            results = await self.vector_repo.search(
                search_query,
                query_embedding.tolist()
            )
            
            # Convert to response DTO
            return SearchResponse(
                query=request.query,
                results=results,
                total_results=len(results),
                search_time=(datetime.now()).timestamp()
            )
            
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return SearchResponse(
                query=request.query,
                results=[],
                total_results=0,
                error=str(e)
            )


class GetStatisticsUseCase:
    """Use case for getting system statistics"""
    
    def __init__(self, vector_repo: VectorRepository):
        self.vector_repo = vector_repo
    
    async def execute(self) -> StatisticsResponse:
        """Get system statistics"""
        try:
            stats = await self.vector_repo.get_statistics()
            
            return StatisticsResponse(
                total_documents=stats.get("total_documents", 0),
                total_chunks=stats.get("total_chunks", 0),
                text_chunks=stats.get("text_chunks", 0),
                table_chunks=stats.get("table_chunks", 0),
                chunks_with_gait_params=stats.get("chunks_with_gait_params", 0),
                documents=stats.get("documents", []),
                metadata=stats
            )
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return StatisticsResponse(
                total_documents=0,
                total_chunks=0,
                text_chunks=0,
                table_chunks=0,
                chunks_with_gait_params=0,
                documents=[],
                error=str(e)
            )


class IndexDirectoryUseCase:
    """Use case for indexing all documents in a directory"""
    
    def __init__(
        self,
        index_document_use_case: IndexDocumentUseCase,
        vector_repo: VectorRepository
    ):
        self.index_document_use_case = index_document_use_case
        self.vector_repo = vector_repo
    
    async def execute(self, request: IndexDirectoryRequest) -> IndexDirectoryResponse:
        """Index all PDF files in directory"""
        directory = Path(request.directory_path)
        
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory}")
        
        # Find all PDF files recursively
        pdf_files = list(directory.rglob("*.pdf"))
        
        if request.max_files:
            pdf_files = pdf_files[:request.max_files]
        
        logger.info(f"Found {len(pdf_files)} PDF files to index")
        
        # Track results
        success_count = 0
        failed_count = 0
        total_chunks = 0
        failed_files = []
        
        # Process files with progress bar
        async def process_file(pdf_path: Path):
            nonlocal success_count, failed_count, total_chunks
            
            req = IndexDocumentRequest(file_path=str(pdf_path))
            response = await self.index_document_use_case.execute(req)
            
            if response.success:
                success_count += 1
                total_chunks += response.chunks_created
            else:
                failed_count += 1
                failed_files.append(pdf_path.name)
            
            return response
        
        # Process files concurrently with limit
        semaphore = asyncio.Semaphore(3)  # Limit concurrent processing
        
        async def process_with_limit(pdf_path):
            async with semaphore:
                return await process_file(pdf_path)
        
        # Create tasks with progress bar
        tasks = []
        for pdf_path in pdf_files:
            task = process_with_limit(pdf_path)
            tasks.append(task)
        
        # Execute with progress tracking
        if tasks:
            results = []
            async for result in tqdm(
                asyncio.as_completed(tasks),
                total=len(tasks),
                desc="Indexing documents"
            ):
                results.append(await result)
        
        return IndexDirectoryResponse(
            total_files=len(pdf_files),
            success_count=success_count,
            failed_count=failed_count,
            total_chunks_created=total_chunks,
            failed_files=failed_files,
            message=f"Indexed {success_count}/{len(pdf_files)} documents successfully"
        )


class DeleteDocumentUseCase:
    """Use case for deleting a document"""
    
    def __init__(self, vector_repo: VectorRepository):
        self.vector_repo = vector_repo
    
    async def execute(self, document_id: str) -> bool:
        """Delete a document and all its chunks"""
        try:
            # For deletion, use document_id directly without PaperId validation
            # since document IDs may contain Korean characters and special characters
            deleted_count = await self.vector_repo.delete_by_document(document_id)
            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
            return deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False