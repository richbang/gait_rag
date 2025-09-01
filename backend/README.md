# Medical Gait RAG WebUI Backend

FastAPI backend for Medical Gait RAG system with authentication and conversation management.

## Architecture

```
backend/
├── auth/         # Authentication module (JWT-based)
├── chat/         # Chat & conversation management
├── core/         # Core utilities (config, security, middleware)
├── database/     # Database models and session management
└── main.py       # FastAPI application entry point
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements-web.txt
```

### 2. Environment Variables

Create `.env` file:
```
APP_NAME=Medical Gait RAG WebUI
APP_VERSION=1.0.0
ENVIRONMENT=development
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# Database
DATABASE_URL=sqlite:///./gait_rag.db

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### 3. Run Server

```bash
python main.py
```

Server will start on `http://localhost:8003`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (returns JWT token)
- `GET /api/v1/auth/me` - Get current user info

### Conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations` - List user conversations
- `GET /api/v1/conversations/{id}` - Get conversation with messages
- `DELETE /api/v1/conversations/{id}` - Delete conversation
- `POST /api/v1/conversations/{id}/messages` - Send message

### RAG Integration
- `POST /api/v1/rag/search` - Search documents
- `POST /api/v1/rag/qa` - Question answering with vLLM

## Service Dependencies

- **Port 8000**: vLLM server (Seed-OSS-36B-Instruct-AWQ)
- **Port 8001**: RAG API server
- **Port 8003**: WebUI Backend (this service)

## Database Schema

- **users**: User accounts
- **conversations**: Chat conversations
- **messages**: Chat messages with RAG sources
- **contexts**: Saved contexts (future feature)

## Testing

```bash
# Run all services first:
# 1. Start vLLM: ./start_vllm_server.sh
# 2. Start RAG API: python api.py
# 3. Start Backend: python main.py

# Test with curl:
curl -X POST http://localhost:8003/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
```

## Notes

- JWT tokens expire after 7 days (10080 minutes)
- Database uses SQLite for simplicity
- All timestamps are in UTC
- Supports Korean language queries