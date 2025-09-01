#!/usr/bin/env python
"""
Setup script for Medical Gait RAG WebUI
Creates directory structure and initial files
"""

import os
import json
from pathlib import Path

def create_directory_structure():
    """Create the project directory structure."""
    
    # Backend directories
    backend_dirs = [
        "backend/auth",
        "backend/chat",
        "backend/database",
        "backend/core",
        "backend/tests",
    ]
    
    # Frontend directories
    frontend_dirs = [
        "frontend/src/components",
        "frontend/src/pages",
        "frontend/src/api",
        "frontend/src/contexts",
        "frontend/src/types",
        "frontend/src/hooks",
        "frontend/src/utils",
        "frontend/public",
    ]
    
    # Create all directories
    for dir_path in backend_dirs + frontend_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {dir_path}")
    
    # Create __init__.py files for Python packages
    for dir_path in backend_dirs:
        if not dir_path.endswith("tests"):
            init_file = Path(dir_path) / "__init__.py"
            init_file.touch()
            print(f"✓ Created {init_file}")


def create_backend_config():
    """Create backend configuration files."""
    
    # .env file
    env_content = """# Backend Configuration
DATABASE_URL=sqlite:///./gait_rag.db
SECRET_KEY=change-this-secret-key-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# RAG API Configuration
RAG_API_URL=http://localhost:8000

# Redis (Optional)
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=development
"""
    
    with open("backend/.env", "w") as f:
        f.write(env_content)
    print("✓ Created backend/.env")
    
    # Core config.py
    config_content = '''"""Configuration management."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "sqlite:///./gait_rag.db"
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24
    
    # RAG API
    rag_api_url: str = "http://localhost:8000"
    
    # Redis (Optional)
    redis_url: Optional[str] = None
    
    # Application
    app_name: str = "Medical Gait RAG WebUI"
    app_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    
    # CORS
    cors_origins: list = ["http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    """Get cached settings."""
    return Settings()
'''
    
    with open("backend/core/config.py", "w") as f:
        f.write(config_content)
    print("✓ Created backend/core/config.py")


def create_frontend_config():
    """Create frontend configuration files."""
    
    # package.json
    package_json = {
        "name": "medical-gait-rag-frontend",
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "tsc && vite build",
            "preview": "vite preview",
            "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
            "test": "vitest"
        },
        "dependencies": {
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            "react-router-dom": "^6.28.0",
            "axios": "^1.7.9",
            "zustand": "^5.0.2",
            "clsx": "^2.1.1"
        },
        "devDependencies": {
            "@types/react": "^18.3.12",
            "@types/react-dom": "^18.3.1",
            "@typescript-eslint/eslint-plugin": "^8.17.0",
            "@typescript-eslint/parser": "^8.17.0",
            "@vitejs/plugin-react": "^4.3.4",
            "autoprefixer": "^10.4.20",
            "eslint": "^9.15.0",
            "eslint-plugin-react-hooks": "^5.0.0",
            "eslint-plugin-react-refresh": "^0.4.14",
            "postcss": "^8.4.49",
            "tailwindcss": "^3.4.16",
            "typescript": "^5.6.3",
            "vite": "^5.4.11",
            "vitest": "^2.1.8"
        }
    }
    
    with open("frontend/package.json", "w") as f:
        json.dump(package_json, f, indent=2)
    print("✓ Created frontend/package.json")
    
    # vite.config.ts
    vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      }
    }
  },
  build: {
    sourcemap: true,
    chunkSizeWarningLimit: 1000,
  }
})
"""
    
    with open("frontend/vite.config.ts", "w") as f:
        f.write(vite_config)
    print("✓ Created frontend/vite.config.ts")
    
    # tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "module": "ESNext",
            "skipLibCheck": True,
            "moduleResolution": "bundler",
            "allowImportingTsExtensions": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
            "strict": True,
            "noUnusedLocals": True,
            "noUnusedParameters": True,
            "noFallthroughCasesInSwitch": True
        },
        "include": ["src"],
        "references": [{"path": "./tsconfig.node.json"}]
    }
    
    with open("frontend/tsconfig.json", "w") as f:
        json.dump(tsconfig, f, indent=2)
    print("✓ Created frontend/tsconfig.json")
    
    # tailwind.config.js
    tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
    
    with open("frontend/tailwind.config.js", "w") as f:
        f.write(tailwind_config)
    print("✓ Created frontend/tailwind.config.js")
    
    # .env
    env_content = """# Frontend Configuration
VITE_API_URL=http://localhost:8001
"""
    
    with open("frontend/.env", "w") as f:
        f.write(env_content)
    print("✓ Created frontend/.env")


def create_initial_files():
    """Create initial starter files."""
    
    # Backend main.py
    main_content = '''"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from core.config import get_settings
from core.logging import setup_logging

settings = get_settings()

# Setup logging
setup_logging(settings.log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    logger.info("Shutting down application")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Medical Gait RAG WebUI API",
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/api/v1/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.environment == "development"
    )
'''
    
    with open("backend/main.py", "w") as f:
        f.write(main_content)
    print("✓ Created backend/main.py")
    
    # Frontend App.tsx
    app_content = '''import React from 'react'
import './index.css'

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold text-gray-800">
          Medical Gait RAG WebUI
        </h1>
        <p className="mt-4 text-gray-600">
          Welcome to the Medical Gait Analysis RAG System
        </p>
      </div>
    </div>
  )
}

export default App
'''
    
    with open("frontend/src/App.tsx", "w") as f:
        f.write(app_content)
    print("✓ Created frontend/src/App.tsx")
    
    # Frontend main.tsx
    main_tsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
'''
    
    with open("frontend/src/main.tsx", "w") as f:
        f.write(main_tsx)
    print("✓ Created frontend/src/main.tsx")
    
    # Frontend index.css
    index_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;
'''
    
    with open("frontend/src/index.css", "w") as f:
        f.write(index_css)
    print("✓ Created frontend/src/index.css")
    
    # Frontend index.html
    index_html = '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Medical Gait RAG</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''
    
    with open("frontend/index.html", "w") as f:
        f.write(index_html)
    print("✓ Created frontend/index.html")


def create_readme():
    """Create README for WebUI."""
    
    readme_content = '''# Medical Gait RAG WebUI

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements-web.txt
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## Development

See documentation:
- [Implementation Guide](../WEBUI_IMPLEMENTATION.md)
- [Code Guidelines](../CODE_GUIDELINES.md)
- [Architecture](../WEBUI_ARCHITECTURE.md)
'''
    
    with open("README_WEBUI.md", "w") as f:
        f.write(readme_content)
    print("✓ Created README_WEBUI.md")


def main():
    """Run all setup functions."""
    print("\n🚀 Setting up Medical Gait RAG WebUI\n")
    
    create_directory_structure()
    print()
    
    create_backend_config()
    print()
    
    create_frontend_config()
    print()
    
    create_initial_files()
    print()
    
    create_readme()
    print()
    
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Backend: cd backend && pip install -r requirements-web.txt")
    print("2. Frontend: cd frontend && npm install")
    print("3. Start development servers")
    print("\nHappy coding! 🎉")


if __name__ == "__main__":
    main()