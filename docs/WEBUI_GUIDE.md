# Medical Gait RAG WebUI - 통합 구현 가이드

## 🎯 프로젝트 개요

사내용 의료 보행 분석 RAG 시스템의 웹 인터페이스 구축을 위한 통합 가이드입니다.
간단하고 유지보수가 쉬운 구조를 유지하면서 필수 기능을 모두 제공합니다.

## 🐛 문제 해결 기록 (2025-09-02)

### 문제: Frontend와 Backend 연결 실패
**증상:**
- 프론트엔드에서 로그인 시도 시 백엔드로 요청이 전달되지 않음
- 브라우저 콘솔에 "Network Error" 발생
- 백엔드 로그에 HTTP 요청이 기록되지 않음

**원인:**
1. **포트 충돌**: 기존 RAG 백엔드(8001)와 WebUI 백엔드(8003)가 혼재
2. **CORS 설정 문제**: axios가 절대 URL을 사용하여 프록시가 작동하지 않음
3. **HTTP 요청 로깅 부재**: 백엔드에 요청 로깅 미들웨어가 없어 디버깅 어려움

**해결 방법:**
1. **HTTP 요청 로깅 미들웨어 추가** (backend/main.py):
   ```python
   @app.middleware("http")
   async def log_requests(request: Request, call_next):
       start_time = time.time()
       logger.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
       response = await call_next(request)
       process_time = time.time() - start_time
       logger.info(f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
       return response
   ```

2. **프록시 설정 추가** (frontend/package.json):
   ```json
   "proxy": "http://localhost:8003"
   ```

3. **Frontend API 설정 수정** (frontend/src/App.tsx):
   ```typescript
   // 절대 URL 대신 상대 경로 사용
   const API_URL = '';  // 이전: 'http://localhost:8003'
   ```

**결과:**
- 프론트엔드에서 백엔드로 정상적으로 요청 전달
- 모든 HTTP 요청이 로그에 기록되어 디버깅 용이
- 로그인 및 인증 기능 정상 작동

## 🛠️ 기술 스택 (2024년 12월 기준 최신 버전)

### Backend
- **FastAPI** 0.115.5 - 높은 성능의 웹 프레임워크
- **SQLite** - 간단한 배포, 파일 기반 데이터베이스
- **SQLAlchemy** 2.0.36 - ORM
- **Pydantic** 2.10.3 - 데이터 검증
- **python-jose** 3.3.0 - JWT 토큰
- **passlib** 1.7.4 - 비밀번호 해싱
- **Redis** 5.2.1 - 세션 캐시 (선택적)
- **Loguru** 0.7.3 - 로깅

### Frontend
- **React** 18.3.1 + **TypeScript** 5.6
- **Vite** 5.4 - 빌드 도구
- **TailwindCSS** 3.4 - 스타일링
- **Axios** 1.7.9 - API 통신
- **React Router** 6.28 - 라우팅
- **Zustand** 5.0 - 상태 관리

## 📁 프로젝트 구조

