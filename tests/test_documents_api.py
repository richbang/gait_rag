#!/usr/bin/env python3
"""
Test documents API endpoint
"""

import httpx
import asyncio
import json

async def test_documents_api():
    # Login first
    async with httpx.AsyncClient() as client:
        # Login
        response = await client.post(
            "http://localhost:8003/api/v1/auth/login",
            data={"username": "admin", "password": "admin12345"}
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            return
        
        token = response.json()["access_token"]
        print(f"Login successful, token obtained")
        
        # Get documents
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            "http://localhost:8003/api/v1/rag/documents",
            headers=headers
        )
        
        print(f"Documents API status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total documents: {data.get('total', 0)}")
            print(f"Documents list length: {len(data.get('documents', []))}")
            
            # Show first 5 documents
            for i, doc in enumerate(data.get('documents', [])[:5]):
                print(f"{i+1}. {doc.get('file_name')} - {doc.get('chunks')} chunks")
        else:
            print(f"Error: {response.text}")
        
        # Also check stats
        response = await client.get(
            "http://localhost:8003/api/v1/rag/stats",
            headers=headers
        )
        
        print(f"\nStats API status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"Total documents in stats: {stats.get('total_documents', 0)}")
            print(f"Total chunks in stats: {stats.get('total_chunks', 0)}")

if __name__ == "__main__":
    asyncio.run(test_documents_api())