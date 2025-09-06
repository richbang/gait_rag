#!/usr/bin/env python3
"""
Test full reindexing process monitoring
"""

import httpx
import asyncio
from pathlib import Path
from loguru import logger

async def test_full_reindex():
    """Test reindexing all PDFs with monitoring"""
    
    # Count total PDFs
    data_dir = Path("/data1/home/ict12/Kmong/medical_gait_rag/data")
    pdf_files = list(data_dir.rglob("*.pdf"))
    total_files = len(pdf_files)
    logger.info(f"Found {total_files} PDF files to index")
    
    # Reset vector store first
    logger.info("Resetting vector store...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post("http://localhost:8001/reset-vector-store")
        if response.status_code == 200:
            logger.info("Vector store reset successfully")
        else:
            logger.error(f"Failed to reset: {response.text}")
            return
    
    # Start indexing files
    logger.info("Starting indexing process...")
    success_count = 0
    failed_count = 0
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        try:
            logger.info(f"[{idx}/{total_files}] Indexing: {pdf_file.name}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "http://localhost:8001/index/document",
                    json={
                        "file_path": str(pdf_file),
                        "force_reindex": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    chunks = result.get("chunks_created", 0)
                    logger.info(f"  ✓ Success: {chunks} chunks created")
                    success_count += 1
                else:
                    logger.error(f"  ✗ Failed: Status {response.status_code}")
                    failed_count += 1
                    
        except Exception as e:
            logger.error(f"  ✗ Error: {e}")
            failed_count += 1
        
        # Progress update every 10 files
        if idx % 10 == 0:
            logger.info(f"Progress: {idx}/{total_files} files processed ({success_count} success, {failed_count} failed)")
        
        # Small delay to prevent overwhelming
        await asyncio.sleep(0.1)
    
    # Final summary
    logger.info("="*60)
    logger.info(f"INDEXING COMPLETE")
    logger.info(f"Total files: {total_files}")
    logger.info(f"Success: {success_count}")
    logger.info(f"Failed: {failed_count}")
    logger.info("="*60)
    
    # Get final statistics
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/statistics")
        if response.status_code == 200:
            stats = response.json()
            logger.info(f"Final stats: {stats['total_documents']} documents, {stats['total_chunks']} chunks")

if __name__ == "__main__":
    asyncio.run(test_full_reindex())