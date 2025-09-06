# RAG Core System (src/) - 상세 문서

## 디렉토리 구조

```
src/
├── domain/           # 도메인 모델 및 비즈니스 규칙
├── application/      # 비즈니스 로직 (Use Cases)
├── infrastructure/   # 외부 서비스 구현
├── presentation/     # API 엔드포인트
├── common/          # 공통 유틸리티
└── container.py     # 의존성 주입 컨테이너
```

## 1. Domain Layer (도메인 계층)

### domain/entities.py
**주요 클래스:**
- `Document`: PDF 문서 엔티티
- `DocumentChunk`: 문서 청크 (검색 단위)
- `GaitParameter`: 보행 파라미터 (speed, cadence 등)
- `SearchResult`: 검색 결과

**핵심 기능:**
```python
class DocumentChunk:
    def has_gait_parameters() -> bool
        # 보행 파라미터 포함 여부 확인
        # gait_parameters 리스트가 비어있지 않으면 True
```

### domain/value_objects.py
- `PaperId`: 문서 고유 식별자
- `ChunkId`: 청크 고유 식별자
- `DiseaseCategory`: 질병 분류 (STROKE, PARKINSON 등)

### domain/repositories.py
**인터페이스 정의:**
- `VectorRepository`: 벡터 저장소 인터페이스
- `DocumentRepository`: 문서 저장소 인터페이스

## 2. Infrastructure Layer (인프라 계층)

### infrastructure/vector_store.py (314 lines)
**클래스:** `ChromaVectorStore`

**주요 메서드:**
- `index_chunks()`: 청크를 ChromaDB에 저장
- `search()`: 벡터 유사도 검색
- `delete_by_document()`: 문서별 삭제
- `get_statistics()`: 통계 조회

**메타데이터 저장:**
```python
metadata = {
    "document_id": chunk.document_id,
    "page_number": chunk.page_number,
    "has_gait_params": chunk.has_gait_parameters(),  # 보행 파라미터 플래그
    "gait_params": json.dumps(gait_params)  # 실제 파라미터 데이터
}
```

### infrastructure/embedding.py (249 lines)
**클래스:** `JinaEmbeddingService`

**주요 기능:**
- Jina Embeddings v4 모델 사용 (2048차원)
- GPU 6번 사용 (CUDA_VISIBLE_DEVICES=2)
- 배치 처리 지원 (기본 8개)
- 최대 8192 토큰 지원

**핵심 메서드:**
```python
async def embed_batch(texts: List[str]) -> List[np.ndarray]:
    # 텍스트 배치를 임베딩 벡터로 변환
    # None 체크 포함 (빈 출력 방지)
```

### infrastructure/document_processor.py (362 lines)
**클래스:** `PDFDocumentProcessor`

**보행 키워드 감지:**
```python
GAIT_KEYWORDS = [
    # 영어
    'speed', 'velocity', 'cadence', 'step length', 
    'stride length', 'walking speed', 'gait speed',
    
    # 한글
    '속도', '보행', '보폭', '걸음', '보행속도'
]
```

**주요 프로세스:**
1. PDF에서 텍스트/테이블 추출 (PyMuPDF)
2. 청크 분할 (500 단어, 100 오버랩)
3. 보행 키워드 검색 (`_contains_gait_keywords()`)
4. 테이블에서 보행 파라미터 추출
5. 질병 카테고리 자동 분류

### infrastructure/vllm_client.py (266 lines)
**클래스:** `VLLMClient`

**설정:**
- 모델: Nemotron-12B
- 최대 토큰: 8192
- 컨텍스트: 131,072 토큰
- Temperature: 0.6

**프롬프트 구성:**
```python
def _construct_prompt(prompt, context, system_prompt):
    # 1. 시스템 프롬프트
    # 2. RAG 컨텍스트 (검색된 문서)
    # 3. 사용자 질문
    # 4. 답변 지시사항
```

**컨텍스트 관리:**
```python
# 토큰 추정 (1토큰 ≈ 3-4자)
if estimated_tokens > 120000:  # 91% 사용
    logger.warning("Approaching context limit!")
```

