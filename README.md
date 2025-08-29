# Medical Gait Analysis RAG System

의료 보행 분석 연구 논문을 위한 RAG(Retrieval-Augmented Generation) 시스템

## 🏗️ Clean Architecture

```
src/
├── domain/          # 비즈니스 엔티티 및 규칙
├── application/     # 유스케이스 및 비즈니스 로직
├── infrastructure/  # 외부 서비스 구현 (ChromaDB, Jina)
├── presentation/    # API 엔드포인트 (FastAPI)
├── common/         # 공통 유틸리티
└── container.py    # 의존성 주입
```

## 🚀 빠른 시작

### 1. 설치

```bash
pip install -r requirements.txt
```

### 2. 문서 인덱싱

```bash
python index_papers_v2.py --directory ./data --device cuda:5
```

### 3. API 서버 실행

```bash
python api_v2.py --host 0.0.0.0 --port 8000
```

## 📚 주요 기능

- **ChromaDB 1.0+** 벡터 데이터베이스
- **Jina v4 임베딩** (2048차원, 한국어/영어 지원)
- **의료 도메인 특화** (뇌졸중, 파킨슨, 관절염, 측만증)
- **보행 파라미터 자동 추출**
- **비동기 처리** (async/await)
- **RESTful API** (FastAPI)

## 🔍 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|----------|--------|------|
| `/search` | POST | 문서 검색 |
| `/index/document` | POST | 단일 문서 인덱싱 |
| `/index/directory` | POST | 디렉토리 인덱싱 |
| `/statistics` | GET | 시스템 통계 |
| `/documents/{id}` | DELETE | 문서 삭제 |

## 🎯 검색 예제

```python
import httpx

response = httpx.post("http://localhost:8000/search", json={
    "query": "walking speed in stroke patients",
    "limit": 5,
    "disease_categories": ["stroke"],
    "require_gait_params": True
})
```

## 📊 지원 보행 파라미터

- Walking speed/velocity (보행 속도)
- Cadence (분당 걸음 수)
- Step/stride length (보폭)
- Step width (보행 너비)
- Double/single support time (지지 시간)
- Joint angles (관절 각도)

## 🧪 테스트

```bash
pytest tests/
```

## 📄 라이센스

MIT License