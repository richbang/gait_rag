#!/usr/bin/env python
"""
Simple script to reset the vector store
"""
import chromadb
from chromadb.config import Settings as ChromaSettings

# Initialize ChromaDB client with absolute path
import os
chroma_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
client = chromadb.PersistentClient(
    path=chroma_path,
    settings=ChromaSettings(anonymized_telemetry=False)
)

# Delete the collection if it exists
collection_name = "gait_papers"
try:
    client.delete_collection(collection_name)
    print(f"Deleted collection: {collection_name}")
except:
    print(f"Collection {collection_name} doesn't exist")

# Create new collection
collection = client.create_collection(
    name=collection_name,
    metadata={"hnsw:space": "cosine"}
)
print(f"Created new collection: {collection_name}")
print(f"Collection count after reset: {collection.count()}")
print(f"ChromaDB path: {chroma_path}")
print("Vector store reset successfully!")