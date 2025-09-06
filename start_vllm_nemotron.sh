#!/bin/bash

# NVIDIA Nemotron-Nano-12B-v2 vLLM Server Startup Script
# 12.3B parameter Mamba-Transformer hybrid model

echo "Starting NVIDIA Nemotron-Nano-12B-v2"
echo "=========================================="

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate gait_rag

# GPU configuration
export CUDA_VISIBLE_DEVICES=4,5

# Model settings
MODEL_NAME="nvidia/NVIDIA-Nemotron-Nano-12B-v2"
SERVED_NAME="nemotron-nano-12b"
TENSOR_PARALLEL=2
CONTEXT_LENGTH=131072  # Official max model length
PORT=8000

echo "Environment: gait_rag (conda)"
echo "Model: $MODEL_NAME"
echo "Size: 12.3B parameters"
echo "Context Length: $CONTEXT_LENGTH tokens"
echo "Tensor Parallel Size: $TENSOR_PARALLEL GPUs"
echo "GPU Devices: $CUDA_VISIBLE_DEVICES"
echo "Port: $PORT"
echo "=========================================="

# Start vLLM server with Nemotron
# Note: Mamba-Transformer hybrid requires special cache settings
vllm serve $MODEL_NAME \
    --served-model-name $SERVED_NAME \
    --trust-remote-code \
    --max-model-len $CONTEXT_LENGTH \
    --tensor-parallel-size $TENSOR_PARALLEL \
    --gpu-memory-utilization 0.85 \
    --max-num-seqs 8 \
    --mamba_ssm_cache_dtype float32 \
    --dtype bfloat16 \
    --swap-space 4 \
    --disable-log-requests \
    --host 0.0.0.0 \
    --port $PORT \
    --enable-chunked-prefill

# Important notes:
# - mamba_ssm_cache_dtype float32 is required for accuracy
# - Reduce max-num-seqs if VRAM issues occur
# - Model uses BF16 precision natively