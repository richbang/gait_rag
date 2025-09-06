# Medical Gait RAG - 설치 가이드

## 시스템 요구사항
- Ubuntu 20.04+ (WSL2 지원)
- NVIDIA GPU (24GB+ VRAM)
- Python 3.10+
- Node.js 18+
- 50GB+ 디스크 공간

## 빠른 설치

### 1. 프로젝트 클론
```bash
git clone git@github.com:richbang/gait_rag.git
cd gait_rag
```

### 2. Conda 환경 생성
```bash
conda create -n gait_rag python=3.10
conda activate gait_rag
```

### 3. Python 패키지 설치
```bash
pip install -r requirements.txt
pip install vllm==0.6.4.post1 safetensors
```

### 4. 프론트엔드 설정
```bash
cd frontend
npm install
cd ..
```

### 5. 환경 변수 설정
```bash
cp .env.example .env
# GPU 설정에 맞게 .env 파일 수정
```

### 6. 문서 인덱싱 (선택사항)
```bash
# data/ 폴더에 PDF 파일들을 넣고
python index_papers.py
```

### 7. 서비스 시작
```bash
chmod +x *.sh
./start_all_services.sh
```

## WSL 특별 설정

### GPU 설정 확인
```bash
# WSL에서
nvidia-smi
```

### GPU 메모리 부족 시
`start_vllm_nemotron.sh` 수정:
```bash
# GPU 설정 변경
export CUDA_VISIBLE_DEVICES=0  # WSL은 보통 0
TENSOR_PARALLEL=1  # GPU 1개 사용

# 메모리 사용량 줄이기
--gpu-memory-utilization 0.8  # 0.95에서 낮춤
--max-num-seqs 4  # 8에서 낮춤
```

### WSL 메모리 설정
Windows에서 `%UserProfile%\.wslconfig` 파일 생성:
```ini
[wsl2]
memory=32GB
processors=8
swap=8GB
```

## 서비스 접속
- **Web UI**: http://localhost:3000
- **기본 계정**: 
  - Username: `demouser`
  - Password: `demo12345`

## 문제 해결

### 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :8000
# 프로세스 종료
kill -9 <PID>
```

### 서비스 종료
```bash
./stop_all_services.sh
```

## 로그 확인
```bash
tail -f logs/rag_api.log
tail -f logs/webui_backend.log
```