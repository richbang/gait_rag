#!/usr/bin/env python3
"""
Test the actual reindex endpoint through WebUI backend
"""

import httpx
import asyncio
import json
from loguru import logger

# Admin credentials
USERNAME = "admin"
PASSWORD = "admin12345"

async def login():
    """Login and get access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8003/api/v1/auth/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        if response.status_code == 200:
            result = response.json()
            return result["access_token"]
        else:
            logger.error(f"Login failed: {response.status_code}")
            return None

async def test_reindex(token: str):
    """Test the reindex endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        logger.info("Calling reindex endpoint...")
        response = await client.post(
            "http://localhost:8003/api/v1/rag/reindex",
            headers=headers
        )
        
        logger.info(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            logger.error(f"Reindex failed: {response.text}")
            return False

async def monitor_progress(token: str):
    """Monitor indexing progress for a short time"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        for i in range(10):  # Check 10 times
            await asyncio.sleep(2)  # Wait 2 seconds between checks
            
            # Get statistics
            response = await client.get(
                "http://localhost:8003/api/v1/rag/stats",
                headers=headers
            )
            
            if response.status_code == 200:
                stats = response.json()
                logger.info(f"Stats check {i+1}: Total chunks = {stats.get('total_chunks', 0)}, Documents = {stats.get('total_documents', 0)}")

async def main():
    logger.info("Starting reindex endpoint test")
    
    # Login first
    token = await login()
    if not token:
        logger.error("Could not login")
        return
    
    logger.info("Login successful")
    
    # Test reindex
    success = await test_reindex(token)
    
    if success:
        logger.info("Reindex endpoint called successfully")
        # Monitor progress
        await monitor_progress(token)
    else:
        logger.error("Reindex endpoint failed")

if __name__ == "__main__":
    asyncio.run(main())