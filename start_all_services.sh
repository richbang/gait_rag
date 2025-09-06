#!/bin/bash

# Medical Gait RAG System - Startup Script

echo "================================================"
echo "Medical Gait RAG System - Starting All Services"
echo "================================================"

# Check if vLLM is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✓ vLLM already running on port 8000"
else
    echo "Starting vLLM server..."
    cd /data1/home/ict12/Kmong/medical_gait_rag
    ./start_vllm_server.sh &
    sleep 10
    echo "✓ vLLM started on port 8000"
fi

# Check if RAG API is already running
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    echo "✓ RAG API already running on port 8001"
else
    echo "Starting RAG API..."
    cd /data1/home/ict12/Kmong/medical_gait_rag
    python api.py > logs/rag_api.log 2>&1 &
    sleep 5
    echo "✓ RAG API started on port 8001"
fi

# Check if WebUI Backend is already running
if lsof -Pi :8003 -sTCP:LISTEN -t >/dev/null ; then
    echo "✓ WebUI Backend already running on port 8003"
else
    echo "Starting WebUI Backend..."
    cd /data1/home/ict12/Kmong/medical_gait_rag/backend
    python main.py > ../logs/webui_backend.log 2>&1 &
    sleep 3
    echo "✓ WebUI Backend started on port 8003"
fi

# Check if Frontend is already running
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✓ Frontend already running on port 3000"
else
    echo "Starting Frontend..."
    cd /data1/home/ict12/Kmong/medical_gait_rag/frontend
    npm start > ../logs/frontend.log 2>&1 &
    sleep 5
    echo "✓ Frontend started on port 3000"
fi

echo ""
echo "================================================"
echo "All services are running!"
echo "================================================"
echo ""
echo "Service URLs:"
echo "  - Frontend:      http://localhost:3000"
echo "  - WebUI Backend: http://localhost:8003"
echo "  - RAG API:       http://localhost:8001"
echo "  - vLLM Server:   http://localhost:8000"
echo ""
echo "Default test account:"
echo "  Username: demouser"
echo "  Password: demo12345"
echo ""
echo "To stop all services, run: ./stop_all_services.sh"
echo "================================================"