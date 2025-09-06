# Medical Gait Analysis RAG System

의료 보행 분석 문서를 위한 고성능 RAG(Retrieval-Augmented Generation) 시스템

## Quick Start

```bash
# 모든 서비스 시작
./start_all_services.sh

# 브라우저에서 접속
http://localhost:3000
```

## System Requirements

- **Hardware**: 2x NVIDIA RTX A5000 (24GB VRAM) or equivalent
- **OS**: Ubuntu 20.04+
- **Python**: 3.10+
- **Disk**: 50GB+ free space

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐
│   Frontend  │────▶│ WebUI Backend│────▶│  RAG API  │
│  (React)    │     │  (FastAPI)   │     │ (FastAPI) │
│   :3000     │     │    :8003     │     │   :8001   │
└─────────────┘     └──────────────┘     └───────────┘
                                                │
                                                ▼
                                        ┌───────────────┐
                                        │  vLLM Server  │
                                        │     :8000     │
                                        └───────────────┘
                                                │
                                        ┌───────┴────────┐
                                        │                │
                                  ┌─────▼────┐   ┌──────▼──────┐
                                  │ ChromaDB │   │  Nemotron   │
                                  │          │   │    12B      │
                                  └──────────┘   └─────────────┘
```

## Installation

### 1. Clone Repository
```bash
git clone git@github.com:richbang/gait_rag.git
cd gait_rag
```

### 2. Setup Environment
```bash
# Conda 환경 생성
conda create -n gait_rag python=3.10
conda activate gait_rag

# 패키지 설치
pip install -r requirements.txt
pip install vllm==0.6.4.post1 safetensors
```

### 3. Configure Environment
```bash
# 환경 변수 설정
cp .env.example .env
# Edit .env file with your GPU settings

# 프론트엔드 설정
cd frontend && npm install && cd ..
```

### 4. Start Services
```bash
chmod +x *.sh
./start_all_services.sh
```

## Features

- **LLM Support**: NVIDIA Nemotron-12B with 131K context
- **Smart Retrieval**: ChromaDB + Jina Embeddings v4
- **Dual Mode Chat**: RAG mode (@) or Direct mode
- **Authentication**: User management system
- **Real-time Interface**: React + WebSocket
- **Multi-language**: Korean, English support

## Project Structure

```
medical_gait_rag/
├── Startup Scripts
│   ├── start_all_services.sh    # Start everything
│   ├── start_vllm_seed.sh       # Seed-OSS model
│   ├── start_vllm_nemotron.sh   # Nemotron model
│   └── stop_all_services.sh     # Stop everything
│
├── Core Services
│   ├── api.py                   # RAG API server
│   ├── index_papers.py          # Document indexing
│   └── set_model.sh             # Model switcher
│
├── Application Code
│   ├── src/                     # Core RAG logic
│   ├── backend/                 # WebUI backend
│   ├── frontend/                # React frontend
│   └── webui/                   # Alternative UI
│
└── Data & Logs
    ├── data/                    # Documents
    ├── logs/                    # Service logs
    └── tests/                   # Test files
```

## Usage

### Web Interface

1. **Start services**: `./start_all_services.sh`
2. **Open browser**: http://localhost:3000
3. **Login**: 
   - Username: `demouser`
   - Password: `demo12345`

### Chat Modes

#### RAG Mode (Document Search)
```
@파킨슨병 환자의 보행 특징은?
```

#### Direct Mode (Pure LLM)
```
정상 보행 주기의 단계를 설명해주세요
```

## Configuration

### Environment Variables (.env)
```env
DATABASE_URL=sqlite:///./medical_gait.db
VLLM_MODEL=nemotron-nano-12b
VLLM_MAX_TOKENS=8192
VLLM_TEMPERATURE=0.6
```

### Model Settings
Edit `src/infrastructure/config.py` to change default model

## API Endpoints

### RAG API (8001)
- `POST /qa` - Question answering
- `GET /health` - Health check

### WebUI Backend (8003)
- `POST /api/auth/login` - User login
- `POST /api/chat/messages` - Send message
- `GET /api/chat/conversations` - Get history

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CUDA OOM | Reduce `--max-num-seqs` in startup scripts |
| Port in use | Run `./stop_all_services.sh` first |
| Model not loading | Check disk space (need 50GB+) |
| No response | Check logs in `logs/` directory |

## Performance

- **Response Time**: < 2s (cached) / 5-10s (RAG search)
- **Context Window**: 128K-131K tokens
- **Concurrent Users**: 5-8 recommended
- **Memory Usage**: ~22GB per GPU

## Development

```bash
# Run tests
pytest tests/

# View logs
tail -f logs/rag_api.log
tail -f logs/webui_backend.log

# Index new documents
python index_papers.py
```

## License

Proprietary - All Rights Reserved

## Support

For issues or questions, please open an issue on GitHub.