# Backend API System (backend/) - 상세 문서

## 디렉토리 구조

```
backend/
├── main.py              # FastAPI 앱 진입점
├── auth/               # 인증 시스템
├── chat/               # 채팅 시스템
├── rag/                # RAG 관리
├── database/           # DB 모델 및 세션
└── init_db.py         # DB 초기화
```

## 1. Main Application (main.py)

### FastAPI 설정:
```python
app = FastAPI(title="Medical Gait RAG WebUI Backend")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True
)

# 라우터 등록
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(admin_router, prefix="/api/v1/admin")
app.include_router(rag_router, prefix="/api/v1/rag")
```

### 서버 시작:
```bash
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

## 2. Authentication System (auth/)

### auth/models.py - 사용자 모델
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password_hash = Column(String)  # bcrypt 해시
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
```

### auth/service.py - 인증 서비스
**주요 기능:**
- `create_user()`: 사용자 생성 (bcrypt 해싱)
- `authenticate_user()`: 로그인 검증
- `create_access_token()`: JWT 토큰 생성 (24시간)
- `verify_token()`: 토큰 검증

### auth/router.py - 인증 엔드포인트
```python
POST /api/auth/register  # 사용자 등록
POST /api/auth/login     # 로그인 (JWT 반환)
GET /api/auth/profile    # 현재 사용자 정보
POST /api/auth/logout    # 로그아웃
```

### auth/dependencies.py - 인증 의존성
```python
async def get_current_user(token: str):
    # Authorization 헤더에서 토큰 추출
    # JWT 디코드 및 사용자 조회
    # 401 Unauthorized if invalid

async def require_admin(user: User):
    # 관리자 권한 확인
    # 403 Forbidden if not admin
```

## 3. Chat System (chat/)

### chat/router.py (359 lines)
**WebSocket 엔드포인트:**
```python
@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # JWT 토큰 검증
    # 사용자별 WebSocket 연결 관리
    # 실시간 메시지 처리
```

**채팅 엔드포인트:**
```python
GET /api/chat/conversations  # 대화 목록
GET /api/chat/conversations/{id}  # 특정 대화
POST /api/chat/conversations  # 새 대화 생성
DELETE /api/chat/conversations/{id}  # 대화 삭제

POST /api/chat/messages  # 메시지 전송
GET /api/chat/messages/{conversation_id}  # 메시지 내역
```

### chat/service.py (301 lines)
**ChatService 클래스:**

```python
async def process_message(message: str, conversation_id: int):
    # @ 감지: RAG 모드 vs Direct 모드
    if message.startswith('@'):
        # RAG API 호출
        response = await rag_proxy.query_with_rag(query)
    else:
        # vLLM 직접 호출
        response = await rag_proxy.direct_llm_query(query)
    
    # DB에 메시지 저장
    # WebSocket으로 실시간 전송
```

### chat/rag_proxy.py (285 lines)
**RAGProxyService 클래스:**

```python
async def query_with_rag(query: str):
    # RAG API (8001) 호출
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/qa",
            json={"query": query, "k": 5}
        )
    # 소스 문서 정보 포함하여 반환

async def direct_llm_query(query: str):
    # vLLM 서버 (8000) 직접 호출
    # 시스템 프롬프트 + 사용자 쿼리
    # streaming 지원
```

### chat/models.py - 채팅 모델
```python
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    created_at = Column(DateTime)
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    sources = Column(JSON)  # RAG 소스 문서
    created_at = Column(DateTime)
```

## 4. RAG Management (rag/)

### rag/routes.py (657 lines)
**가장 큰 파일 - RAG 관리 API**

**통계 엔드포인트:**
```python
GET /api/v1/rag/stats
    # ChromaDB 직접 연결
    # 문서별 청크 카운트
    # has_gait_params 메타데이터 집계
    # 반환: {
    #   total_documents: N,
    #   total_chunks: N,
    #   chunks_with_gait_params: N  # 보행 파라미터 포함 청크
    # }
```

