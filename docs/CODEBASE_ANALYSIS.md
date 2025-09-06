# Medical Gait RAG - 코드베이스 분석 보고서

## 📊 현재 시스템 구조

### 1. 아키텍처 패턴
- **Clean Architecture 구조** 적용
  - `domain/`: 비즈니스 엔티티
  - `application/`: 유스케이스 
  - `infrastructure/`: 외부 서비스 (DB, Embedding, vLLM)
  - `presentation/`: API 레이어

### 2. 핵심 기술 스택
- **Backend**: FastAPI (포트 8000)
- **Vector DB**: ChromaDB
- **Embedding**: Jina v4 (jinaai/jina-embeddings-v4)
- **LLM**: vLLM 서버 (Seed-OSS-36B-Instruct-AWQ)
- **문서 처리**: PyMuPDF

### 3. 현재 API 엔드포인트

```python
GET  /                      # 헬스체크
GET  /health               # 상태 확인
POST /search               # 문서 검색
POST /qa                   # 질의응답 (vLLM 통합)
POST /index/document       # 단일 문서 인덱싱
POST /index/directory      # 디렉토리 인덱싱
GET  /document/metadata    # 문서 메타데이터 조회
DELETE /document/{id}      # 문서 삭제
```

### 4. 주요 발견사항

#### ✅ 장점
- Clean Architecture로 잘 구조화됨
- 의존성 주입 컨테이너 사용
- 비동기 처리 지원
- vLLM 통합 완료

#### ⚠️ 제약사항
- **인증/인가 시스템 없음** 
- **사용자 관리 기능 없음**
- **세션/대화 기록 저장 없음**
- **웹소켓 미지원** (실시간 스트리밍)

## 🔌 WebUI 통합 포인트

### 1. 기존 API 활용
- `/search`, `/qa` 엔드포인트 직접 사용
- ChromaDB는 그대로 유지
- vLLM 클라이언트 재사용

### 2. 추가 필요 기능
- **인증 시스템**: JWT 기반 사용자 인증
- **세션 관리**: 대화 기록 저장
- **사용자 데이터**: SQLite DB 추가
- **WebSocket**: 실시간 응답 스트리밍

### 3. 통합 전략

```python
# 기존 RAG API (포트 8000)
/api/v1/rag/search    → POST /search
/api/v1/rag/qa        → POST /qa
/api/v1/rag/index     → POST /index/document

# 새로운 WebUI API (포트 8001)
/api/v1/auth/*        # 인증 관련
/api/v1/conversations/* # 대화 관리
/api/v1/contexts/*    # 컨텍스트 저장
```

## 📝 개발 로드맵

### Phase 1: 기반 구축 (Day 1-2)
1. **프로젝트 구조 생성**
   - `python setup_webui.py` 실행
   - 기본 디렉토리 구조 확립

2. **데이터베이스 설정**
   - SQLite 스키마 생성
   - Alembic 마이그레이션 설정

3. **인증 시스템 구현**
   - JWT 토큰 발급/검증
   - 사용자 등록/로그인

### Phase 2: 핵심 기능 (Day 3-5)
1. **RAG API 프록시**
   - 기존 API와 통신 레이어
   - 응답 캐싱

2. **대화 관리**
   - 대화 저장/조회
   - 메시지 이력 관리

3. **React UI 구현**
   - 로그인/회원가입 페이지
   - 채팅 인터페이스
   - 사이드바 네비게이션

### Phase 3: 고급 기능 (Day 6-7)
1. **컨텍스트 관리**
   - 자주 사용하는 컨텍스트 저장
   - 빠른 삽입 기능

2. **실시간 기능**
   - WebSocket 통합 (선택적)
   - 스트리밍 응답

3. **UI/UX 개선**
   - 소스 문서 표시
   - 검색 필터링
   - 다크모드

### Phase 4: 마무리 (Day 8)
1. **테스트**
   - API 통합 테스트
   - UI 컴포넌트 테스트

2. **문서화**
   - API 문서 자동 생성
   - 사용자 가이드

3. **배포 준비**
   - Docker 설정
   - 환경 변수 정리

## 🚀 즉시 시작 가능한 작업

### 1. 환경 설정
```bash
# WebUI 프로젝트 생성
python setup_webui.py

# Backend 설정
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements-web.txt

# Frontend 설정  
cd ../frontend
npm install
```

### 2. 첫 번째 구현 파일

#### `backend/database/models.py` (사용자/대화 모델)
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    department = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")
```

## 💡 주요 고려사항

1. **기존 시스템과의 호환성**
   - RAG API는 포트 8000에서 계속 실행
   - WebUI API는 포트 8001에서 실행
   - 내부 통신으로 RAG API 호출

2. **성능 최적화**
   - Redis 캐싱 (선택적)
   - 응답 페이지네이션
   - 프론트엔드 레이지 로딩

3. **보안**
   - JWT 토큰 24시간 만료
   - Rate limiting 적용
   - SQL injection 방지 (SQLAlchemy ORM)

4. **확장성**
   - 모듈식 구조로 기능 추가 용이
   - 파일당 200줄 제한 준수
   - 명확한 레이어 분리

## 🎯 다음 단계

1. **즉시**: `setup_webui.py` 실행하여 프로젝트 구조 생성
2. **다음**: 데이터베이스 모델 구현 및 마이그레이션
3. **그 다음**: 인증 라우터 구현
4. **마지막**: React 컴포넌트 개발 시작

---

이 분석을 기반으로 체계적이고 효율적인 WebUI 개발이 가능합니다.