## 3. Application Layer (애플리케이션 계층)

### application/use_cases.py (313 lines)

**IndexDocumentUseCase:**
```python
async def execute(request: IndexDocumentRequest):
    1. PDF 파일 검증
    2. 콘텐츠 추출 (document_processor)
    3. 청크 생성
    4. 임베딩 생성 (embedding_service)
    5. ChromaDB 저장 (vector_repo)
    6. 문서 ID 생성 (data/ 기준 상대경로)
```

**SearchDocumentsUseCase:**
```python
async def execute(request: SearchRequest):
    1. 쿼리 임베딩 생성
    2. ChromaDB 검색 (코사인 유사도)
    3. 스코어 필터링 (min_score: 0.7)
    4. 결과 정렬 및 반환
```

**QAUseCase:**
```python
async def execute(request: QARequest):
    1. 검색 실행 (SearchDocumentsUseCase)
    2. 컨텍스트 구성 (상위 k개 청크)
    3. LLM 프롬프트 생성
    4. 답변 생성 (vllm_client)
    5. 소스 문서 포함하여 반환
```

### application/dto.py
**데이터 전송 객체:**
- `IndexDocumentRequest/Response`
- `SearchRequest/Response`
- `QARequest/Response`
- `StatisticsResponse`

## 4. Presentation Layer (프레젠테이션 계층)

### presentation/routes.py (434 lines)
**엔드포인트:**

```python
POST /qa  # 질의응답
    - RAG 모드: 문서 검색 + LLM 답변
    - Direct 모드: LLM 직접 답변

POST /index/document  # 단일 문서 인덱싱
    - PDF 파일 경로 받음
    - 청크 생성 및 저장
    - 보행 파라미터 추출

POST /index/directory  # 디렉토리 일괄 인덱싱
    - 모든 PDF 파일 처리
    - 진행상황 로깅

GET /search  # 문서 검색
    - 쿼리 기반 검색
    - 유사도 점수 반환

GET /statistics  # 통계 조회
    - 총 문서/청크 수
    - 보행 파라미터 포함 청크 수

DELETE /documents/{document_id}  # 문서 삭제
    - 특정 문서의 모든 청크 제거
```

## 5. Container (의존성 주입)

### container.py (182 lines)
**Dependency Injector 사용:**

```python
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # 서비스 프로바이더
    embedding_service = providers.Singleton(
        JinaEmbeddingService,
        model_path=config.embedding.model_path
    )
    
    vector_repository = providers.Singleton(
        ChromaVectorStore,
        collection_name=config.chromadb.collection_name
    )
    
    # Use Case 프로바이더
    qa_use_case = providers.Factory(
        QAUseCase,
        search_use_case=search_use_case,
        vllm_client=vllm_client
    )
```

## 6. 데이터 플로우

### 문서 인덱싱 플로우:
```
PDF 파일 → PDFDocumentProcessor → 청크 생성
    ↓
보행 키워드 검색 → has_gait_params 플래그 설정
    ↓
JinaEmbeddingService → 임베딩 벡터 생성
    ↓
ChromaVectorStore → 벡터 + 메타데이터 저장
```

### 질의응답 플로우:
```
사용자 질문 → 임베딩 변환
    ↓
ChromaDB 검색 → 유사 청크 추출
    ↓
컨텍스트 구성 → LLM 프롬프트 생성
    ↓
vLLM Server → 답변 생성
    ↓
소스 문서 정보 + 답변 반환
```

## 7. 보행 파라미터 처리 상세

### 키워드 기반 감지:
1. 각 청크의 텍스트에서 GAIT_KEYWORDS 검색
2. 키워드 발견 시 `has_gait_params = True`
3. 메타데이터로 ChromaDB에 저장

### 통계 계산:
```python
# vector_store.py
async def get_statistics():
    for metadata in all_items["metadatas"]:
        if metadata.get("has_gait_params"):
            stats["chunks_with_gait_params"] += 1
```

### 웹 UI 표시:
- Frontend: `/api/v1/rag/stats` 호출
- Backend: ChromaDB 조회 후 카운트
- 결과: "보행 파라미터 포함: N개" 표시