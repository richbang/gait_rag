# Medical Gait RAG System - 프로젝트 전체 분석

## 🏗️ 시스템 아키텍처

### 개요
의료 보행 분석을 위한 RAG (Retrieval-Augmented Generation) 시스템으로, 의학 논문과 임상 데이터를 벡터화하여 지능형 질의응답을 제공하는 플랫폼입니다.

### 시스템 구성
```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│                    Port 3000 (Dev)                          │
├─────────────────────────────────────────────────────────────┤
│                  WebUI Backend (FastAPI)                     │
│                       Port 8003                             │
├─────────────────────────────────────────────────────────────┤
│                   RAG Backend (FastAPI)                      │
│                       Port 8001                             │
├─────────────────┬───────────────┬───────────────────────────┤
│   ChromaDB      │  vLLM Server  │     SQLite DB            │
│ (Vector Store)  │   Port 8000   │  (User/Chat Data)        │
└─────────────────┴───────────────┴───────────────────────────┘
```

## 📊 기술 스택 분석

### Backend 기술
| 구성 요소 | 기술 | 버전 | 용도 |
|---------|------|------|------|
| Web Framework | FastAPI | 0.115.5 | 고성능 비동기 API 서버 |
| ORM | SQLAlchemy | 2.0.36 | 데이터베이스 추상화 |
| Vector DB | ChromaDB | 1.0+ | 임베딩 벡터 저장/검색 |
| Embedding | Jina v4 | - | 문서 임베딩 생성 |
| LLM | Seed-OSS-36B | - | 답변 생성 (vLLM 서빙) |
| Authentication | JWT (python-jose) | 3.3.0 | 사용자 인증 |
| Password | passlib + bcrypt | 1.7.4 | 비밀번호 암호화 |
| Logging | Loguru | 0.7.3 | 구조화된 로깅 |
| PDF Processing | PyMuPDF | 1.23+ | PDF 문서 파싱 |

### Frontend 기술
| 구성 요소 | 기술 | 버전 | 용도 |
|---------|------|------|------|
| Framework | React | 19.1.1 | UI 프레임워크 |
| Language | TypeScript | 4.9.5 | 타입 안정성 |
| HTTP Client | Axios | 1.11.0 | API 통신 |
| Build Tool | React Scripts | 5.0.1 | 빌드 및 개발 서버 |
| Styling | TailwindCSS | 4.1.12 | 유틸리티 기반 CSS |

## 🗂️ 프로젝트 구조 분석

### 1. RAG 백엔드 (`src/` - Clean Architecture)
```
src/
├── domain/           # 비즈니스 엔티티
│   ├── entities.py   # Document, DocumentChunk, GaitParameter
│   ├── repositories.py # 저장소 인터페이스
│   └── services.py   # 도메인 서비스
├── application/      # 유스케이스 레이어
│   ├── use_cases.py  # 검색, 인덱싱, QA 유스케이스
│   └── dto.py        # 데이터 전송 객체
├── infrastructure/   # 외부 서비스 구현
│   ├── vector_store.py # ChromaDB 통합
│   ├── embedding.py  # Jina 임베딩
│   ├── vllm_client.py # vLLM 클라이언트
│   └── document_processor.py # PDF 처리
└── presentation/     # API 레이어
    └── routes.py     # FastAPI 엔드포인트
```

### 2. WebUI 백엔드 (`backend/`)
```
backend/
├── auth/            # 인증 모듈
├── chat/            # 채팅 기능
├── database/        # SQLite 데이터베이스
├── core/            # 공통 유틸리티
└── main.py          # 앱 진입점
```

### 3. Frontend (`frontend/`)
```
frontend/src/
├── App.tsx          # 메인 채팅 컴포넌트
├── index.tsx        # React 진입점
└── App.css          # 스타일링
```

## 💡 핵심 기능 구현

### 1. 이중 모드 채팅 시스템
- **일반 채팅 모드**: 문서 검색 없이 LLM 직접 대화
- **RAG 모드** (@prefix): 문서 검색 + 컨텍스트 기반 답변
- 구현 위치: `backend/chat/service.py:115-254`

### 2. 멀티턴 대화 관리
- 전체 대화 히스토리 유지 (제한 없음)
- 대화 컨텍스트를 LLM 프롬프트에 포함
- 토큰 사용량 모니터링 (32K 컨텍스트 윈도우)
- 구현 위치: `backend/chat/service.py:137-152`

### 3. 벡터 검색 시스템
- ChromaDB 기반 시맨틱 검색
- Jina v4 임베딩 (1024차원)
- 코사인 유사도 기반 매칭
- 구현 위치: `src/infrastructure/vector_store.py`

### 4. LLM 통합
- vLLM 서버 통합 (포트 8000)
- Seed-OSS-36B-Instruct-AWQ 모델
- 영어 시스템 프롬프트 + 한국어 응답
- Thinking 태그 자동 제거
- 구현 위치: `src/infrastructure/vllm_client.py`