```
medical_gait_rag/
├── backend/
│   ├── auth/                      # 인증 모듈
│   │   ├── __init__.py
│   │   ├── models.py              # User 모델 (50줄)
│   │   ├── router.py              # 인증 엔드포인트 (100줄)
│   │   ├── service.py             # 인증 비즈니스 로직 (80줄)
│   │   ├── dependencies.py        # JWT 검증 (30줄)
│   │   └── schemas.py             # Request/Response 스키마 (40줄)
│   │
│   ├── chat/                      # 채팅 모듈
│   │   ├── __init__.py
│   │   ├── models.py              # Conversation/Message 모델 (60줄)
│   │   ├── router.py              # 채팅 엔드포인트 (150줄)
│   │   ├── service.py             # 채팅 비즈니스 로직 (120줄)
│   │   └── schemas.py             # 채팅 스키마 (40줄)
│   │
│   ├── database/                  # 데이터베이스 설정
│   │   ├── __init__.py           # DB 초기화 (20줄)
│   │   ├── base.py               # SQLAlchemy Base (20줄)
│   │   ├── session.py            # 세션 관리 (30줄)
│   │   └── migrations/           # Alembic 마이그레이션
│   │
│   ├── core/                      # 핵심 유틸리티
│   │   ├── __init__.py
│   │   ├── config.py             # 설정 관리 (50줄)
│   │   ├── security.py           # 보안 유틸리티 (60줄)
│   │   ├── exceptions.py         # 커스텀 예외 (40줄)
│   │   ├── middleware.py         # 미들웨어 (80줄)
│   │   └── logging.py            # 로깅 설정 (40줄)
│   │
│   ├── contexts/                  # 컨텍스트 관리
│   │   ├── __init__.py
│   │   ├── models.py             # Context 모델 (40줄)
│   │   ├── router.py             # Context 엔드포인트 (80줄)
│   │   └── service.py            # Context 로직 (60줄)
│   │
│   ├── main.py                   # FastAPI 앱 진입점 (100줄)
│   ├── requirements.txt          # Python 의존성
│   └── .env                      # 환경 변수
│
├── frontend/
│   ├── src/
│   │   ├── components/           # React 컴포넌트
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx        (100줄)
│   │   │   │   └── RegisterForm.tsx     (100줄)
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx       (150줄)
│   │   │   │   ├── MessageList.tsx      (80줄)
│   │   │   │   ├── MessageInput.tsx     (60줄)
│   │   │   │   └── SourceDisplay.tsx    (50줄)
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx           (60줄)
│   │   │   │   ├── Sidebar.tsx          (100줄)
│   │   │   │   └── Layout.tsx           (80줄)
│   │   │   └── common/
│   │   │       ├── Button.tsx           (40줄)
│   │   │       ├── Input.tsx            (40줄)
│   │   │       └── ErrorBoundary.tsx    (50줄)
│   │   │
│   │   ├── pages/                # 페이지 컴포넌트
│   │   │   ├── Login.tsx         (80줄)
│   │   │   ├── Register.tsx      (80줄)
│   │   │   ├── Dashboard.tsx     (120줄)
│   │   │   └── Chat.tsx          (100줄)
│   │   │
│   │   ├── api/                  # API 클라이언트
│   │   │   ├── client.ts         (50줄 - Axios 설정)
│   │   │   ├── auth.ts           (60줄)
│   │   │   ├── chat.ts           (80줄)
│   │   │   └── contexts.ts       (60줄)
│   │   │
│   │   ├── stores/               # Zustand 상태 관리
│   │   │   ├── authStore.ts      (80줄)
│   │   │   ├── chatStore.ts      (100줄)
│   │   │   └── contextStore.ts   (60줄)
│   │   │
│   │   ├── hooks/                # 커스텀 훅
│   │   │   ├── useAuth.ts        (50줄)
│   │   │   ├── useChat.ts        (60줄)
│   │   │   └── useDebounce.ts    (20줄)
│   │   │
│   │   ├── types/                # TypeScript 타입
│   │   │   ├── auth.ts           (30줄)
│   │   │   ├── chat.ts           (40줄)
│   │   │   └── index.ts          (20줄)
│   │   │
│   │   ├── utils/                # 유틸리티
│   │   │   ├── format.ts         (40줄)
│   │   │   ├── validation.ts     (40줄)
│   │   │   └── constants.ts      (20줄)
│   │   │
│   │   ├── App.tsx               (60줄)
│   │   ├── main.tsx              (20줄)
│   │   └── index.css             (10줄)
│   │
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── .env
│
├── scripts/
│   ├── setup.sh                  # 초기 설정 스크립트
│   ├── migrate.py                # DB 마이그레이션
│   └── test.sh                   # 테스트 실행
│
└── docs/
    ├── API.md                    # API 문서
    └── DEPLOYMENT.md             # 배포 가이드
```

## 💾 데이터베이스 스키마 (SQLite)

```sql
-- 사용자 테이블
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    department TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 대화 테이블
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 메시지 테이블
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources TEXT, -- JSON 문자열로 저장
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- 저장된 컨텍스트 테이블
CREATE TABLE contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT, -- 쉼표로 구분된 태그
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_contexts_user ON contexts(user_id);
```

## 🔒 보안 및 에러 처리

### 1. 인증 시스템

```python
# backend/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from loguru import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityService:
    """보안 관련 서비스"""
    
    SECRET_KEY = "your-secret-key-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24시간
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """JWT 토큰 생성"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=SecurityService.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SecurityService.SECRET_KEY, algorithm=SecurityService.ALGORITHM)
```

### 2. 에러 처리 미들웨어

```python
# backend/core/middleware.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# Rate Limiting 설정
limiter = Limiter(key_func=get_remote_address)

class ErrorHandlingMiddleware:
    """글로벌 에러 처리 미들웨어"""
    
    async def __call__(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except ValueError as e:
            logger.error(f"Value error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": str(e)}
            )
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

# API 응답 포맷
class APIResponse:
    """통일된 API 응답 포맷"""
    
    @staticmethod
    def success(data=None, message="Success"):
        return {
            "status": "success",
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(message="Error", code=400):
        return {
            "status": "error",
            "message": message,
            "code": code
        }
```

### 3. CORS 설정

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.middleware import ErrorHandlingMiddleware, limiter

