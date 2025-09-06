#!/usr/bin/env python3
import requests
import json

# 1. 로그인
login_data = {
    "username": "admin",
    "password": "admin12345"
}

response = requests.post("http://localhost:8003/api/v1/auth/login", data=login_data)
print(f"Login status: {response.status_code}")

if response.status_code == 200:
    token = response.json()["access_token"]
    print("Login successful")
    
    # 2. Get documents
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("http://localhost:8003/api/v1/rag/documents", headers=headers)
    print(f"\nDocuments API status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total documents: {data.get('total', 0)}")
        docs = data.get('documents', [])
        print(f"Documents array length: {len(docs)}")
        
        # Show first 5 documents
        for i, doc in enumerate(docs[:5], 1):
            print(f"{i}. {doc.get('file_name')} - {doc.get('chunks')} chunks")
    else:
        print(f"Error: {response.text}")
    
    # 3. Get stats
    response = requests.get("http://localhost:8003/api/v1/rag/stats", headers=headers)
    print(f"\nStats API status: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"Stats - total_documents: {stats.get('total_documents')}")
        print(f"Stats - total_chunks: {stats.get('total_chunks')}")
        print(f"Stats - documents list length: {len(stats.get('documents', []))}")
else:
    print(f"Login failed: {response.text}")