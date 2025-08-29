#!/usr/bin/env python3
"""
Test script for vLLM integration with RAG system
"""

import asyncio
import httpx
import json
from typing import Dict, Any


async def test_search_endpoint():
    """Test basic search without vLLM"""
    url = "http://localhost:8000/search"
    
    payload = {
        "query": "gait parameters in stroke patients",
        "limit": 3
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Search endpoint working")
            print(f"Found {result['total_results']} results")
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            return False


async def test_qa_without_vllm():
    """Test QA endpoint without vLLM (retrieval only)"""
    url = "http://localhost:8000/qa"
    
    payload = {
        "query": "What are the main gait parameters affected in stroke patients?",
        "limit": 3,
        "use_vllm": False  # Disable vLLM
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ QA endpoint working (retrieval only)")
            print(f"Found {len(result['sources'])} source documents")
            print(f"vLLM used: {result['vllm_used']}")
            return True
        else:
            print(f"❌ QA retrieval failed: {response.status_code}")
            return False


async def test_qa_with_vllm():
    """Test QA endpoint with vLLM answer generation"""
    url = "http://localhost:8000/qa"
    
    payload = {
        "query": "What are the main gait parameters affected in stroke patients?",
        "limit": 3,
        "use_vllm": True  # Enable vLLM
    }
    
    print("\n🔄 Testing with vLLM (this may take a moment)...")
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("answer"):
                    print("✅ QA with vLLM working!")
                    print(f"\nQuestion: {result['query']}")
                    print(f"\nAnswer: {result['answer'][:200]}..." if len(result['answer']) > 200 else f"\nAnswer: {result['answer']}")
                    print(f"\nSources used: {len(result['sources'])}")
                    print(f"vLLM used: {result['vllm_used']}")
                    return True
                else:
                    print("⚠️  QA endpoint works but vLLM server may not be running")
                    print("To start vLLM server, run: ./start_vllm_server.sh")
                    return False
            else:
                print(f"❌ QA with vLLM failed: {response.status_code}")
                return False
                
        except httpx.TimeoutException:
            print("⏱️  Request timed out - vLLM server may not be running")
            print("To start vLLM server, run: ./start_vllm_server.sh")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_health_endpoint():
    """Test health check endpoint"""
    url = "http://localhost:8000/health"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health check: {result['status']}")
            print(f"Version: {result['version']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Medical Gait RAG System with vLLM Integration")
    print("=" * 60)
    
    print("\n1. Testing health endpoint...")
    await test_health_endpoint()
    
    print("\n2. Testing search endpoint...")
    await test_search_endpoint()
    
    print("\n3. Testing QA endpoint without vLLM...")
    await test_qa_without_vllm()
    
    print("\n4. Testing QA endpoint with vLLM...")
    await test_qa_with_vllm()
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("\nNote: If vLLM tests fail, ensure:")
    print("1. vLLM server is running: ./start_vllm_server.sh")
    print("2. USE_VLLM=true in .env file")
    print("3. vLLM server is accessible at the configured URL")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())