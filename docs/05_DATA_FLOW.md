# 데이터 플로우 상세 문서

## 1. 문서 인덱싱 플로우

### 1.1 단일 문서 인덱싱

```
[PDF 파일]
    ↓
[Frontend: 파일 업로드]
    ↓ FormData (multipart/form-data)
[Backend: POST /api/v1/rag/documents/upload]
    ↓ 파일 저장: data/uploads/YYYYMMDD_HHMMSS_filename.pdf
[RAG API: POST /index/document]
    ↓
[PDFDocumentProcessor]
    ├─→ PyMuPDF로 텍스트 추출
    ├─→ 테이블 추출 (있는 경우)
    └─→ 페이지별 콘텐츠 저장
    ↓
[청크 생성]
    ├─→ 텍스트 분할 (500 단어, 100 오버랩)
    ├─→ 보행 키워드 검색
    │   └─→ GAIT_KEYWORDS 매칭
    │       └─→ has_gait_params = True/False
    └─→ 메타데이터 생성
    ↓
[JinaEmbeddingService]
    ├─→ GPU 6번 사용
    ├─→ 배치 처리 (8개씩)
    └─→ 2048차원 벡터 생성
    ↓
[ChromaVectorStore]
    ├─→ 벡터 저장
    ├─→ 메타데이터 저장
    │   ├─→ document_id
    │   ├─→ page_number
    │   ├─→ has_gait_params  ← 보행 파라미터 플래그
    │   └─→ gait_params (JSON)
    └─→ 컬렉션: "gait_papers"
```

### 1.2 보행 파라미터 감지 상세

```python
# document_processor.py
GAIT_KEYWORDS = [
    # 영어 키워드
    'speed', 'velocity', 'cadence', 
    'step length', 'stride length',
    'walking speed', 'gait speed',
    
    # 한글 키워드  
    '속도', '보행', '보폭', 
    '걸음', '보행속도'
]

def _contains_gait_keywords(text):
    text_lower = text.lower()
    for keyword in GAIT_KEYWORDS:
        if keyword in text_lower:
            return True  # → has_gait_params = True
    return False
```

## 2. 질의응답 플로우

### 2.1 RAG 모드 (@로 시작)

```
[사용자 입력: "@파킨슨병 보행 특징"]
    ↓
[Frontend: @ 감지 → use_rag=true]
    ↓
[Backend: POST /api/chat/messages]
    ├─→ DB에 사용자 메시지 저장
    └─→ RAGProxyService 호출
    ↓
[RAG API: POST /qa]
    ↓
[검색 단계]
    ├─→ 쿼리 임베딩 생성 (JinaEmbedding)
    ├─→ ChromaDB 벡터 검색
    │   ├─→ 코사인 유사도 계산
    │   ├─→ 상위 k=5개 청크 선택
    │   └─→ min_score=0.7 필터링
    └─→ 검색 결과 정렬
    ↓
[컨텍스트 구성]
    ├─→ 검색된 청크 텍스트 결합
    ├─→ 소스 문서 정보 포함
    └─→ 총 토큰 수 계산
    ↓
[LLM 답변 생성]
    ├─→ vLLM Server (포트 8000)
    ├─→ Nemotron-12B 모델
    ├─→ 131,072 토큰 컨텍스트
    └─→ Temperature: 0.6
    ↓
[응답 구성]
    ├─→ LLM 답변 텍스트
    ├─→ 소스 문서 리스트
    │   ├─→ document_id
    │   ├─→ page_number
    │   ├─→ 유사도 점수
    │   └─→ has_gait_params
    └─→ 처리 시간
    ↓
[Backend: DB 저장 + WebSocket 전송]
    ↓
[Frontend: 메시지 + 소스 표시]
```

### 2.2 Direct 모드 (@ 없음)

```
[사용자 입력: "정상 보행 주기 설명"]
    ↓
[Frontend: @ 없음 → use_rag=false]
    ↓
[Backend: vLLM 직접 호출]
    ├─→ 시스템 프롬프트 추가
    └─→ 검색 없이 바로 생성
    ↓
[vLLM Server]
    └─→ Nemotron-12B 직접 응답
    ↓
[Frontend: 메시지만 표시 (소스 없음)]
```

## 3. 통계 조회 플로우

### 3.1 보행 파라미터 통계

```
[AdminPage: 마운트 시 자동 조회]
    ↓
[GET /api/v1/rag/stats]
    ↓
[Backend: rag/routes.py]
    ├─→ RAG API 호출 시도
    │   └─→ GET http://localhost:8001/statistics
    └─→ 실패 시 ChromaDB 직접 연결
    ↓
[ChromaDB 조회]
    ├─→ collection.get() 모든 문서
    └─→ 메타데이터 순회
        └─→ if metadata.get('has_gait_params'):
            chunks_with_gait_params += 1
    ↓
[통계 반환]
{
    "total_documents": 15,
    "total_chunks": 523,
    "text_chunks": 498,
    "table_chunks": 25,
    "chunks_with_gait_params": 187  ← 보행 키워드 포함 청크
}
    ↓
[Frontend: 통계 카드 업데이트]
    └─→ "보행 파라미터 포함: 187개"
```

