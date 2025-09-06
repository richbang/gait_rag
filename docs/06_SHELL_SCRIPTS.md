# Shell Scripts 문서

## 스크립트 목록

Medical Gait RAG 시스템은 3개의 핵심 쉘 스크립트를 제공합니다.

## 1. start_all_services.sh

### 용도
모든 서비스를 순차적으로 시작하는 메인 스크립트

### 실행 순서
1. **vLLM Server** (포트 8000)
   - start_vllm_nemotron.sh 호출

2. **RAG API** (포트 8001)
   - python api.py 실행
   - 로그: logs/rag_api.log

3. **WebUI Backend** (포트 8003)
   - python backend/main.py 실행
   - 로그: logs/webui_backend.log

4. **Frontend** (포트 3000)
   - npm start 실행
   - 로그: logs/frontend.log

### 기능
- 포트 중복 확인 (lsof 사용)
- 이미 실행 중인 서비스 건너뛰기
- 로그 디렉토리 자동 생성
- 서비스 URL 및 로그인 정보 표시

### 사용법
```bash
./start_all_services.sh
```

## 2. stop_all_services.sh

### 용도
실행 중인 모든 서비스를 안전하게 종료

### 종료 순서
1. **Frontend** - React 개발 서버
   - react-scripts start 프로세스
   - npm start 프로세스
   - node 포트 3000 프로세스

2. **WebUI Backend** - FastAPI 서버
   - uvicorn main:app 프로세스
   - python main.py 프로세스
   - backend/main.py 프로세스

3. **RAG API** - RAG 서버
   - python api.py 프로세스
   - uvicorn 포트 8001 프로세스
   - api:app 프로세스

4. **vLLM Server** - LLM 추론 서버
   - vllm serve 프로세스
   - vllm.entrypoints 프로세스

### 기능
- pkill을 사용한 안전한 프로세스 종료
- 2초 대기 후 포트 상태 확인
- 각 포트(3000, 8003, 8001, 8000) 사용 여부 표시

### 사용법
```bash
./stop_all_services.sh
```

## 3. start_vllm_nemotron.sh

### 용도
NVIDIA Nemotron-12B 모델을 vLLM으로 서빙

### 모델 사양
- **모델명**: nvidia/NVIDIA-Nemotron-Nano-12B-v2
- **파라미터**: 12.3B
- **아키텍처**: Mamba-Transformer 하이브리드
- **컨텍스트**: 131,072 토큰 (128K)

### GPU 설정
```bash
export CUDA_VISIBLE_DEVICES=0,1  # GPU 0번 및 1번 사용
TENSOR_PARALLEL=2                 # 2개 GPU 병렬 처리
```

### vLLM 파라미터
| 파라미터 | 값 | 설명 |
|----------|-----|------|
| --max-model-len | 131072 | 최대 컨텍스트 길이 |
| --tensor-parallel-size | 2 | GPU 병렬 수 |
| --gpu-memory-utilization | 0.85 | GPU 메모리 사용률 85% |
| --max-num-seqs | 8 | 동시 처리 시퀀스 수 |
| --mamba_ssm_cache_dtype | float32 | Mamba SSM 캐시 정밀도 |
| --dtype | bfloat16 | 모델 정밀도 |
| --swap-space | 4 | 스왑 공간 4GB |
| --enable-chunked-prefill | - | 청크 단위 prefill |

### 메모리 사용
- GPU당 약 22GB VRAM 사용
- 총 44GB VRAM 필요

### 사용법
```bash
# 직접 실행
./start_vllm_nemotron.sh

# 또는 start_all_services.sh에서 자동 호출
```

## 포트 확인 명령어

### 특정 포트 사용 여부 확인
```bash
lsof -Pi :8000 -sTCP:LISTEN
```

### 모든 서비스 포트 확인
```bash
for port in 3000 8003 8001 8000; do
    echo "Port $port:"
    lsof -Pi :$port -sTCP:LISTEN
done
```

## 로그 파일 위치

| 서비스 | 로그 파일 |
|--------|-----------|
| vLLM | 콘솔 출력 (터미널) |
| RAG API | logs/rag_api.log |
| WebUI Backend | logs/webui_backend.log |
| Frontend | logs/frontend.log |

## 문제 해결

### 포트가 이미 사용 중일 때
```bash
# 특정 포트를 사용하는 프로세스 찾기
lsof -i :8000

# 프로세스 강제 종료
kill -9 <PID>
```

### vLLM CUDA 에러
```bash
# GPU 상태 확인
nvidia-smi

# CUDA 장치 확인
echo $CUDA_VISIBLE_DEVICES
```

### 서비스가 시작되지 않을 때
1. 로그 파일 확인
2. 포트 충돌 확인
3. Python 환경 확인 (conda activate gait_rag)
4. 의존성 확인 (pip list)

## 권장 실행 순서

### 시스템 시작
```bash
# 1. 모든 서비스 시작
./start_all_services.sh

# 2. 서비스 상태 확인
curl http://localhost:8000/health  # vLLM
curl http://localhost:8001/health  # RAG API
curl http://localhost:8003/health  # WebUI Backend
```

### 시스템 종료
```bash
# 1. 모든 서비스 종료
./stop_all_services.sh

# 2. 포트 해제 확인
for port in 3000 8003 8001 8000; do
    lsof -Pi :$port -sTCP:LISTEN || echo "Port $port is free"
done
```

## 환경 변수

### 필수 환경 변수 (.env)
```bash
# GPU 설정
CUDA_VISIBLE_DEVICES=2           # 임베딩용 GPU
VLLM_CUDA_VISIBLE_DEVICES=0,1    # vLLM용 GPU

# 모델 설정
VLLM_CONTEXT_LENGTH=131072       # Nemotron 컨텍스트
VLLM_MAX_TOKENS=8192             # 최대 생성 토큰
```

### Conda 환경
```bash
# 환경 활성화
conda activate gait_rag

# Python 버전 확인
python --version  # Python 3.10+
```