**문서 관리:**
```python
GET /api/v1/rag/documents  # 인덱싱된 문서 목록
    # ChromaDB에서 document_id별 그룹화
    # 각 문서의 청크 수 계산
    
POST /api/v1/rag/documents/upload  # PDF 업로드
    # data/uploads/에 저장
    # RAG API로 인덱싱 요청
    
DELETE /api/v1/rag/documents/{document_id}  # 문서 삭제
    # URL 인코딩 처리
    # RAG API로 삭제 요청
```

**재인덱싱:**
```python
POST /api/v1/rag/reindex
    # BackgroundTasks 사용
    # WebSocket으로 진행상황 전송
    # 모든 PDF 파일 재처리
    
async def run_indexing():
    # reset_vector_store.py 실행
    # PDF 파일별 순차 처리
    # progress_manager로 상태 업데이트
```

### rag/websocket.py
**ProgressManager 클래스:**
```python
class ProgressManager:
    # WebSocket 연결 관리
    # 인덱싱 진행상황 브로드캐스트
    
    async def file_processing(filename: str):
        # 현재 처리 중인 파일 알림
    
    async def file_completed(filename: str, chunks: int):
        # 파일 완료 알림
```

## 5. Admin System (auth/admin_router.py)

**사용자 관리:**
```python
GET /api/v1/admin/users  # 사용자 목록
POST /api/v1/admin/users  # 사용자 생성
PUT /api/v1/admin/users/{id}  # 사용자 수정
DELETE /api/v1/admin/users/{id}  # 사용자 삭제
PUT /api/v1/admin/users/{id}/toggle-admin  # 관리자 권한 토글
```

## 6. Database System (database/)

### database/models.py
**SQLAlchemy 모델:**
- User: 사용자 정보
- Conversation: 대화 세션
- Message: 채팅 메시지

### database/session.py
```python
DATABASE_URL = "sqlite:///./gait_rag.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    # FastAPI 의존성
    # 자동 세션 관리
```

## 7. Database Initialization (init_db.py - 195 lines)

**초기 설정:**
```python
def init_database(reset=False):
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 기본 사용자 생성
    - admin / admin12345 (관리자)
    - demouser / demo12345 (일반)
    
    # 웰컴 메시지 생성
    # 사용 예시 포함
```

## 8. 데이터 플로우

### 메시지 처리 플로우:
```
Frontend → WebSocket/HTTP → Backend
    ↓
메시지 파싱 (@감지)
    ↓
RAG 모드: Backend → RAG API → ChromaDB/vLLM
Direct 모드: Backend → vLLM Server
    ↓
응답 생성 → DB 저장
    ↓
WebSocket/HTTP → Frontend
```

### 인증 플로우:
```
로그인 요청 → auth/login
    ↓
비밀번호 검증 (bcrypt)
    ↓
JWT 토큰 생성 (24시간)
    ↓
모든 요청에 Bearer Token 포함
    ↓
get_current_user() 의존성으로 검증
```

## 9. 보행 파라미터 통계 처리

### 통계 수집 과정:
```python
# rag/routes.py - get_rag_statistics()

1. RAG API 호출 시도 (http://localhost:8001/statistics)
2. 실패 시 ChromaDB 직접 연결:
   client = chromadb.PersistentClient(path="/data1/.../chroma_db")
   
3. 컬렉션 조회:
   collection = client.get_collection("gait_papers")
   
4. 메타데이터 순회:
   for metadata in result['metadatas']:
       if metadata.get('has_gait_params'):
           chunks_with_gait_params += 1
           
5. Frontend로 전송:
   return {
       "chunks_with_gait_params": chunks_with_gait_params
   }
```

## 10. 환경 설정

### 필수 환경 변수:
```bash
DATABASE_URL=sqlite:///./gait_rag.db
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# RAG API 연결
RAG_API_URL=http://localhost:8001
VLLM_API_URL=http://localhost:8000
```

### 포트 설정:
- Backend API: 8003
- RAG API 프록시: → 8001
- vLLM 프록시: → 8000