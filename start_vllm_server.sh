#!/bin/bash

# vLLM Server Startup Script for Seed-OSS-36B-Instruct-AWQ
# This script starts the vLLM server with optimized settings

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate gait_rag

# Load GPU configuration from .env if exists
if [ -f .env ]; then
    # Read VLLM_CUDA_VISIBLE_DEVICES from .env
    VLLM_CUDA_VISIBLE_DEVICES=$(grep -E '^VLLM_CUDA_VISIBLE_DEVICES=' .env | cut -d'=' -f2 | cut -d'#' -f1 | tr -d ' ')
    # Read VLLM_TENSOR_PARALLEL_SIZE from .env
    VLLM_TENSOR_PARALLEL_SIZE=$(grep -E '^VLLM_TENSOR_PARALLEL_SIZE=' .env | cut -d'=' -f2 | cut -d'#' -f1 | tr -d ' ')
    # Read VLLM_CONTEXT_LENGTH from .env
    VLLM_CONTEXT_LENGTH=$(grep -E '^VLLM_CONTEXT_LENGTH=' .env | cut -d'=' -f2 | cut -d'#' -f1 | tr -d ' ')
fi

# Set defaults if not found in .env
export CUDA_VISIBLE_DEVICES=${VLLM_CUDA_VISIBLE_DEVICES:-4,5}
TENSOR_PARALLEL=${VLLM_TENSOR_PARALLEL_SIZE:-2}
CONTEXT_LENGTH=${VLLM_CONTEXT_LENGTH:-128000}

echo "🚀 Starting vLLM Server with Seed-OSS-36B-Instruct-AWQ"
echo "Environment: gait_rag"
echo "Context Length: $CONTEXT_LENGTH"
echo "Tensor Parallel Size: $TENSOR_PARALLEL GPUs"
echo "GPU Devices: $CUDA_VISIBLE_DEVICES"
echo "----------------------------------------"

# Start vLLM server
vllm serve \
    QuantTrio/Seed-OSS-36B-Instruct-AWQ \
    --served-model-name Seed-OSS-36B-Instruct-AWQ \
    --enable-auto-tool-choice \
    --tool-call-parser seed_oss \
    --swap-space 2 \
    --max-num-seqs 5 \
    --max-model-len $CONTEXT_LENGTH \
    --max-seq-len-to-capture $CONTEXT_LENGTH \
    --gpu-memory-utilization 0.9 \
    --tensor-parallel-size $TENSOR_PARALLEL \
    --trust-remote-code \
    --disable-log-requests \
    --host 0.0.0.0 \
    --port 8000