## 🔄 데이터 플로우

### 사용자 요청 처리 플로우
```
1. 사용자 입력 (Frontend)
   ↓
2. WebUI Backend (포트 8003)
   - 인증 확인
   - 대화 히스토리 로드
   ↓
3. @ 접두사 확인
   - @있음 → RAG 모드
   - @없음 → 일반 모드
   ↓
4a. RAG 모드 (문서 검색)
    - RAG Backend 호출 (포트 8001)
    - ChromaDB 벡터 검색
    - 관련 문서 추출
    ↓
4b. 일반 모드
    - 직접 LLM 호출
    ↓
5. vLLM 서버 (포트 8000)
   - 프롬프트 생성
   - 답변 생성
   ↓
6. 응답 처리
   - Thinking 태그 제거
   - DB 저장
   - Frontend 반환
```

## 📈 성능 특성

### 시스템 제약사항
| 항목 | 값 | 설명 |
|-----|-----|-----|
| LLM 컨텍스트 | 32,768 토큰 | Qwen2.5 기반 모델 제한 |
| 최대 생성 토큰 | 4,096 | 답변 생성 길이 제한 |
| 임베딩 차원 | 1,024 | Jina v4 임베딩 크기 |
| 동시 사용자 | ~50명 | SQLite 제약 |
| API 타임아웃 | 60초 | HTTP 요청 제한 |

### 최적화 포인트
1. **토큰 관리**: 대화 히스토리 20,000 토큰 경고
2. **벡터 검색**: 상위 5개 문서 기본값
3. **캐싱**: 벡터 저장소 메모리 캐싱
4. **로깅**: 구조화된 로그로 디버깅 용이

## 🐛 이슈 추적

### 해결된 이슈
1. ✅ Frontend-Backend 연결 실패 (포트 미스매치)
2. ✅ CORS 에러 (프록시 설정)
3. ✅ 멀티턴 대화 컨텍스트 누락
4. ✅ 중국어 thinking 태그 출력
5. ✅ @ 접두사 모드 구분 미작동

### 현재 제약사항
1. ⚠️ 실시간 스트리밍 미지원 (WebSocket 없음)
2. ⚠️ 파일 업로드 미구현
3. ⚠️ 사용자별 권한 관리 없음
4. ⚠️ 백업/복원 기능 없음

## 🔒 보안 고려사항

### 구현된 보안
- JWT 기반 인증 (24시간 만료)
- bcrypt 비밀번호 해싱
- SQL Injection 방지 (ORM 사용)
- CORS 정책 설정

### 미구현 보안
- Rate Limiting
- API Key 관리
- 감사 로그
- 데이터 암호화

## 📝 개발 가이드

### 환경 설정
```bash
# RAG 백엔드 (포트 8001)
cd /path/to/project
python api.py

# vLLM 서버 (포트 8000)
vllm serve QuantTrio/Seed-OSS-36B-Instruct-AWQ \
  --port 8000 \
  --max-model-len 32768

# WebUI 백엔드 (포트 8003)
cd backend
python main.py

# Frontend (포트 3000)
cd frontend
npm start
```

### 주요 설정 파일
- `backend/core/config.py`: WebUI 설정
- `src/infrastructure/config.py`: RAG 설정
- `frontend/package.json`: 프록시 설정

## 🚀 향후 개선 방향

### 단기 (1-2주)
1. WebSocket 기반 실시간 스트리밍
2. 파일 업로드 및 인덱싱 UI
3. 대화 내보내기 (PDF/JSON)
4. 검색 필터 고도화

### 중기 (1-2개월)
1. 다중 LLM 모델 지원
2. 사용자 권한 관리
3. 통계 대시보드
4. 자동 백업 시스템

### 장기 (3-6개월)
1. 분산 벡터 DB 지원
2. 다국어 지원 확대
3. 플러그인 시스템
4. 엔터프라이즈 기능

## 📊 코드 메트릭스

### 코드 규모
- 총 Python 파일: 약 50개
- 총 TypeScript 파일: 약 5개
- 평균 파일당 라인: 150-200줄
- 테스트 커버리지: 약 40%

### 복잡도
- 순환 복잡도: 낮음 (Clean Architecture)
- 결합도: 낮음 (의존성 주입)
- 응집도: 높음 (모듈별 명확한 책임)

## 🏆 프로젝트 강점

1. **Clean Architecture**: 명확한 계층 분리
2. **비동기 처리**: FastAPI의 async/await 활용
3. **타입 안정성**: TypeScript + Pydantic
4. **확장 가능**: 모듈식 설계
5. **문서화**: 명확한 코드 주석 및 문서

## ⚠️ 주의사항

1. SQLite는 동시 쓰기 제한 있음
2. vLLM 서버 메모리 사용량 높음 (최소 24GB)
3. 대용량 PDF 처리 시 타임아웃 가능
4. 프론트엔드 React 19 실험적 버전 사용

---

*마지막 업데이트: 2025-09-03*
*작성자: Claude Code Assistant*