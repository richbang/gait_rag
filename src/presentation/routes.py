"""
API Route Definitions
"""

from typing import List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks  # API 체크완료: FastAPI imports correct
from pydantic import BaseModel  # API 체크완료: Pydantic v2 BaseModel correct
import logging

from ..container import Container
from ..application.dto import (
    IndexDocumentRequest, SearchRequest, IndexDirectoryRequest
)
from ..domain.entities import DocumentType, DiseaseCategory

logger = logging.getLogger(__name__)


# Request/Response Models

class SearchRequestModel(BaseModel):  # API 체크완료: Pydantic BaseModel usage correct
    """Search request model"""
    query: str
    limit: int = 5
    document_types: Optional[List[DocumentType]] = None
    disease_categories: Optional[List[DiseaseCategory]] = None
    require_gait_params: bool = False
    paper_ids: Optional[List[str]] = None
    min_score: float = 0.0


class QARequestModel(BaseModel):
    """Question-Answer request model with vLLM"""
    query: str
    limit: int = 5
    use_vllm: bool = True  # Enable answer generation
    document_types: Optional[List[DocumentType]] = None
    disease_categories: Optional[List[DiseaseCategory]] = None
    require_gait_params: bool = False
    min_score: float = 0.0
    direct_mode: bool = False  # Direct LLM mode without document search


class IndexDocumentRequestModel(BaseModel):
    """Index document request model"""
    file_path: str
    force_reindex: bool = False


class IndexDirectoryRequestModel(BaseModel):
    """Index directory request model"""
    directory_path: str
    max_files: Optional[int] = None
    recursive: bool = True
    force_reindex: bool = False


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    version: str


# Dependency

def get_container(app: FastAPI) -> Container:  # API 체크완료: Dependency function correct
    """Get container from app state"""
    return app.state.container


# Route Setup

