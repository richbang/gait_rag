"""
Dependency Injection Container
"""

from typing import Optional
import logging

from .infrastructure import (
    ChromaVectorStore,
    JinaEmbeddingService,
    PDFDocumentProcessor,
    VLLMClient,
    get_settings,
    Settings
)

from .application import (
    IndexDocumentUseCase,
    SearchDocumentsUseCase,
    GetStatisticsUseCase,
    IndexDirectoryUseCase,
    DeleteDocumentUseCase
)

logger = logging.getLogger(__name__)


class Container:
    """Dependency injection container"""
    
    def __init__(self, settings: Optional[Settings] = None):  # API 체크완료: Container initialization with Settings correct
        """Initialize container with settings"""
        self.settings = settings or get_settings()  # API 체크완료: get_settings() from pydantic-settings correct
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.settings.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize repositories
        self._vector_repo = None
        
        # Initialize services
        self._embedding_service = None
        self._document_processor = None
        self._vllm_client = None
        
        # Initialize use cases
        self._index_document_use_case = None
        self._search_documents_use_case = None
        self._get_statistics_use_case = None
        self._index_directory_use_case = None
        self._delete_document_use_case = None
        
        logger.info("Container initialized")
    
    # Repositories
    
    @property
    def vector_repository(self) -> ChromaVectorStore:  # API 체크완료: Lazy loading pattern correct
        """Get vector repository instance"""
        if self._vector_repo is None:
            self._vector_repo = ChromaVectorStore(  # API 체크완료: ChromaVectorStore initialization correct
                collection_name=self.settings.chroma_collection_name,
                persist_directory=self.settings.chroma_persist_directory,
                reset=False
            )
        return self._vector_repo
    
    # Services
    
    @property
    def embedding_service(self) -> JinaEmbeddingService:  # API 체크완료: Lazy loading pattern correct
        """Get embedding service instance"""
        if self._embedding_service is None:
            self._embedding_service = JinaEmbeddingService(  # API 체크완료: JinaEmbeddingService initialization correct
                model_name=self.settings.jina_model_name,
                device=self.settings.embedding_device,
                batch_size=self.settings.embedding_batch_size
            )
        return self._embedding_service
    
    @property
    def document_processor(self) -> PDFDocumentProcessor:  # API 체크완료: Lazy loading pattern correct
        """Get document processor instance"""
        if self._document_processor is None:
            self._document_processor = PDFDocumentProcessor(  # API 체크완료: PDFDocumentProcessor initialization correct
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
                max_pages=self.settings.max_pages_per_doc
            )
        return self._document_processor
    
    @property
    def vllm_client(self) -> Optional[VLLMClient]:
        """Get vLLM client instance (if enabled)"""
        if self.settings.use_vllm and self._vllm_client is None:
            self._vllm_client = VLLMClient(
                api_url=self.settings.vllm_api_url,
                model=self.settings.vllm_model,
                max_tokens=self.settings.vllm_max_tokens,
                temperature=self.settings.vllm_temperature
            )
        return self._vllm_client if self.settings.use_vllm else None
    
    # Use Cases
    
    @property
    def index_document_use_case(self) -> IndexDocumentUseCase:
        """Get index document use case"""
        if self._index_document_use_case is None:
            self._index_document_use_case = IndexDocumentUseCase(
                vector_repo=self.vector_repository,
                embedding_service=self.embedding_service,
                document_processor=self.document_processor
            )
        return self._index_document_use_case
    
    @property
    def search_documents_use_case(self) -> SearchDocumentsUseCase:
        """Get search documents use case"""
        if self._search_documents_use_case is None:
            self._search_documents_use_case = SearchDocumentsUseCase(
                vector_repo=self.vector_repository,
                embedding_service=self.embedding_service
            )
        return self._search_documents_use_case
    
    @property
    def get_statistics_use_case(self) -> GetStatisticsUseCase:
        """Get statistics use case"""
        if self._get_statistics_use_case is None:
            self._get_statistics_use_case = GetStatisticsUseCase(
                vector_repo=self.vector_repository
            )
        return self._get_statistics_use_case
    
    @property
    def index_directory_use_case(self) -> IndexDirectoryUseCase:
        """Get index directory use case"""
        if self._index_directory_use_case is None:
            self._index_directory_use_case = IndexDirectoryUseCase(
                index_document_use_case=self.index_document_use_case,
                vector_repo=self.vector_repository
            )
        return self._index_directory_use_case
    
    @property
    def delete_document_use_case(self) -> DeleteDocumentUseCase:
        """Get delete document use case"""
        if self._delete_document_use_case is None:
            self._delete_document_use_case = DeleteDocumentUseCase(
                vector_repo=self.vector_repository
            )
        return self._delete_document_use_case
    
    def reset_vector_store(self) -> None:  # API 체크완료: Reset method correct
        """Reset vector store (delete all data)"""
        self._vector_repo = ChromaVectorStore(  # API 체크완료: ChromaVectorStore with reset=True correct
            collection_name=self.settings.chroma_collection_name,
            persist_directory=self.settings.chroma_persist_directory,
            reset=True
        )
        logger.info("Vector store reset")


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:  # API 체크완료: Singleton pattern correct
    """Get or create container instance"""
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container() -> None:
    """Reset container instance"""
    global _container
    _container = None