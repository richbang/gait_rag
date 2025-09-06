# Medical Gait RAG System - 전체 아키텍처

## 시스템 개요

Medical Gait RAG는 의료 보행 분석 문서를 처리하고 검색하는 3-tier 아키텍처 시스템입니다.

## 서비스 구성

### 1. Frontend Service (Port 3000)
- **기술스택**: React 18, TypeScript, Tailwind CSS
- **주요파일**: `frontend/src/App.tsx` (1145 lines), `AdminPage.tsx` (1424 lines)
- **역할**: 사용자 인터페이스, 실시간 채팅, 관리자 패널

### 2. WebUI Backend (Port 8003)
- **기술스택**: FastAPI, SQLAlchemy, SQLite
- **주요파일**: 
  - `backend/main.py` - 서버 진입점
  - `backend/chat/router.py` (359 lines) - 채팅 엔드포인트
  - `backend/rag/routes.py` (657 lines) - RAG 관리 API
- **역할**: 사용자 인증, 대화 관리, RAG 프록시

### 3. RAG API Service (Port 8001)
- **기술스택**: FastAPI, Dependency Injection
- **주요파일**:
  - `api.py` - RAG 서버 진입점
  - `src/presentation/routes.py` (434 lines) - RAG 엔드포인트
- **역할**: 문서 인덱싱, 벡터 검색, 답변 생성

### 4. vLLM Server (Port 8000)
- **모델**: NVIDIA Nemotron-12B (131,072 token context)
- **GPU**: 2x RTX A5000 (Tensor Parallel)
- **역할**: 언어 모델 추론

### 5. 데이터 저장소
- **ChromaDB**: 벡터 데이터베이스 (`./chroma_db/`)
- **SQLite**: 사용자/대화 데이터 (`./gait_rag.db`)
- **PDF Storage**: 원본 문서 (`./data/`)

## 네트워크 플로우

```
사용자 → Frontend(:3000) → WebUI Backend(:8003) → RAG API(:8001)
                                                        ↓
                                                  vLLM Server(:8000)
                                                        ↓
                                                  ChromaDB + Nemotron
```

## GPU 할당

- **GPU 0,1**: vLLM Nemotron (Tensor Parallel)
- **GPU 2 (CUDA_VISIBLE_DEVICES=2)**: Jina Embeddings v4


## 프로세스 시작 순서

1. vLLM Server 시작 (`start_vllm_nemotron.sh`)
2. RAG API 시작 (`python api.py`)
3. WebUI Backend 시작 (`cd backend && uvicorn main:app`)
4. Frontend 시작 (`cd frontend && npm run dev`)

## 주요 포트 정리

| 서비스 | 포트 | 용도 |
|--------|------|------|
| Frontend | 3000 | 웹 UI |
| WebUI Backend | 8003 | API Gateway |
| RAG API | 8001 | RAG Core |
| vLLM | 8000 | LLM Inference |

## 환경 변수 (.env)

```bash
# GPU 설정
CUDA_VISIBLE_DEVICES=2  # Embedding GPU
VLLM_CUDA_VISIBLE_DEVICES=0,1  # LLM GPUs

# 모델 설정
VLLM_MAX_TOKENS=8192
VLLM_CONTEXT_LENGTH=131072
EMBEDDING_BATCH_SIZE=8

# 문서 처리
CHUNK_SIZE=500
CHUNK_OVERLAP=100
```