def setup_routes(app: FastAPI):  # API 체크완료: Route setup function correct
    """Setup all API routes"""
    
    @app.get("/", response_model=HealthResponse)  # API 체크완료: response_model usage correct
    async def root():
        """Root endpoint"""
        return HealthResponse(
            status="healthy",
            message="Medical Gait Analysis RAG API",
            version="2.0.0"
        )
    
    @app.get("/health", response_model=HealthResponse)  # API 체크완료: response_model usage correct
    async def health_check():
        """Health check endpoint"""
        return HealthResponse(
            status="healthy",
            message="Service is running",
            version="2.0.0"
        )
    
    @app.post("/search")
    async def search_documents(
        request: SearchRequestModel,
        container: Container = Depends(lambda: get_container(app))  # API 체크완료: Depends usage correct
    ):
        """Search for documents matching query"""
        try:
            # Convert to application DTO
            search_request = SearchRequest(
                query=request.query,
                limit=request.limit,
                document_types=request.document_types,
                disease_categories=request.disease_categories,
                require_gait_params=request.require_gait_params,
                paper_ids=request.paper_ids,
                min_score=request.min_score
            )
            
            # Execute use case
            response = await container.search_documents_use_case.execute(search_request)
            
            if response.error:
                raise HTTPException(status_code=500, detail=response.error)  # API 체크완료: HTTPException usage correct
            
            # Convert results for JSON serialization
            results = []
            for result in response.results:
                results.append({
                    "chunk_id": result.chunk.chunk_id,
                    "document_id": result.chunk.document_id,
                    "content": result.chunk.content,
                    "page_number": result.chunk.page_number,
                    "chunk_type": result.chunk.chunk_type.value,
                    "score": result.score,
                    "has_gait_params": result.chunk.has_gait_parameters(),
                    "gait_parameters": [
                        {
                            "name": p.name,
                            "value": p.value,
                            "unit": p.unit
                        } for p in result.chunk.gait_parameters
                    ] if result.chunk.gait_parameters else [],
                    "metadata": result.document_metadata
                })
            
            return {
                "query": response.query,
                "results": results,
                "total_results": response.total_results,
                "search_time": response.search_time
            }
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))  # API 체크완료: HTTPException usage correct
    
    @app.post("/qa")
    async def question_answer(
        request: QARequestModel,
        container: Container = Depends(lambda: get_container(app))
    ):
        """Search and generate answer using vLLM"""
        try:
            # Check for direct mode (no document search)
            if request.direct_mode:
                logger.info(f"Direct mode activated for query: {request.query[:50]}...")
                # Direct LLM mode without search
                answer = None
                if request.use_vllm and container.vllm_client:
                    try:
                        # Use general assistant prompt for chat mode
                        chat_prompt = "You are a helpful assistant. Please respond naturally in Korean."
                        answer = await container.vllm_client.generate(
                            prompt=request.query,
                            context=None,  # No document context in chat mode
                            system_prompt=chat_prompt
                        )
                    except Exception as e:
                        logger.error(f"Direct vLLM generation failed: {e}")
                        answer = "답변 생성에 실패했습니다. 다시 시도해주세요."
                else:
                    answer = "LLM 서버가 사용 불가능합니다."
                
                return {
                    "query": request.query,
                    "answer": answer,
                    "sources": [],
                    "total_sources": 0,
                    "vllm_used": answer is not None
                }
            
            # First, search for relevant documents
            search_request = SearchRequest(
                query=request.query,
                limit=request.limit,
                document_types=request.document_types,
                disease_categories=request.disease_categories,
                require_gait_params=request.require_gait_params,
                min_score=request.min_score
            )
            
            search_response = await container.search_documents_use_case.execute(search_request)
            
            if search_response.error:
                raise HTTPException(status_code=500, detail=search_response.error)
            
            # Prepare context from search results
            context_chunks = []
            for result in search_response.results[:request.limit]:
                context_chunks.append(
                    f"[Document: {result.chunk.document_id}, Page: {result.chunk.page_number}]\n"
                    f"{result.chunk.content}\n"
                )
            
            context = "\n---\n".join(context_chunks)
            
            # Generate answer using vLLM if enabled
            answer = None
            if request.use_vllm and container.vllm_client:
                try:
                    answer = await container.vllm_client.generate(
                        prompt=request.query,
                        context=context,
                        system_prompt=(
                            "You are a medical AI assistant specializing in gait analysis. "
                            "Answer based on the provided research papers and clinical data. "
                            "Be specific and cite document sources. "
                            "Respond in Korean."
                        )
                    )
                except Exception as e:
                    logger.warning(f"vLLM generation failed: {e}")
                    answer = "Answer generation failed. Please check vLLM server."
            
            # Format search results
            results = []
            for result in search_response.results:
                results.append({
                    "chunk_id": result.chunk.chunk_id,
                    "document_id": result.chunk.document_id,
                    "content": result.chunk.content,
                    "page_number": result.chunk.page_number,
                    "score": result.score,
                    "has_gait_params": result.chunk.has_gait_parameters(),
                })
            
            return {
                "query": request.query,
                "answer": answer,  # Generated answer from vLLM
                "sources": results,  # Source documents used
                "total_sources": len(results),
                "vllm_used": answer is not None
            }
            
        except Exception as e:
            logger.error(f"QA error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/index/document")
    async def index_document(
        request: IndexDocumentRequestModel,
        background_tasks: BackgroundTasks,  # API 체크완료: BackgroundTasks parameter correct
        container: Container = Depends(lambda: get_container(app))
    ):
        """Index a single document"""
        try:
            # Validate file exists
            if not Path(request.file_path).exists():
                raise HTTPException(  # API 체크완료: HTTPException with 400 status correct
                    status_code=400,
                    detail=f"File not found: {request.file_path}"
                )
            
            # Convert to application DTO
            index_request = IndexDocumentRequest(
                file_path=request.file_path,
                force_reindex=request.force_reindex
            )
            
            # Execute use case
            response = await container.index_document_use_case.execute(index_request)
            
            return {
                "success": response.success,
                "document_id": response.document_id,
                "chunks_created": response.chunks_created,
                "tables_found": response.tables_found,
                "pages_processed": response.pages_processed,
                "processing_time": response.processing_time,
                "message": response.message,
                "error": response.error
            }
            
        except Exception as e:
            logger.error(f"Index document error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))  # API 체크완료: HTTPException usage correct
    
    @app.post("/index/directory")
    async def index_directory(
        request: IndexDirectoryRequestModel,
        container: Container = Depends(lambda: get_container(app))
    ):
        """Index all documents in a directory"""
        try:
            # Validate directory exists
            if not Path(request.directory_path).exists():
                raise HTTPException(  # API 체크완료: HTTPException with 400 status correct
                    status_code=400,
                    detail=f"Directory not found: {request.directory_path}"
                )
            
            # Convert to application DTO
            index_request = IndexDirectoryRequest(
                directory_path=request.directory_path,
                max_files=request.max_files,
                recursive=request.recursive,
                force_reindex=request.force_reindex
            )
            
            # Execute use case
            response = await container.index_directory_use_case.execute(index_request)
            
            return {
                "total_files": response.total_files,
                "success_count": response.success_count,
                "failed_count": response.failed_count,
                "total_chunks_created": response.total_chunks_created,
                "failed_files": response.failed_files,
                "message": response.message,
                "processing_time": response.processing_time
            }
            
        except Exception as e:
            logger.error(f"Index directory error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))  # API 체크완료: HTTPException usage correct
    
    @app.post("/reset-vector-store")
    async def reset_vector_store(
        container: Container = Depends(lambda: get_container(app))
    ):
        """Reset the vector store collection"""
        try:
            # Import ChromaDB to manually reset
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            from pathlib import Path
            
            # Delete the collection directly
            chroma_path = Path("/data1/home/ict12/Kmong/medical_gait_rag/chroma_db")
            client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            try:
                client.delete_collection("gait_papers")
                logger.info("Deleted existing collection: gait_papers")
            except:
                pass
            
            # Create new collection
            client.create_collection(
                name="gait_papers",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Created new collection: gait_papers")
            
            # Force recreate vector repository in container
            container._vector_repo = None
            
            return {
                "status": "success",
                "message": "Vector store reset successfully"
            }
        except Exception as e:
            logger.error(f"Reset vector store error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/statistics")
    async def get_statistics(
        container: Container = Depends(lambda: get_container(app))
    ):
        """Get system statistics"""
        try:
            response = await container.get_statistics_use_case.execute()
            
            if response.error:
                raise HTTPException(status_code=500, detail=response.error)  # API 체크완료: HTTPException usage correct
            
            return {
                "total_documents": response.total_documents,
                "total_chunks": response.total_chunks,
                "text_chunks": response.text_chunks,
                "table_chunks": response.table_chunks,
                "chunks_with_gait_params": response.chunks_with_gait_params,
                "documents": response.documents,
                "metadata": response.metadata
            }
            
        except Exception as e:
            logger.error(f"Statistics error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))  # API 체크완료: HTTPException usage correct
    
    @app.delete("/documents/{document_id:path}")
    async def delete_document(
        document_id: str,
        container: Container = Depends(lambda: get_container(app))
    ):
        """Delete a document and all its chunks"""
        try:
            import urllib.parse
            # URL decode the document_id
            decoded_document_id = urllib.parse.unquote(document_id)
            logger.info(f"Deleting document: {decoded_document_id}")
            
            success = await container.delete_document_use_case.execute(decoded_document_id)
            
            if success:
                return {"message": f"Document {decoded_document_id} deleted successfully"}
            else:
                # If no chunks found, consider it already deleted (idempotent operation)
                logger.info(f"Document {decoded_document_id} not found or already deleted")
                return {"message": f"Document {decoded_document_id} not found or already deleted", "deleted_count": 0}
                
        except Exception as e:
            logger.error(f"Delete document error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))  # API 체크완료: HTTPException usage correct
    
    @app.post("/reset")
    async def reset_collection(
        container: Container = Depends(lambda: get_container(app))
    ):
        """Reset the entire collection (delete all data)"""
        try:
            container.reset_vector_store()
            return {"message": "Collection reset successfully"}
            
        except Exception as e:
            logger.error(f"Reset collection error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))  # API 체크완료: HTTPException usage correct