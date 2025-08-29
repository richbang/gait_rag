# vLLM Integration Guide

## Overview
The Medical Gait RAG system now supports answer generation using vLLM with the Seed-OSS-36B-Instruct-AWQ model. This integration allows the system to not only retrieve relevant documents but also generate comprehensive answers based on the retrieved context.

## Architecture

### Components
1. **VLLMClient** (`src/infrastructure/vllm_client.py`)
   - Handles communication with vLLM server
   - Constructs prompts with retrieved context
   - Manages HTTP connections and error handling

2. **Container Integration** (`src/container.py`)
   - Lazy-loaded vLLM client
   - Configurable via environment variables
   - Optional component (can run without vLLM)

3. **QA Endpoint** (`/qa` in `src/presentation/routes.py`)
   - Combines document retrieval with answer generation
   - Returns both generated answer and source documents
   - Falls back gracefully if vLLM is unavailable

## Configuration

### Environment Variables (.env)
```env
# vLLM Configuration
USE_VLLM=true                              # Enable/disable vLLM integration
VLLM_API_URL=http://localhost:8000/v1      # vLLM server endpoint
VLLM_MODEL=Seed-OSS-36B-Instruct-AWQ       # Model name as served
VLLM_MAX_TOKENS=4096                       # Max tokens to generate
VLLM_TEMPERATURE=0.1                       # Generation temperature
VLLM_CONTEXT_LENGTH=128000                 # Model context window
```

## Usage

### 1. Start vLLM Server
```bash
# Option 1: Use the provided script
./start_vllm_server.sh

# Option 2: Run manually
vllm serve QuantTrio/Seed-OSS-36B-Instruct-AWQ \
  --served-model-name Seed-OSS-36B-Instruct-AWQ \
  --max-model-len 128000 \
  --tensor-parallel-size 2 \
  --host 0.0.0.0 \
  --port 8000
```

### 2. Start RAG API Server
```bash
python -m src.main
```

### 3. Use the QA Endpoint

#### With vLLM (Answer Generation)
```python
import httpx

response = httpx.post(
    "http://localhost:8000/qa",
    json={
        "query": "What are the main gait parameters in stroke patients?",
        "limit": 5,
        "use_vllm": True  # Enable answer generation
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])} documents")
```

#### Without vLLM (Retrieval Only)
```python
response = httpx.post(
    "http://localhost:8000/qa",
    json={
        "query": "What are the main gait parameters in stroke patients?",
        "limit": 5,
        "use_vllm": False  # Disable answer generation
    }
)
```

## API Endpoints

### POST /qa
Question-answering endpoint with optional vLLM generation.

**Request Body:**
```json
{
    "query": "string",
    "limit": 5,
    "use_vllm": true,
    "document_types": ["RESEARCH_PAPER"],
    "disease_categories": ["STROKE"],
    "require_gait_params": false,
    "min_score": 0.0
}
```

**Response:**
```json
{
    "query": "string",
    "answer": "Generated answer from vLLM based on retrieved context",
    "sources": [
        {
            "chunk_id": "string",
            "document_id": "string",
            "content": "string",
            "page_number": 1,
            "score": 0.85,
            "has_gait_params": true
        }
    ],
    "total_sources": 5,
    "vllm_used": true
}
```

## Testing

Run the integration test:
```bash
python test_vllm_integration.py
```

This will test:
1. Health check
2. Basic search (without vLLM)
3. QA retrieval only (vLLM disabled)
4. QA with answer generation (vLLM enabled)

## Troubleshooting

### vLLM Server Not Responding
- Check if vLLM server is running: `curl http://localhost:8000/v1/models`
- Verify GPU memory is sufficient for the model
- Check vLLM server logs for errors

### Answer Generation Fails
- Ensure `USE_VLLM=true` in .env
- Verify vLLM server URL is correct
- Check that the model name matches the served model
- Monitor vLLM server resource usage

### Performance Issues
- Adjust `VLLM_MAX_TOKENS` for shorter responses
- Increase `VLLM_TEMPERATURE` for more creative answers
- Consider using fewer search results in context (`limit` parameter)

## GPU Configuration

The system supports separate GPU configuration:
- **Embeddings**: Set via `EMBEDDING_DEVICE` (e.g., `cuda:5`)
- **vLLM**: Configured when starting vLLM server with `--tensor-parallel-size`

This allows optimal resource allocation across multiple GPUs.

## Development Notes

### Adding New Models
To use a different model:
1. Update `VLLM_MODEL` in .env
2. Adjust `start_vllm_server.sh` with new model path
3. Update context length if needed
4. Test prompt format compatibility

### Customizing Prompts
Edit the system prompt in `VLLMClient._construct_prompt()` or pass custom prompts:
```python
answer = await vllm_client.generate(
    prompt=query,
    context=context,
    system_prompt="Custom instructions here"
)
```

### Monitoring
- RAG API logs: Standard output when running `src.main`
- vLLM logs: Check vLLM server output
- Performance metrics: Available at vLLM's `/metrics` endpoint