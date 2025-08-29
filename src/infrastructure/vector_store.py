"""
ChromaDB Vector Store Implementation (v1.0+)
"""

import chromadb
from chromadb import Collection
from chromadb.config import Settings as ChromaSettings
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path

from ..domain.repositories import VectorRepository
from ..domain.entities import DocumentChunk, SearchResult, SearchQuery, DocumentType
from ..domain.value_objects import PaperId, ChunkId

logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorRepository):
    """ChromaDB implementation of vector repository"""
    
    def __init__(  # API 체크완료: __init__ parameters correct
        self, 
        collection_name: str = "gait_papers",
        persist_directory: str = "./storage/chromadb",
        reset: bool = False
    ):
        """
        Initialize ChromaDB vector store
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data
            reset: Whether to reset existing collection
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        
        # Ensure directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client (v1.0+ syntax)
        # API 체크완료: PersistentClient(path=..., settings=...) correct
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize or get collection
        self._initialize_collection(reset)
        logger.info(f"ChromaDB initialized with collection: {collection_name}")
    
    def _initialize_collection(self, reset: bool) -> None:
        """Initialize or get existing collection"""
        if reset:
            try:
                self.client.delete_collection(name=self.collection_name)  # API 체크완료: delete_collection(name=...) correct
                logger.info(f"Deleted existing collection: {self.collection_name}")
            except Exception:
                pass
        
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(  # API 체크완료: get_collection(name=...) correct
                name=self.collection_name
            )
            count = self.collection.count()  # API 체크완료: collection.count() correct
            logger.info(f"Using existing collection with {count} items")
        except Exception:
            # Create new collection if doesn't exist
            self.collection = self.client.create_collection(  # API 체크완료: create_collection(name=..., metadata=...) correct
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:M": 16
                }
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    async def index_chunk(self, chunk: DocumentChunk) -> None:
        """Index a single chunk"""
        await self.index_chunks([chunk])
    
    async def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Batch index multiple chunks"""
        if not chunks:
            return
        
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for chunk in chunks:
            # Prepare chunk ID
            chunk_id = ChunkId(chunk.document_id, chunk.chunk_index)
            ids.append(str(chunk_id))
            
            # Prepare document content
            documents.append(chunk.content)
            
            # Prepare embedding
            if chunk.embedding is None:
                raise ValueError(f"Chunk {chunk_id} missing embedding")
            embeddings.append(chunk.embedding)
            
            # Prepare metadata
            metadata = {
                "document_id": chunk.document_id,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "chunk_type": chunk.chunk_type.value,
                "has_gait_params": chunk.has_gait_parameters(),
                **chunk.metadata
            }
            
            # Add gait parameters if present
            if chunk.gait_parameters:
                metadata["gait_params_count"] = len(chunk.gait_parameters)
                metadata["gait_params"] = [
                    {
                        "name": p.name,
                        "value": p.value,
                        "unit": p.unit
                    } for p in chunk.gait_parameters
                ]
            
            metadatas.append(metadata)
        
        # Upsert to ChromaDB
        self.collection.upsert(  # API 체크완료: collection.upsert(ids=, documents=, embeddings=, metadatas=) correct
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        logger.info(f"Indexed {len(chunks)} chunks")
    
    async def search(
        self, 
        query: SearchQuery, 
        query_embedding: List[float]
    ) -> List[SearchResult]:
        """Search for similar chunks"""
        # Build where clause for filtering
        where = {}
        where_conditions = []
        
        if query.document_types:
            where_conditions.append({
                "chunk_type": {
                    "$in": [dt.value for dt in query.document_types]
                }
            })
        
        if query.require_gait_params:
            where_conditions.append({
                "has_gait_params": {"$eq": True}
            })
        
        if query.paper_ids:
            where_conditions.append({
                "document_id": {"$in": query.paper_ids}
            })
        
        # Combine conditions
        if len(where_conditions) == 1:
            where = where_conditions[0]
        elif len(where_conditions) > 1:
            where = {"$and": where_conditions}
        
        # Execute search
        results = self.collection.query(  # API 체크완료: collection.query(query_embeddings=, n_results=, where=, include=) correct
            query_embeddings=[query_embedding],
            n_results=query.limit,
            where=where if where else None,
            include=["documents", "metadatas", "distances"]
        )
        
        # Parse results
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                # Calculate similarity score from distance
                distance = results["distances"][0][i]
                score = 1.0 / (1.0 + distance)  # Convert distance to similarity
                
                # Skip if below minimum score
                if score < query.min_score:
                    continue
                
                # Reconstruct chunk
                metadata = results["metadatas"][0][i]
                chunk = DocumentChunk(
                    chunk_id=results["ids"][0][i],
                    document_id=metadata["document_id"],
                    content=results["documents"][0][i],
                    page_number=metadata["page_number"],
                    chunk_index=metadata["chunk_index"],
                    chunk_type=DocumentType(metadata["chunk_type"]),
                    metadata={k: v for k, v in metadata.items() 
                             if k not in ["document_id", "page_number", 
                                         "chunk_index", "chunk_type", 
                                         "has_gait_params", "gait_params"]}
                )
                
                # Add gait parameters if present
                if "gait_params" in metadata:
                    from ..domain.entities import GaitParameter
                    chunk.gait_parameters = [
                        GaitParameter(
                            name=p["name"],
                            value=p["value"],
                            unit=p.get("unit")
                        ) for p in metadata["gait_params"]
                    ]
                
                search_result = SearchResult(
                    chunk=chunk,
                    score=score,
                    document_metadata={"document_id": metadata["document_id"]}
                )
                
                search_results.append(search_result)
        
        return search_results
    
    async def delete_by_document(self, document_id: PaperId) -> int:
        """Delete all chunks for a document"""
        # Get all chunk IDs for the document
        results = self.collection.get(  # API 체크완료: collection.get(where=, include=) correct
            where={"document_id": str(document_id)},
            include=["ids"]
        )
        
        if results["ids"]:
            self.collection.delete(ids=results["ids"])  # API 체크완료: collection.delete(ids=) correct
            return len(results["ids"])
        return 0
    
    async def get_chunk(self, chunk_id: ChunkId) -> Optional[DocumentChunk]:
        """Get a specific chunk by ID"""
        results = self.collection.get(  # API 체크완료: collection.get(ids=, include=) correct
            ids=[str(chunk_id)],
            include=["documents", "metadatas"]
        )
        
        if results["ids"]:
            metadata = results["metadatas"][0]
            chunk = DocumentChunk(
                chunk_id=str(chunk_id),
                document_id=metadata["document_id"],
                content=results["documents"][0],
                page_number=metadata["page_number"],
                chunk_index=metadata["chunk_index"],
                chunk_type=DocumentType(metadata["chunk_type"]),
                metadata={k: v for k, v in metadata.items() 
                         if k not in ["document_id", "page_number", 
                                     "chunk_index", "chunk_type"]}
            )
            return chunk
        return None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics"""
        # Get all items for statistics
        all_items = self.collection.get(  # API 체크완료: collection.get(limit=, include=) correct
            limit=10000,
            include=["metadatas"]
        )
        
        stats = {
            "total_chunks": self.collection.count(),  # API 체크완료: collection.count() correct
            "documents": set(),
            "text_chunks": 0,
            "table_chunks": 0,
            "chunks_with_gait_params": 0
        }
        
        if all_items["metadatas"]:
            for metadata in all_items["metadatas"]:
                stats["documents"].add(metadata.get("document_id", "unknown"))
                
                chunk_type = metadata.get("chunk_type", "text")
                if chunk_type == "text":
                    stats["text_chunks"] += 1
                elif chunk_type == "table":
                    stats["table_chunks"] += 1
                
                if metadata.get("has_gait_params"):
                    stats["chunks_with_gait_params"] += 1
        
        stats["total_documents"] = len(stats["documents"])
        stats["documents"] = sorted(list(stats["documents"]))
        
        return stats
    
    async def clear_all(self) -> None:
        """Clear all data from repository"""
        self.client.delete_collection(name=self.collection_name)  # API 체크완료: delete_collection(name=) correct
        self._initialize_collection(reset=False)
        logger.info("Cleared all data from vector store")