app = FastAPI(title="Medical Gait RAG WebUI", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# 에러 처리 미들웨어
app.add_middleware(ErrorHandlingMiddleware)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
```

## 📋 API 엔드포인트

### 인증 API
```python
POST   /api/v1/auth/register     # 회원가입
POST   /api/v1/auth/login        # 로그인
GET    /api/v1/auth/me           # 현재 사용자 정보
POST   /api/v1/auth/logout       # 로그아웃
PUT    /api/v1/auth/profile      # 프로필 수정
```

### 채팅 API
```python
GET    /api/v1/conversations                      # 대화 목록
POST   /api/v1/conversations                      # 대화 생성
GET    /api/v1/conversations/{id}                 # 대화 조회
DELETE /api/v1/conversations/{id}                 # 대화 삭제
POST   /api/v1/conversations/{id}/messages        # 메시지 전송
GET    /api/v1/conversations/{id}/messages        # 메시지 목록
```

### 컨텍스트 API
```python
GET    /api/v1/contexts                           # 컨텍스트 목록
POST   /api/v1/contexts                           # 컨텍스트 저장
PUT    /api/v1/contexts/{id}                      # 컨텍스트 수정
DELETE /api/v1/contexts/{id}                      # 컨텍스트 삭제
```

### RAG 통합 API
```python
POST   /api/v1/rag/search                         # 문서 검색
POST   /api/v1/rag/qa                            # 질의응답
GET    /api/v1/rag/health                        # 상태 확인
```

## 🧪 테스트 전략

### 1. 단위 테스트
```python
# tests/test_auth.py
import pytest
from backend.core.security import SecurityService

def test_password_hashing():
    """비밀번호 해싱 테스트"""
    password = "testpass123"
    hashed = SecurityService.get_password_hash(password)
    assert SecurityService.verify_password(password, hashed)

def test_jwt_token():
    """JWT 토큰 생성 및 검증"""
    data = {"sub": "testuser"}
    token = SecurityService.create_access_token(data)
    assert token is not None
```

### 2. 통합 테스트
```python
# tests/test_integration.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_login_flow():
    """로그인 플로우 테스트"""
    # 회원가입
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "testpass123",
        "full_name": "Test User"
    })
    assert response.status_code == 200
    
    # 로그인
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### 3. 테스트 커버리지 목표
- 핵심 비즈니스 로직: 90% 이상
- API 엔드포인트: 80% 이상
- 유틸리티 함수: 70% 이상

## 🚀 개발 환경 설정

### 1. Backend 설정
```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r backend/requirements.txt

# 데이터베이스 초기화
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# 개발 서버 실행
uvicorn backend.main:app --reload --port 8001
```

### 2. Frontend 설정
```bash
# 의존성 설치
cd frontend
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build
```

### 3. 환경 변수 설정
```env
# backend/.env
DATABASE_URL=sqlite:///./gait_rag.db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
RAG_API_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379  # 선택적
LOG_LEVEL=INFO
ENVIRONMENT=development

# frontend/.env
VITE_API_URL=http://localhost:8001
VITE_APP_NAME=Medical Gait RAG
```

## 📊 모니터링 및 로깅

### 1. 로깅 설정
```python
# backend/core/logging.py
from loguru import logger
import sys

def setup_logging(log_level: str = "INFO"):
    """로깅 설정"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level=log_level
    )
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level=log_level
    )
```

### 2. 성능 모니터링
```python
# backend/core/monitoring.py
import time
from functools import wraps
from loguru import logger

def measure_performance(func):
    """함수 실행 시간 측정 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} executed in {duration:.2f}s")
        return result
    return wrapper
```

## 🔄 개발 로드맵

### Phase 1: 기본 구현 (1주차)
- [x] 프로젝트 구조 설정
- [ ] 데이터베이스 스키마 구현
- [ ] 사용자 인증 시스템
- [ ] 기본 채팅 인터페이스

### Phase 2: 핵심 기능 (2주차)
- [ ] 대화 관리 기능
- [ ] 메시지 스트리밍
- [ ] 컨텍스트 저장/관리
- [ ] RAG API 통합

### Phase 3: 고급 기능 (3주차)
- [ ] 검색 필터링
- [ ] 내보내기 기능 (PDF/JSON)
- [ ] 사용 통계
- [ ] 관리자 기능

### Phase 4: 최적화 (4주차)
- [ ] 성능 최적화
- [ ] 보안 강화
- [ ] 테스트 커버리지
- [ ] 배포 준비

## 🏁 성공 지표

1. **성능**
   - API 응답 시간 < 200ms (평균)
   - 페이지 로드 시간 < 2초
   - 동시 사용자 50명 지원

2. **안정성**
   - 99.9% 가동률
   - 에러율 < 1%
   - 자동 복구 메커니즘

3. **사용성**
   - 직관적인 UI/UX
   - 모바일 반응형
   - 다국어 지원 (한국어/영어)

4. **유지보수성**
   - 코드 커버리지 > 80%
   - 모든 API 문서화
   - 명확한 에러 메시지

## 📝 참고사항

- 모든 코드는 200줄 이하로 유지
- 함수는 30줄 이하로 작성
- 명확한 타입 힌트 사용
- 에러 처리 필수
- 로깅 적극 활용
- 테스트 우선 개발

## 🆘 문제 해결 가이드

### 일반적인 문제들

1. **CORS 에러**
   - Frontend URL이 CORS 설정에 포함되었는지 확인
   - 개발/프로덕션 환경 구분

2. **JWT 토큰 만료**
   - 자동 갱신 로직 구현
   - 적절한 만료 시간 설정

3. **데이터베이스 락**
   - SQLite WAL 모드 활성화
   - 동시성 제한 설정

4. **메모리 누수**
   - 적절한 연결 풀 관리
   - 리소스 정리 확인

---

이 가이드는 지속적으로 업데이트됩니다. 문제가 발생하면 GitHub Issues에 보고해주세요.