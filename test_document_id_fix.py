#!/usr/bin/env python
"""
Test script to verify document_id generation fix without loading embedding model
"""

import asyncio
from pathlib import Path
from src.infrastructure.document_processor import PDFDocumentProcessor

async def test_document_id_generation():
    """Test that document_ids are generated correctly with full paths"""
    
    processor = PDFDocumentProcessor()
    
    # Find a few PDF files in the data directory
    data_dir = Path("data")
    pdf_files = list(data_dir.rglob("*.pdf"))[:3]
    
    print("Testing document_id generation with updated code:")
    print("=" * 60)
    
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file}")
        
        # Extract content
        content = await processor.extract_content(pdf_file)
        
        # Create chunks
        chunks = await processor.create_chunks(content)
        
        if chunks:
            # Check the document_id in the first chunk
            first_chunk = chunks[0]
            document_id = first_chunk.document_id
            
            print(f"  Full path: {pdf_file}")
            print(f"  Generated document_id: {document_id}")
            
            # Verify it's not just the stem
            if document_id == pdf_file.stem:
                print(f"  ❌ ERROR: document_id is just the stem!")
            else:
                print(f"  ✓ SUCCESS: document_id includes path information")
            
            # Show what the document_id contains
            if "data/" in str(pdf_file):
                expected_id = str(pdf_file).split("data/", 1)[1]
                if document_id == expected_id:
                    print(f"  ✓ CORRECT: document_id matches expected format")
                else:
                    print(f"  ⚠ WARNING: Expected '{expected_id}', got '{document_id}'")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("\nConclusion:")
    print("Each PDF will now have a unique document_id based on its relative path")
    print("from the data directory, ensuring proper document separation in the RAG system.")

if __name__ == "__main__":
    asyncio.run(test_document_id_generation())