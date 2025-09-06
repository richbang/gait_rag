#!/usr/bin/env python
"""
Direct test of embedding service
"""

import asyncio
import sys
sys.path.append('/data1/home/ict12/Kmong/medical_gait_rag')

from src.infrastructure.embedding import JinaEmbeddingService

async def test_embedding():
    """Test embedding service directly"""
    print("Testing Jina Embedding Service directly...")
    
    # Initialize service
    service = JinaEmbeddingService(
        model_name="jinaai/jina-embeddings-v4",
        device="cuda:0",  # Using mapped GPU
        batch_size=8
    )
    
    try:
        # Test single text embedding
        print("\n1. Testing single text embedding...")
        text = "What is the average gait speed for stroke patients?"
        embedding = await service.embed_query(text)
        print(f"   Type: {type(embedding)}")
        print(f"   Shape: {embedding.shape if hasattr(embedding, 'shape') else 'N/A'}")
        print(f"   Dimension: {len(embedding) if hasattr(embedding, '__len__') else 'N/A'}")
        print("   ✓ Single text embedding successful")
        
        # Test batch embedding
        print("\n2. Testing batch embedding...")
        texts = [
            "Gait speed in stroke patients",
            "Balance assessment methods",
            "Parkinson's disease walking patterns"
        ]
        embeddings = await service.embed_batch(texts)
        print(f"   Number of embeddings: {len(embeddings)}")
        print(f"   First embedding type: {type(embeddings[0])}")
        print(f"   First embedding shape: {embeddings[0].shape if hasattr(embeddings[0], 'shape') else 'N/A'}")
        print("   ✓ Batch embedding successful")
        
        print("\n✓ All embedding tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_embedding())
    sys.exit(0 if success else 1)