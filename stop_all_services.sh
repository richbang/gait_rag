#!/bin/bash

# Medical Gait RAG System - 서비스 종료 스크립트
# 모든 서비스를 안전하게 종료

echo "================================================"
echo "Medical Gait RAG System - Stopping All Services"
echo "================================================"

# 1. Frontend 종료 (포트 3000)
echo "Stopping Frontend..."
pkill -f "react-scripts start" 2>/dev/null
pkill -f "node.*3000" 2>/dev/null
pkill -f "npm start" 2>/dev/null

# 2. WebUI Backend 종료 (포트 8003)
echo "Stopping WebUI Backend..."
pkill -f "uvicorn main:app.*8003" 2>/dev/null
pkill -f "python main.py" 2>/dev/null
pkill -f "python.*backend/main.py" 2>/dev/null

# 3. RAG API 종료 (포트 8001)
echo "Stopping RAG API..."
pkill -f "python api.py" 2>/dev/null
pkill -f "uvicorn.*8001" 2>/dev/null
pkill -f "api:app.*8001" 2>/dev/null

# 4. vLLM 서버 종료 (포트 8000)
echo "Stopping vLLM server..."
pkill -f "vllm serve" 2>/dev/null
pkill -f "vllm.entrypoints" 2>/dev/null

# 프로세스 종료 대기
sleep 2

# 포트 상태 확인
echo ""
echo "Checking port status..."
for port in 3000 8003 8001 8000; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  WARNING: Port $port is still in use"
    else
        echo "  Port $port is free"
    fi
done

echo ""
echo "================================================"
echo "All services stopped!"
echo "================================================"