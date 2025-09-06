#!/bin/bash

# Seed-OSS-36B-AWQ vLLM Server Startup Script
# Uses conda environment with existing vLLM installation

echo "🚀 Starting Seed-OSS-36B-AWQ Model"
echo "=================================="

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate gait_rag

# GPU configuration
export CUDA_VISIBLE_DEVICES=4,5

# Model settings
MODEL_NAME="QuantTrio/Seed-OSS-36B-Instruct-AWQ"
SERVED_NAME="Seed-OSS-36B-Instruct-AWQ"
TENSOR_PARALLEL=2
CONTEXT_LENGTH=128000
PORT=8000

echo "Environment: gait_rag (conda)"
echo "Model: $MODEL_NAME"
echo "Context Length: $CONTEXT_LENGTH tokens"
echo "Tensor Parallel Size: $TENSOR_PARALLEL GPUs"
echo "GPU Devices: $CUDA_VISIBLE_DEVICES"
echo "Port: $PORT"
echo "=================================="

# Start vLLM server with Seed-OSS
vllm serve $MODEL_NAME \
    --served-model-name $SERVED_NAME \
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
    --port $PORT