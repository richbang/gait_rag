#!/usr/bin/env python
"""
API Server - Clean Architecture Version
"""

import uvicorn
import argparse
from src.presentation import create_app
from src.infrastructure.config import get_settings


def main():
    """Main entry point for API server"""
    
    parser = argparse.ArgumentParser(description="Medical Gait Analysis RAG API Server")
    
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host address (default from config)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port number (default from config)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes (default from config)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Get settings
    settings = get_settings()
    
    # Override with command line args
    host = args.host or settings.api_host
    port = args.port or settings.api_port
    workers = args.workers or settings.api_workers
    
    # Create app
    app = create_app()
    
    print("=" * 60)
    print("Medical Gait Analysis RAG - API Server")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Workers: {workers}")
    print(f"Debug: {args.debug or settings.debug}")
    print(f"Reload: {args.reload}")
    print("-" * 60)
    
    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers if not args.reload else 1,
        reload=args.reload,
        log_level="debug" if args.debug else "info"
    )


if __name__ == "__main__":
    main()