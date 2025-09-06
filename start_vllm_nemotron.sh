#!/bin/bash

# NVIDIA Nemotron-Nano-12B vLLM 서버 시작 스크립트
# 모델: 12.3B 파라미터 Mamba-Transformer 하이브리드
# 컨텍스트: 131,072 토큰 (128K)

echo "Starting NVIDIA Nemotron-Nano-12B-v2"
echo "=========================================="

# Conda 환경 활성화
source ~/miniconda3/etc/profile.d/conda.sh
conda activate gait_rag

# GPU 설정 (RTX A5000 #4, #5 사용)
export CUDA_VISIBLE_DEVICES=4,5

# 모델 설정
MODEL_NAME="nvidia/NVIDIA-Nemotron-Nano-12B-v2"
SERVED_NAME="nemotron-nano-12b"
TENSOR_PARALLEL=2
CONTEXT_LENGTH=131072  # 공식 최대 컨텍스트 길이
PORT=8000

echo "Environment: gait_rag (conda)"
echo "Model: $MODEL_NAME"
echo "Size: 12.3B parameters"
echo "Context Length: $CONTEXT_LENGTH tokens"
echo "Tensor Parallel Size: $TENSOR_PARALLEL GPUs"
echo "GPU Devices: $CUDA_VISIBLE_DEVICES"
echo "Port: $PORT"
echo "=========================================="

# vLLM 서버 시작
# 주의: Mamba-Transformer 하이브리드는 특별한 캐시 설정 필요
vllm serve $MODEL_NAME \
    --served-model-name $SERVED_NAME \
    --trust-remote-code \
    --max-model-len $CONTEXT_LENGTH \
    --tensor-parallel-size $TENSOR_PARALLEL \
    --gpu-memory-utilization 0.85 \  # GPU 메모리 85% 사용\
    --max-num-seqs 8 \  # 동시 처리 시퀀스 수\
    --mamba_ssm_cache_dtype float32 \  # Mamba SSM 캐시 타입 (정확도 필수)\
    --dtype bfloat16 \  # BF16 정밀도 사용\
    --swap-space 4 \  # 스왑 공간 4GB\
    --disable-log-requests \
    --host 0.0.0.0 \
    --port $PORT \
    --enable-chunked-prefill  # 청크 단위 prefill 활성화

# 중요 사항:
# - mamba_ssm_cache_dtype float32는 정확도를 위해 필수
# - VRAM 부족 시 max-num-seqs 값 감소
# - 모델은 기본적으로 BF16 정밀도 사용
# - 총 VRAM 사용량: 약 22GB per GPU