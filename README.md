# Medical Gait Analysis RAG System

의료 보행 분석 문서를 위한 고성능 RAG(Retrieval-Augmented Generation) 시스템

## Quick Start

```bash
# 모든 서비스 시작
./start_all_services.sh

# 브라우저에서 접속
http://localhost:3000

# 로그인 정보
Username: demouser
Password: demo12345
```

## System Requirements

- **GPU**: 2x NVIDIA RTX A5000 (24GB VRAM)
- **OS**: Ubuntu 20.04+
- **Python**: 3.10+
- **Node.js**: 18+

## Architecture

```
Frontend (React:3000) → WebUI Backend (FastAPI:8003) → RAG API (FastAPI:8001)
                                                              ↓
                                                     vLLM Server (:8000)
                                                              ↓
                                              ChromaDB + Nemotron-12B (131K context)
```

## Key Features

- **LLM**: NVIDIA Nemotron-12B with 131,072 token context
- **Vector DB**: ChromaDB with Jina Embeddings v4
- **Chat Modes**: RAG mode (@) or Direct LLM mode
- **Admin Panel**: User and document management
- **Real-time**: WebSocket support for live updates

## Installation

```bash
# 1. Clone repository
git clone git@github.com:richbang/gait_rag.git
cd gait_rag

# 2. Setup Python environment
conda create -n gait_rag python=3.10
conda activate gait_rag
pip install -r requirements.txt

# 3. Setup frontend
cd frontend && npm install && cd ..

# 4. Configure environment
cp .env.example .env
# Edit .env with your GPU settings

# 5. Initialize database
cd backend && python init_db.py && cd ..

# 6. Start services
./start_all_services.sh
```

## Usage

### RAG Mode (Document Search)
```
@파킨슨병 환자의 보행 특징은?
```

### Direct Mode (Pure LLM)
```
정상 보행 주기의 단계를 설명해주세요
```

## API Endpoints

- **RAG API** (8001): `/qa`, `/index/document`, `/statistics`
- **WebUI Backend** (8003): `/api/auth/login`, `/api/chat/messages`
- **Admin API** (8003): `/api/v1/admin/*`, `/api/v1/rag/*`

## Project Structure

```
medical_gait_rag/
├── src/                 # Core RAG logic
├── backend/            # WebUI backend
├── frontend/           # React frontend
├── data/              # PDF documents
├── tests/             # Test files
└── docs/              # Additional documentation
```

## Documentation

Detailed documentation available in `docs/` directory:
- [Setup Guide](docs/SETUP_GUIDE.md)
- [WebUI Guide](docs/WEBUI_GUIDE.md)
- [vLLM Integration](docs/VLLM_INTEGRATION.md)

## License

Proprietary - All Rights Reserved

## Support

For issues or questions, please open an issue on GitHub.