## 4. 문서 삭제 플로우

```
[AdminPage: 문서 삭제 버튼]
    ↓
[DELETE /api/v1/rag/documents/{document_id}]
    ├─→ URL 인코딩 처리
    └─→ document_id = "uploads/20250906_164936_Abe 2009.pdf"
    ↓
[RAG API: DELETE /documents/{document_id}]
    ↓
[ChromaVectorStore]
    ├─→ where={"document_id": document_id}로 조회
    ├─→ 해당 청크 ID 목록 획득
    └─→ collection.delete(ids=chunk_ids)
    ↓
[결과 반환]
    └─→ chunks_deleted: 23
```

## 5. 재인덱싱 플로우

```
[AdminPage: 재인덱싱 버튼]
    ↓
[POST /api/v1/rag/reindex]
    ├─→ BackgroundTasks 시작
    └─→ WebSocket 연결 대기
    ↓
[reset_vector_store.py 실행]
    ├─→ ChromaDB 컬렉션 삭제
    └─→ 새 컬렉션 생성
    ↓
[디렉토리 스캔]
    └─→ data/**/*.pdf 파일 목록
    ↓
[순차 처리 (파일별)]
    ├─→ WebSocket: "Processing: filename.pdf"
    ├─→ RAG API로 인덱싱 요청
    ├─→ 성공/실패 카운트
    └─→ 진행률 업데이트
    ↓
[WebSocket 진행상황]
{
    "status": "indexing",
    "current_file": "Abe 2009.pdf",
    "completed_files": 3,
    "total_files": 15,
    "chunks_created": 89
}
    ↓
[Frontend: 실시간 진행바 표시]
```

## 6. 인증 플로우

```
[로그인 폼]
    ↓
[POST /api/auth/login]
    ├─→ username: "demouser"
    └─→ password: "demo12345"
    ↓
[Backend: 검증]
    ├─→ bcrypt 해시 비교
    └─→ JWT 토큰 생성 (24시간)
    ↓
[토큰 저장]
    ├─→ localStorage.setItem('token', jwt)
    └─→ axios.defaults.headers['Authorization'] = 'Bearer {jwt}'
    ↓
[모든 API 요청]
    └─→ Header: Authorization: Bearer {jwt}
    ↓
[Backend: get_current_user()]
    ├─→ JWT 디코드
    ├─→ 사용자 조회
    └─→ 401 if invalid
```

## 7. WebSocket 연결 플로우

```
[Frontend: WebSocket 초기화]
    └─→ ws://localhost:8003/api/v1/rag/ws/progress
    ↓
[Backend: WebSocket 핸들러]
    ├─→ 연결 수락
    └─→ ProgressManager 등록
    ↓
[인덱싱 중 이벤트]
    ├─→ file_processing(filename)
    ├─→ file_completed(filename, chunks)
    └─→ update_progress(stats)
    ↓
[브로드캐스트]
    └─→ 모든 연결된 클라이언트에 전송
    ↓
[Frontend: onmessage]
    └─→ UI 업데이트
```

## 8. 에러 처리 플로우

```
[에러 발생]
    ↓
[API 레벨]
    ├─→ try/catch 블록
    ├─→ HTTPException 발생
    └─→ 상태 코드 + 메시지
    ↓
[Backend 레벨]
    ├─→ 401: 인증 실패
    ├─→ 403: 권한 부족
    ├─→ 404: 리소스 없음
    └─→ 500: 서버 에러
    ↓
[Frontend 레벨]
    ├─→ axios 인터셉터
    ├─→ 401 → 로그아웃
    └─→ 사용자 알림
```

## 9. 성능 최적화 포인트

### 임베딩 캐싱
- 동일 텍스트는 재계산 없이 캐시 사용
- 15분 TTL

### 배치 처리
- 임베딩: 8개씩 배치
- 문서 인덱싱: 청크 100개씩

### GPU 분산
- GPU 1: 임베딩 (CUDA 6)
- GPU 4,5: LLM (Tensor Parallel)

### 데이터베이스 인덱스
- conversation_id
- user_id
- created_at

## 10. 주요 데이터 구조

### ChromaDB 메타데이터
```json
{
  "document_id": "uploads/20250906_164936_Abe 2009.pdf",
  "page_number": 5,
  "chunk_index": 23,
  "chunk_type": "text",
  "has_gait_params": true,
  "gait_params": "[{\"name\": \"walking speed\", \"value\": \"1.2\", \"unit\": \"m/s\"}]",
  "disease_category": "PARKINSON"
}
```

### 메시지 응답 구조
```json
{
  "role": "assistant",
  "content": "파킨슨병 환자의 보행 특징은...",
  "sources": [
    {
      "chunk_id": "uploads/file.pdf_5_23",
      "content": "원문 텍스트...",
      "score": 0.89,
      "metadata": {
        "document_id": "uploads/file.pdf",
        "page_number": 5,
        "has_gait_params": true
      }
    }
  ]
}
```