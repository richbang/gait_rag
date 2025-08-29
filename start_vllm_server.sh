#!/bin/bash

# vLLM Server Startup Script for Seed-OSS-36B-Instruct-AWQ
# This script starts the vLLM server with optimized settings

# Load from .env if exists, otherwise use default
if [ -f .env ]; then
    export $(grep -E '^VLLM_CONTEXT_LENGTH=' .env | xargs)
fi
CONTEXT_LENGTH=${VLLM_CONTEXT_LENGTH:-128000}

echo "🚀 Starting vLLM Server with Seed-OSS-36B-Instruct-AWQ"
echo "Context Length: $CONTEXT_LENGTH"
echo "Tensor Parallel Size: 2 GPUs"
echo "Port: 8000"
echo "----------------------------------------"

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
    --tensor-parallel-size 2 \
    --trust-remote-code \
    --disable-log-requests \
    --host 0.0.0.0 \
    --port 8000