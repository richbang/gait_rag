#!/bin/bash

# Model Configuration Setter
# Sets environment variables for different models

echo "📋 Model Configuration"
echo "====================="
echo "1) Seed-OSS-36B-AWQ"
echo "2) GPT-OSS-20B"
echo ""
read -p "Select model (1-2): " choice

case $choice in
    1)
        export VLLM_MODEL="Seed-OSS-36B-Instruct-AWQ"
        export VLLM_MAX_TOKENS=4096
        echo "✅ Set to Seed-OSS-36B-AWQ"
        echo ""
        echo "To start the server, run:"
        echo "  ./start_vllm_seed.sh"
        ;;
    2)
        export VLLM_MODEL="gpt-oss-20b"
        export VLLM_MAX_TOKENS=8192
        echo "✅ Set to GPT-OSS-20B"
        echo ""
        echo "To start the server, run:"
        echo "  ./start_vllm_gptoss.sh"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Environment variables set:"
echo "  VLLM_MODEL=$VLLM_MODEL"
echo "  VLLM_MAX_TOKENS=$VLLM_MAX_TOKENS"
echo ""
echo "Note: These environment variables will be used by the RAG API"