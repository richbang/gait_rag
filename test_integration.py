#!/usr/bin/env python
"""
Integration test for vLLM and RAG engine
"""

import httpx
import asyncio
import json
from datetime import datetime

# API endpoint
API_URL = "http://localhost:8001"

async def test_health_check():
    """Test if API is running"""
    print("=" * 60)
    print("1. Testing API Health Check")
    print("-" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


async def test_statistics():
    """Check indexed documents"""
    print("\n" + "=" * 60)
    print("2. Checking System Statistics")
    print("-" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/statistics")
        if response.status_code == 200:
            stats = response.json()
            print(f"Total Documents: {stats.get('total_documents', 0)}")
            print(f"Total Chunks: {stats.get('total_chunks', 0)}")
            print(f"Text Chunks: {stats.get('text_chunks', 0)}")
            print(f"Table Chunks: {stats.get('table_chunks', 0)}")
            print(f"Chunks with Gait Parameters: {stats.get('chunks_with_gait_params', 0)}")
            
            if stats.get('documents'):
                print(f"\nIndexed Documents ({len(stats['documents'])} total):")
                for doc in stats['documents'][:5]:  # Show first 5
                    print(f"  - {doc}")
            
            return stats.get('total_chunks', 0) > 0
        else:
            print(f"Error: {response.status_code}")
            return False


async def test_search():
    """Test search functionality"""
    print("\n" + "=" * 60)
    print("3. Testing Search Functionality")
    print("-" * 60)
    
    queries = [
        "gait speed in stroke patients",
        "파킨슨 환자의 보행 속도",
        "balance assessment methods"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in queries:
            print(f"\nQuery: '{query}'")
            
            payload = {
                "query": query,
                "limit": 3,
                "min_score": 0.3
            }
            
            response = await client.post(
                f"{API_URL}/search",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  Found {result['total_results']} results")
                
                for i, res in enumerate(result['results'][:2], 1):
                    print(f"\n  Result {i}:")
                    print(f"    Document: {res['document_id']}")
                    print(f"    Page: {res['page_number']}")
                    print(f"    Score: {res['score']:.4f}")
                    print(f"    Has Gait Params: {res['has_gait_params']}")
                    print(f"    Content Preview: {res['content'][:200]}...")
            else:
                print(f"  Error: {response.status_code}")


async def test_qa_with_vllm():
    """Test Q&A with vLLM answer generation"""
    print("\n" + "=" * 60)
    print("4. Testing Q&A with vLLM Integration")
    print("-" * 60)
    
    questions = [
        "What is the average gait speed for stroke patients?",
        "How does Parkinson's disease affect walking patterns?",
        "What are the main gait parameters used in clinical assessment?"
    ]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for question in questions[:1]:  # Test first question only for speed
            print(f"\nQuestion: '{question}'")
            print("-" * 40)
            
            payload = {
                "query": question,
                "limit": 5,
                "use_vllm": True,  # Enable vLLM answer generation
                "min_score": 0.3
            }
            
            print("Searching and generating answer (this may take 30-60 seconds)...")
            start_time = datetime.now()
            
            response = await client.post(
                f"{API_URL}/qa",
                json=payload
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"\nTime taken: {elapsed:.2f} seconds")
                print(f"vLLM Used: {result.get('vllm_used', False)}")
                print(f"Sources Found: {result.get('total_sources', 0)}")
                
                if result.get('answer'):
                    print(f"\nGenerated Answer:")
                    print("=" * 40)
                    print(result['answer'])
                    print("=" * 40)
                else:
                    print("\nNo answer generated (vLLM might be offline)")
                
                if result.get('sources'):
                    print(f"\nTop Sources Used:")
                    for i, source in enumerate(result['sources'][:3], 1):
                        print(f"  {i}. Document: {source['document_id']}, Page: {source['page_number']}, Score: {source['score']:.4f}")
            else:
                print(f"Error: {response.status_code}")
                if response.text:
                    print(f"Details: {response.text}")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MEDICAL GAIT RAG - INTEGRATION TEST")
    print("Testing vLLM and RAG Engine Integration")
    print("=" * 60)
    
    # Check if API is running
    if not await test_health_check():
        print("\n❌ API is not running. Please start it with: python api.py")
        return
    
    # Check if documents are indexed
    has_documents = await test_statistics()
    if not has_documents:
        print("\n⚠️  No documents indexed yet. Consider indexing some PDFs first.")
        print("   Use: python index_papers.py")
    
    # Test search
    if has_documents:
        await test_search()
        
        # Test Q&A with vLLM
        await test_qa_with_vllm()
    
    print("\n" + "=" * 60)
    print("Integration test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())