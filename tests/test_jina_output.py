#!/usr/bin/env python
"""
Test Jina model output type
"""

import torch
from transformers import AutoModel

# Initialize model
print("Loading model...")
model = AutoModel.from_pretrained(
    "jinaai/jina-embeddings-v4", 
    trust_remote_code=True, 
    torch_dtype=torch.float16
)
model.to("cuda:0")
model.eval()

# Test encode_text output
print("\nTesting encode_text output...")
with torch.no_grad():
    embeddings = model.encode_text(
        texts=["Test query"],
        task="retrieval",
        prompt_name="query"
    )
    
    print(f"Type: {type(embeddings)}")
    print(f"Is tensor: {torch.is_tensor(embeddings)}")
    
    if torch.is_tensor(embeddings):
        print(f"Device: {embeddings.device}")
        print(f"Shape: {embeddings.shape}")
        print(f"Dtype: {embeddings.dtype}")
        
        # Try conversion
        try:
            numpy_arr = embeddings.cpu().numpy()
            print(f"✓ Direct .cpu().numpy() works")
        except:
            print(f"✗ Direct .cpu().numpy() failed")
            
        try:
            numpy_arr = embeddings.detach().cpu().numpy()
            print(f"✓ .detach().cpu().numpy() works")
        except:
            print(f"✗ .detach().cpu().numpy() failed")