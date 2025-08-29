#!/usr/bin/env python
"""
Simple test to understand Jina v4 output
"""

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import sys
import torch
import numpy as np

# Redirect stdout to capture print from model
class Capturing:
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self
        self.data = []
        return self
    
    def __exit__(self, *args):
        sys.stdout = self._stdout
    
    def write(self, s):
        self.data.append(s)
        self._stdout.write(s)
    
    def flush(self):
        pass

print("=" * 60)
print("Testing Jina v4 encode_text output")
print("=" * 60)

# Import only after setting CUDA
from transformers import AutoModel

print("\n1. Loading model...")
with Capturing():  # Capture loading messages
    model = AutoModel.from_pretrained(
        "jinaai/jina-embeddings-v4",
        trust_remote_code=True,
        torch_dtype=torch.float16
    )
    model.to("cuda:0")
    model.eval()

print("   Model loaded!")

print("\n2. Testing single text encoding...")
text = "Test query"

with torch.no_grad():
    # Capture the encode_text output
    result = model.encode_text(
        texts=[text],
        task="retrieval",
        prompt_name="query"
    )

print(f"\n3. Analyzing output:")
print(f"   Type: {type(result)}")
print(f"   Type name: {type(result).__name__}")

if isinstance(result, list):
    print(f"   List length: {len(result)}")
    if len(result) > 0:
        print(f"   First element type: {type(result[0])}")
        print(f"   First element type name: {type(result[0]).__name__}")
        if hasattr(result[0], 'shape'):
            print(f"   First element shape: {result[0].shape}")
        if hasattr(result[0], 'device'):
            print(f"   First element device: {result[0].device}")
        if hasattr(result[0], 'dtype'):
            print(f"   First element dtype: {result[0].dtype}")

elif torch.is_tensor(result):
    print(f"   Tensor shape: {result.shape}")
    print(f"   Tensor device: {result.device}")
    print(f"   Tensor dtype: {result.dtype}")

elif isinstance(result, np.ndarray):
    print(f"   NumPy shape: {result.shape}")
    print(f"   NumPy dtype: {result.dtype}")

print("\n4. Testing batch encoding...")
texts = ["Query 1", "Query 2", "Query 3"]

with torch.no_grad():
    batch_result = model.encode_text(
        texts=texts,
        task="retrieval",
        prompt_name="query"
    )

print(f"\n   Batch type: {type(batch_result)}")
print(f"   Batch type name: {type(batch_result).__name__}")

if isinstance(batch_result, list):
    print(f"   Batch list length: {len(batch_result)}")
    for i, item in enumerate(batch_result[:2]):  # Check first 2
        print(f"   Item {i} type: {type(item).__name__}")
        if hasattr(item, 'shape'):
            print(f"   Item {i} shape: {item.shape}")

elif hasattr(batch_result, 'shape'):
    print(f"   Batch shape: {batch_result.shape}")

print("\n" + "=" * 60)