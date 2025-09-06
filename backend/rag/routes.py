"""RAG management routes for admin panel."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import os
import sys
from loguru import logger

from database.session import get_db
from auth.dependencies import get_current_user, require_admin
from database.models import User
from chat.rag_proxy import RAGProxyService
from .websocket import progress_manager

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.get("/stats")
async def get_rag_statistics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get RAG system statistics by calling RAG API.
    
    Returns:
        Statistics about indexed documents and vector store
    """
    try:
        import httpx
        
        # Call RAG API for statistics
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get("http://localhost:8001/statistics")
                if response.status_code == 200:
                    stats = response.json()
                    return {
                        "total_documents": stats.get("total_documents", 0),
                        "total_chunks": stats.get("total_chunks", 0),
                        "text_chunks": stats.get("text_chunks", 0),
                        "table_chunks": stats.get("table_chunks", 0),
                        "chunks_with_gait_params": stats.get("chunks_with_gait_params", 0),
                        "documents": stats.get("documents", [])
                    }
                else:
                    logger.error(f"RAG API returned {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Failed to connect to RAG API: {e}")
        
        # Fallback: try direct ChromaDB connection
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        from pathlib import Path
        
        # Connect directly to ChromaDB
        client = chromadb.PersistentClient(
            path="/data1/home/ict12/Kmong/medical_gait_rag/chroma_db",
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get collection
        try:
            collection = client.get_collection("gait_papers")
            
            # Get all documents
            result = collection.get()
            
            # Count statistics
            total_chunks = len(result['ids']) if result['ids'] else 0
            
            # Extract unique documents
            documents = set()
            text_chunks = 0
            table_chunks = 0
            chunks_with_gait_params = 0
            
            if result['metadatas']:
                for metadata in result['metadatas']:
                    if metadata:
                        if 'document_id' in metadata:
                            documents.add(metadata['document_id'])
                        if metadata.get('chunk_type') == 'TEXT':
                            text_chunks += 1
                        elif metadata.get('chunk_type') == 'TABLE':
                            table_chunks += 1
                        if metadata.get('has_gait_params'):
                            chunks_with_gait_params += 1
            
            return {
                "total_documents": len(documents),
                "total_chunks": total_chunks,
                "text_chunks": text_chunks,
                "table_chunks": table_chunks,
                "chunks_with_gait_params": chunks_with_gait_params,
                "documents": list(documents)
            }
            
        except Exception as e:
            # Collection doesn't exist
            logger.warning(f"Collection not found: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "text_chunks": 0,
                "table_chunks": 0,
                "chunks_with_gait_params": 0,
                "documents": []
            }
            
    except Exception as e:
        logger.error(f"Failed to get RAG statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all indexed documents by calling RAG API.
    
    Returns:
        List of indexed documents with metadata
    """
    try:
        import httpx
        from datetime import datetime
        
        # First try RAG API to get document list
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get("http://localhost:8001/statistics")
                if response.status_code == 200:
                    stats = response.json()
                    documents_list = stats.get("documents", [])
                    
                    if documents_list:
                        # Format documents for display
                        documents = []
                        for doc_id in documents_list:
                            documents.append({
                                'document_id': doc_id,
                                'file_name': doc_id.split('/')[-1] if '/' in doc_id else doc_id,
                                'chunks': 0,  # Set to 0 for now, we'll get chunk counts from ChromaDB
                                'indexed_at': datetime.now().isoformat()
                            })
                        
                        # Now try to get chunk counts from ChromaDB
                        try:
                            import chromadb
                            from chromadb.config import Settings as ChromaSettings
                            
                            logger.info("Attempting to connect to ChromaDB for chunk counts")
                            chroma_client = chromadb.PersistentClient(
                                path="/data1/home/ict12/Kmong/medical_gait_rag/chroma_db",
                                settings=ChromaSettings(anonymized_telemetry=False)
                            )
                            collection = chroma_client.get_collection("gait_papers")
                            result = collection.get()
                            
                            logger.info(f"ChromaDB query returned {len(result.get('ids', []))} chunks")
                            
                            # Count chunks per document
                            doc_chunks = {}
                            if result['metadatas']:
                                for metadata in result['metadatas']:
                                    if metadata and 'document_id' in metadata:
                                        doc_id = metadata['document_id']
                                        doc_chunks[doc_id] = doc_chunks.get(doc_id, 0) + 1
                            
                            logger.info(f"Found chunk counts for {len(doc_chunks)} documents")
                            
                            # Update chunk counts
                            for doc in documents:
                                doc['chunks'] = doc_chunks.get(doc['document_id'], 0)
                                logger.debug(f"Document {doc['file_name']}: {doc['chunks']} chunks")
                                
                        except Exception as e:
                            logger.error(f"Could not get chunk counts from ChromaDB: {e}")
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                        
                        # Sort by file name
                        documents.sort(key=lambda x: x['file_name'])
                        
                        return {'documents': documents, 'total': len(documents)}
            except Exception as e:
                logger.error(f"Failed to connect to RAG API: {e}")
        
        # Fallback: direct ChromaDB connection
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        
        client = chromadb.PersistentClient(
            path="/data1/home/ict12/Kmong/medical_gait_rag/chroma_db",
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        try:
            collection = client.get_collection("gait_papers")
            result = collection.get()
            
            # Count chunks per document
            doc_chunks = {}
            documents_set = set()
            
            if result['metadatas']:
                for metadata in result['metadatas']:
                    if metadata and 'document_id' in metadata:
                        doc_id = metadata['document_id']
                        documents_set.add(doc_id)
                        doc_chunks[doc_id] = doc_chunks.get(doc_id, 0) + 1
            
            # Format documents for display
            documents = []
            for doc_id in documents_set:
                documents.append({
                    'document_id': doc_id,
                    'file_name': doc_id.split('/')[-1] if '/' in doc_id else doc_id,
                    'chunks': doc_chunks.get(doc_id, 0),
                    'indexed_at': datetime.now().isoformat()  # Current time as placeholder
                })
            
            # Sort by file name
            documents.sort(key=lambda x: x['file_name'])
            
            return {'documents': documents, 'total': len(documents)}
            
        except Exception as e:
            logger.warning(f"Collection not found: {e}")
            return {'documents': [], 'total': 0}
            
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Upload and index a new document.
    
    Args:
        file: PDF file to upload and index
        
    Returns:
        Upload status and document ID
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Use the data/uploads directory for consistency with main data directory
        upload_dir = Path("/data1/home/ict12/Kmong/medical_gait_rag/data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file with timestamp to avoid conflicts
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / safe_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded file: {file_path}")
        
        # First check if document already exists
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get current statistics to check existing documents
            stats_response = await client.get("http://localhost:8001/statistics")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                existing_docs = stats.get("documents", [])
                
                # Check if this file (by original name) is already indexed
                relative_path = str(file_path).split("data/", 1)[1] if "data/" in str(file_path) else str(file_path)
                
                # If document exists and force_reindex is False, skip
                if any(file.filename in doc for doc in existing_docs):
                    logger.info(f"Document {file.filename} already indexed, performing incremental update")
            
            # Index the document (will be incremental if already exists)
            response = await client.post(
                "http://localhost:8001/index/document",
                json={
                    "file_path": str(file_path),
                    "force_reindex": False  # Incremental update
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": "success",
                "message": f"Document {file.filename} uploaded and indexed successfully",
                "document_id": result.get("document_id"),
                "chunks_created": result.get("chunks_created", 0),
                "file_path": str(file_path),
                "incremental": True  # Indicates incremental update
            }
        
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id:path}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an indexed document.
    
    Args:
        document_id: ID of document to delete (path parameter)
        
    Returns:
        Deletion status
    """
    try:
        import httpx
        import urllib.parse
        
        # URL decode the document_id
        decoded_document_id = urllib.parse.unquote(document_id)
        logger.info(f"Attempting to delete document: {decoded_document_id}")
        
        async with httpx.AsyncClient() as client:
            # Encode the document_id properly for the RAG API
            encoded_document_id = urllib.parse.quote(decoded_document_id, safe='')
            response = await client.delete(f"http://localhost:8001/documents/{encoded_document_id}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully deleted document: {decoded_document_id}")
                return {
                    "status": "success",
                    "message": f"Document {decoded_document_id} deleted successfully",
                    "chunks_deleted": result.get("chunks_deleted", 0)
                }
            else:
                # Check if the error is "not found" - treat as success (idempotent)
                try:
                    error_text = response.text
                    if "not found" in error_text.lower() or "already deleted" in error_text.lower():
                        logger.info(f"Document not found or already deleted: {decoded_document_id}")
                        return {
                            "status": "success", 
                            "message": f"Document {decoded_document_id} not found or already deleted",
                            "chunks_deleted": 0
                        }
                except:
                    pass
                    
                logger.error(f"RAG API returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex")
async def reindex_all_documents(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Reindex all documents in the storage directory.
    
    Returns:
        Reindexing status
    """
    try:
        import httpx
        from pathlib import Path
        
        # First, reset the vector store
        reset_script = Path("/data1/home/ict12/Kmong/medical_gait_rag/reset_vector_store.py")
        import subprocess
        result = subprocess.run(
            [sys.executable, str(reset_script)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/data1/home/ict12/Kmong/medical_gait_rag"
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to reset vector store: {result.stderr}")
        else:
            logger.info("Vector store reset for reindexing")
            
        # Also reset the RAG API's vector store instance
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                reset_response = await client.post("http://localhost:8001/reset-vector-store")
                if reset_response.status_code == 200:
                    logger.info("RAG API vector store instance reset successfully")
                else:
                    logger.warning(f"Failed to reset RAG API vector store: {reset_response.text}")
        except Exception as e:
            logger.warning(f"Could not reset RAG API vector store: {e}")
        
        # Use the RAG API for indexing with progress monitoring
        async def run_indexing():
            logger.info("Starting background indexing task")
            try:
                # First, get list of files to process
                from pathlib import Path
                data_dir = Path("/data1/home/ict12/Kmong/medical_gait_rag/data")
                pdf_files = list(data_dir.rglob("*.pdf"))
                logger.info(f"Found {len(pdf_files)} PDF files to index")
                
                await progress_manager.start_indexing(len(pdf_files))
                logger.info("Progress manager initialized")
                
                # Process files one by one for better progress tracking
                success_count = 0
                failed_count = 0
                
                # Use separate client for each request to avoid connection issues
                logger.info(f"Starting to process {len(pdf_files)} files")
                for idx, pdf_file in enumerate(pdf_files, 1):
                    file_path = str(pdf_file)
                    filename = pdf_file.name
                    
                    logger.info(f"Processing file {idx}/{len(pdf_files)}: {filename}")
                    await progress_manager.file_processing(filename)
                    logger.debug(f"Progress manager notified for {filename}")
                    
                    try:
                        # Create new client for each file to avoid connection pool issues
                        logger.debug(f"Creating HTTP client for {filename}")
                        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                            # Index single file
                            logger.debug(f"Sending index request for: {file_path}")
                            response = await client.post(
                                "http://localhost:8001/index/document",
                                json={
                                    "file_path": file_path,
                                    "force_reindex": False
                                }
                            )
                            logger.debug(f"Received response for {filename}: status={response.status_code}")
                            
                            # Process response inside the async with block
                            if response.status_code == 200:
                                result = response.json()
                                chunks = result.get("chunks_created", 0)
                                await progress_manager.file_completed(filename, chunks, True)
                                success_count += 1
                                logger.info(f"Successfully indexed {filename}: {chunks} chunks")
                            else:
                                await progress_manager.file_completed(filename, 0, False)
                                failed_count += 1
                                logger.error(f"Failed to index {filename}: Status {response.status_code}: {response.text}")
                                
                    except Exception as e:
                        await progress_manager.file_completed(filename, 0, False)
                        failed_count += 1
                        logger.error(f"Error indexing {filename}: {e}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    # Update overall progress
                    await progress_manager.update_progress({
                        "completed_files": idx,
                        "message": f"Progress: {idx}/{len(pdf_files)} files"
                    })
                    
                    # Add small delay between files to prevent overwhelming the system
                    import asyncio
                    await asyncio.sleep(0.5)
                    logger.debug(f"Completed processing {idx}/{len(pdf_files)} files, moving to next...")
                
                logger.info("All files processed, finishing indexing...")
                await progress_manager.finish_indexing()
                logger.info(f"Reindexing completed: {success_count} success, {failed_count} failed")
                logger.info("Background indexing task completed successfully")
                        
            except Exception as e:
                logger.error(f"Reindexing error: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                await progress_manager.update_progress({
                    "status": "error",
                    "message": f"Error: {str(e)}"
                })
                logger.error("Background indexing task failed")
        
        # Start reindexing in background
        background_tasks.add_task(run_indexing)
        
        return {
            "status": "success",
            "message": "Reindexing started in background. This may take several minutes.",
            "details": {
                "directory": "data/",
                "api_endpoint": "http://localhost:8001",
                "reset": True
            }
        }
    except Exception as e:
        logger.error(f"Failed to start reindexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/embedding/status")
async def get_embedding_status(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get embedding service status.
    
    Returns:
        Embedding model information and status
    """
    try:
        import httpx
        
        # Try to get actual status from RAG API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8001/health")
                if response.status_code == 200:
                    # RAG API is running with embeddings on GPU
                    return {
                        "status": "active",
                        "model": "jinaai/jina-embeddings-v4",
                        "dimension": 2048,
                        "device": "cuda:0",  # RAG API runs on GPU 0
                        "max_length": 8192,
                        "api_status": "connected"
                    }
        except:
            pass
        
        # Fallback if RAG API is not available
        return {
            "status": "inactive",
            "model": "jinaai/jina-embeddings-v4",
            "dimension": 2048,
            "device": "not loaded",
            "max_length": 8192,
            "api_status": "disconnected"
        }
    except Exception as e:
        logger.error(f"Failed to get embedding status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vllm/status")
async def get_vllm_status(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get vLLM service status.
    
    Returns:
        vLLM model information and status
    """
    try:
        rag_proxy = RAGProxyService()
        
        # Test vLLM connection
        try:
            response = await rag_proxy.direct_llm_query(
                query="Test",
                use_vllm=True
            )
            vllm_active = True
        except:
            vllm_active = False
        
        return {
            "status": "active" if vllm_active else "inactive",
            "model": "nvidia/Llama-3.1-Nemotron-Mini-128k-Instruct",
            "api_url": rag_proxy.vllm_url,  # Changed from vllm_api_url to vllm_url
            "max_tokens": 2048,
            "temperature": 0.7
        }
    except Exception as e:
        logger.error(f"Failed to get vLLM status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_vector_store(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Clear all data from vector store.
    WARNING: This will delete all indexed documents!
    
    Returns:
        Clear status
    """
    try:
        import subprocess
        import sys
        from pathlib import Path
        
        # Use the reset script
        reset_script = Path("/data1/home/ict12/Kmong/medical_gait_rag/reset_vector_store.py")
        
        result = subprocess.run(
            [sys.executable, str(reset_script)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/data1/home/ict12/Kmong/medical_gait_rag"
        )
        
        if result.returncode != 0:
            logger.error(f"Reset failed: {result.stderr}")
            raise Exception(f"Reset failed: {result.stderr}")
            
        logger.info("Vector store cleared successfully")
        
        return {
            "status": "success",
            "message": "Vector store cleared successfully",
            "details": result.stdout
        }
    except Exception as e:
        logger.error(f"Failed to clear vector store: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for real-time indexing progress."""
    await progress_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        progress_manager.disconnect(websocket)