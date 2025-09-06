#!/usr/bin/env python3
"""
Debug script to test reindexing process
"""

import asyncio
import httpx
from pathlib import Path
import logging
from typing import List

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_single_file_index():
    """Test indexing a single file"""
    # Use actual file from subdirectory
    pdf_file = "/data1/home/ict12/Kmong/medical_gait_rag/data/2. 25.04.30-기타질환/파킨슨/B 2022.pdf"
    
    logger.info(f"Testing single file: {pdf_file}")
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        try:
            response = await client.post(
                "http://localhost:8001/index/document",
                json={
                    "file_path": pdf_file,
                    "force_reindex": True
                }
            )
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.json()}")
            return True
        except Exception as e:
            logger.error(f"Failed to index file: {e}")
            return False

async def test_multiple_files_sequential():
    """Test indexing multiple files sequentially"""
    data_dir = Path("/data1/home/ict12/Kmong/medical_gait_rag/data")
    pdf_files = list(data_dir.rglob("*.pdf"))[:3]  # Test with first 3 files using recursive glob
    
    logger.info(f"Testing {len(pdf_files)} files sequentially")
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        logger.info(f"\n--- Processing file {idx}/{len(pdf_files)}: {pdf_file.name} ---")
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            try:
                response = await client.post(
                    "http://localhost:8001/index/document",
                    json={
                        "file_path": str(pdf_file),
                        "force_reindex": False
                    }
                )
                logger.info(f"Response status: {response.status_code}")
                result = response.json()
                logger.info(f"Success: {result.get('success')}, Chunks: {result.get('chunks_created')}")
                
                # Small delay between files
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to index file {pdf_file.name}: {e}")
                break
        
        logger.info(f"Completed processing file {idx}")
    
    logger.info("Sequential test completed")

async def test_multiple_files_background():
    """Test indexing with background task simulation"""
    data_dir = Path("/data1/home/ict12/Kmong/medical_gait_rag/data")
    pdf_files = list(data_dir.rglob("*.pdf"))[:3]  # Use recursive glob
    
    logger.info(f"Testing {len(pdf_files)} files in background task")
    
    async def background_task():
        for idx, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"\n[BG] Processing file {idx}/{len(pdf_files)}: {pdf_file.name}")
            
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                try:
                    response = await client.post(
                        "http://localhost:8001/index/document",
                        json={
                            "file_path": str(pdf_file),
                            "force_reindex": False
                        }
                    )
                    logger.info(f"[BG] Response status: {response.status_code}")
                    result = response.json()
                    logger.info(f"[BG] Success: {result.get('success')}, Chunks: {result.get('chunks_created')}")
                    
                except Exception as e:
                    logger.error(f"[BG] Failed to index file {pdf_file.name}: {e}")
                    break
            
            logger.info(f"[BG] Completed file {idx}")
            await asyncio.sleep(0.5)
        
        logger.info("[BG] Background task completed")
    
    # Create and run background task
    task = asyncio.create_task(background_task())
    await task

async def test_reset_vector_store():
    """Test resetting vector store"""
    logger.info("Testing vector store reset")
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        try:
            response = await client.post("http://localhost:8001/reset-vector-store")
            logger.info(f"Reset response: {response.status_code}")
            logger.info(f"Reset result: {response.json()}")
            return True
        except Exception as e:
            logger.error(f"Failed to reset vector store: {e}")
            return False

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("REINDEXING DEBUG TESTS")
    print("="*60)
    
    # Test 1: Single file
    print("\n[TEST 1] Single file indexing")
    print("-"*40)
    await test_single_file_index()
    await asyncio.sleep(2)
    
    # Test 2: Reset vector store
    print("\n[TEST 2] Reset vector store")
    print("-"*40)
    await test_reset_vector_store()
    await asyncio.sleep(2)
    
    # Test 3: Multiple files sequential
    print("\n[TEST 3] Multiple files sequential")
    print("-"*40)
    await test_multiple_files_sequential()
    await asyncio.sleep(2)
    
    # Test 4: Multiple files in background
    print("\n[TEST 4] Multiple files background task")
    print("-"*40)
    await test_multiple_files_background()
    
    print("\n" + "="*60)
    print("TESTS COMPLETED")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())