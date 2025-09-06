# Medical Gait RAG System - 문서 목록

## 시스템 문서

이 디렉토리는 Medical Gait RAG System의 전체 아키텍처와 구현을 설명하는 상세 문서를 포함합니다.

## 문서 구조

1. **[01_ARCHITECTURE.md](01_ARCHITECTURE.md)**
   - 전체 시스템 아키텍처
   - 서비스 구성 (Frontend, Backend, RAG, vLLM)
   - GPU 할당 및 포트 설정
   - 환경 변수 설정

2. **[02_RAG_CORE_SYSTEM.md](02_RAG_CORE_SYSTEM.md)**
   - src/ 디렉토리 상세
   - Domain, Infrastructure, Application 계층
   - 보행 파라미터 처리 로직
   - ChromaDB 및 임베딩 시스템

3. **[03_BACKEND_API.md](03_BACKEND_API.md)**
   - backend/ 디렉토리 상세
   - 인증 시스템 (JWT)
   - 채팅 및 WebSocket
   - RAG 관리 API

4. **[04_FRONTEND.md](04_FRONTEND.md)**
   - React/TypeScript 구조
   - App.tsx 및 AdminPage.tsx
   - 상태 관리 및 API 통신
   - UI 컴포넌트

5. **[05_DATA_FLOW.md](05_DATA_FLOW.md)**
   - 문서 인덱싱 플로우
   - 질의응답 처리 과정
   - 보행 파라미터 통계 플로우
   - WebSocket 실시간 통신

## 보행 파라미터 처리 핵심

### 감지 키워드
- **영어**: speed, velocity, cadence, step length, stride length, walking speed, gait speed
- **한글**: 속도, 보행, 보폭, 걸음, 보행속도

### 처리 과정
1. PDF 문서에서 텍스트 추출
2. 청크 단위로 키워드 검색
3. `has_gait_params` 플래그 설정
4. ChromaDB에 메타데이터로 저장
5. 통계 API에서 집계하여 표시

## 주요 파일 크기

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| backend/rag/routes.py | 657 | RAG 관리 API |
| src/presentation/routes.py | 434 | RAG 엔드포인트 |
| src/infrastructure/document_processor.py | 362 | PDF 처리 |
| backend/chat/router.py | 359 | 채팅 라우터 |
| src/infrastructure/vector_store.py | 314 | ChromaDB 관리 |
| frontend/src/AdminPage.tsx | 1424 | 관리자 패널 |
| frontend/src/App.tsx | 1145 | 메인 채팅 UI |

## 시스템 요구사항

- **GPU**: 2x NVIDIA RTX A5000 (24GB VRAM)
- **Python**: 3.10+
- **Node.js**: 18+
- **컨텍스트**: Nemotron-12B (131,072 토큰)

## 빠른 참조

### 서비스 포트
- Frontend: 3000
- WebUI Backend: 8003
- RAG API: 8001
- vLLM Server: 8000

### 데이터 저장소
- ChromaDB: `./chroma_db/`
- SQLite: `./gait_rag.db`
- PDF 문서: `./data/`

### 기본 계정
- 관리자: admin / admin12345
- 데모: demouser / demo12345