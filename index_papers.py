#!/usr/bin/env python
"""
Document Indexing CLI - Clean Architecture Version
"""

import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime

from src.container import get_container
from src.application import IndexDirectoryRequest
from src.infrastructure.config import Settings


async def main():
    """Main entry point for indexing documents"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Index medical gait analysis papers into RAG system"
    )
    
    parser.add_argument(
        "--directory", "-d",
        type=str,
        default="data",
        help="Directory containing PDF files (default: data)"
    )
    
    parser.add_argument(
        "--max-files", "-m",
        type=int,
        default=None,
        help="Maximum number of PDFs to process (default: all)"
    )
    
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset collection before indexing"
    )
    
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device for embeddings (e.g., cuda:0, cuda:5, cpu)"
    )
    
    parser.add_argument(
        "--collection",
        type=str,
        default="gait_papers",
        help="ChromaDB collection name (default: gait_papers)"
    )
    
    args = parser.parse_args()
    
    # Validate directory
    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory '{directory}' not found")
        sys.exit(1)
    
    # Create custom settings if needed
    settings_overrides = {}
    if args.device:
        settings_overrides["embedding_device"] = args.device
    if args.collection:
        settings_overrides["chroma_collection_name"] = args.collection
    
    # Initialize container with custom settings
    if settings_overrides:
        settings = Settings(**settings_overrides)
        from src.container import Container
        container = Container(settings)
    else:
        container = get_container()
    
    # Print configuration
    print("=" * 60)
    print("Medical Gait Analysis RAG - Document Indexing")
    print("=" * 60)
    print(f"Directory: {args.directory}")
    print(f"Max files: {args.max_files or 'all'}")
    print(f"Reset collection: {args.reset}")
    print(f"Device: {container.settings.embedding_device}")
    print(f"Collection: {container.settings.chroma_collection_name}")
    print("-" * 60)
    
    # Reset collection if requested
    if args.reset:
        print("\nResetting collection...")
        container.reset_vector_store()
    
    # Get initial statistics
    print("\nGetting initial statistics...")
    initial_stats = await container.get_statistics_use_case.execute()
    print(f"Initial collection: {initial_stats.total_documents} documents, "
          f"{initial_stats.total_chunks} chunks")
    
    # Index directory
    print(f"\nIndexing documents from {args.directory}...")
    start_time = datetime.now()
    
    request = IndexDirectoryRequest(
        directory_path=str(directory),
        max_files=args.max_files,
        recursive=True,
        force_reindex=False
    )
    
    response = await container.index_directory_use_case.execute(request)
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    # Print results
    print("\n" + "=" * 60)
    print("Indexing Results")
    print("=" * 60)
    print(f"Total files: {response.total_files}")
    print(f"Success: {response.success_count}")
    print(f"Failed: {response.failed_count}")
    print(f"Total chunks created: {response.total_chunks_created}")
    print(f"Processing time: {processing_time:.2f} seconds")
    
    if response.success_count > 0:
        print(f"Average time per file: {processing_time/response.success_count:.2f} seconds")
    
    if response.failed_files:
        print(f"\nFailed files:")
        for file in response.failed_files[:10]:
            print(f"  - {file}")
        if len(response.failed_files) > 10:
            print(f"  ... and {len(response.failed_files) - 10} more")
    
    # Get final statistics
    final_stats = await container.get_statistics_use_case.execute()
    print(f"\nFinal collection: {final_stats.total_documents} documents, "
          f"{final_stats.total_chunks} chunks")
    print(f"  Text chunks: {final_stats.text_chunks}")
    print(f"  Table chunks: {final_stats.table_chunks}")
    print(f"  Chunks with gait parameters: {final_stats.chunks_with_gait_params}")
    
    # Show sample indexed documents
    if final_stats.documents:
        print(f"\nSample indexed documents:")
        for doc in final_stats.documents[:5]:
            print(f"  - {doc}")
        if len(final_stats.documents) > 5:
            print(f"  ... and {len(final_stats.documents) - 5} more")
    
    print("\nIndexing complete!")
    print("\nNext steps:")
    print("1. Run API server: python api_v2.py")
    print("2. Test search: python test_search.py")
    print("3. Run validation: python validate_rag.py")


if __name__ == "__main__":
    asyncio.run(main())