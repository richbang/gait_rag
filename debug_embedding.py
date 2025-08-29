#!/usr/bin/env python
"""
Debug embedding service
"""

import sys
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import torch
import numpy as np
from transformers import AutoModel

print("=" * 60)
print("DEBUGGING JINA EMBEDDING MODEL OUTPUT")
print("=" * 60)

# Load model
print("\n1. Loading model...")
model = AutoModel.from_pretrained(
    "jinaai/jina-embeddings-v4",
    trust_remote_code=True,
    torch_dtype=torch.float16
)

print(f"   Model device before: {next(model.parameters()).device}")
model.to("cuda:0")
print(f"   Model device after: {next(model.parameters()).device}")
model.eval()
print("   ✓ Model loaded")

# Test single text
print("\n2. Testing single text encoding...")
text = "What is gait speed?"

with torch.no_grad():
    result = model.encode_text(
        texts=[text],
        task="retrieval", 
        prompt_name="query"
    )
    
print(f"   Output type: {type(result)}")
print(f"   Has .cpu(): {hasattr(result, 'cpu')}")
print(f"   Has .detach(): {hasattr(result, 'detach')}")
print(f"   Has .numpy(): {hasattr(result, 'numpy')}")

if hasattr(result, 'device'):
    print(f"   Device: {result.device}")
if hasattr(result, 'shape'):
    print(f"   Shape: {result.shape}")
if hasattr(result, 'dtype'):
    print(f"   Dtype: {result.dtype}")

# Try conversions
print("\n3. Testing conversions...")

# Method 1: Direct
try:
    np_array = result.numpy()
    print(f"   ✓ Direct .numpy() works")
except Exception as e:
    print(f"   ✗ Direct .numpy() failed: {e}")

# Method 2: CPU first
try:
    np_array = result.cpu().numpy()
    print(f"   ✓ .cpu().numpy() works")
except Exception as e:
    print(f"   ✗ .cpu().numpy() failed: {e}")

# Method 3: Detach + CPU
try:
    np_array = result.detach().cpu().numpy()
    print(f"   ✓ .detach().cpu().numpy() works")
except Exception as e:
    print(f"   ✗ .detach().cpu().numpy() failed: {e}")

# Method 4: Our current approach
print("\n4. Testing our approach...")
try:
    embeddings = result
    if hasattr(embeddings, 'cpu'):
        embeddings = embeddings.cpu()
        print(f"   After .cpu(): type={type(embeddings)}, device={embeddings.device if hasattr(embeddings, 'device') else 'N/A'}")
    
    if hasattr(embeddings, 'detach'):  
        embeddings = embeddings.detach()
        print(f"   After .detach(): type={type(embeddings)}")
    
    if hasattr(embeddings, 'numpy'):
        embeddings = embeddings.numpy()
        print(f"   After .numpy(): type={type(embeddings)}, shape={embeddings.shape}")
    
    embeddings = embeddings.astype(np.float32)
    print(f"   ✓ Final conversion successful: shape={embeddings.shape}, dtype={embeddings.dtype}")
    
except Exception as e:
    print(f"   ✗ Our approach failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)