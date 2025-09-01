# Medical Gait RAG WebUI

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-web.txt
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## Development

See documentation:
- [Implementation Guide](../WEBUI_IMPLEMENTATION.md)
- [Code Guidelines](../CODE_GUIDELINES.md)
- [Architecture](../WEBUI_ARCHITECTURE.md)
