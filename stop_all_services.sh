#!/bin/bash

# Medical Gait RAG System - Stop Script

echo "================================================"
echo "Medical Gait RAG System - Stopping All Services"
echo "================================================"

# Stop Frontend
echo "Stopping Frontend..."
pkill -f "react-scripts start" 2>/dev/null
pkill -f "node.*3000" 2>/dev/null

# Stop WebUI Backend
echo "Stopping WebUI Backend..."
pkill -f "uvicorn main:app.*8003" 2>/dev/null
pkill -f "python main.py" 2>/dev/null

# Stop RAG API
echo "Stopping RAG API..."
pkill -f "python api.py" 2>/dev/null
pkill -f "uvicorn.*8001" 2>/dev/null

# Stop vLLM
echo "Stopping vLLM server..."
pkill -f "vllm serve" 2>/dev/null

sleep 2

echo ""
echo "================================================"
echo "All services stopped!"
echo "================================================"