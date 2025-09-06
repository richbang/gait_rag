"""
vLLM Model Configuration
Switch between different models for comparison
"""

# Model configurations
VLLM_MODELS = {
    "seed-oss": {
        "name": "Seed-OSS-36B-Instruct-AWQ",
        "api_url": "http://localhost:8000/v1",
        "max_tokens": 4096,
        "temperature": 0.1,
        "context_length": 128000,
        "description": "36B AWQ quantized model, excellent for Korean",
        "thinking_tags": ["<:think>", "</:think>", "/seed:thinking", "/seed"]
    },
    "gpt-oss": {
        "name": "gpt-oss-20b",
        "api_url": "http://localhost:8002/v1",
        "max_tokens": 4096,
        "temperature": 0.1,
        "context_length": 128000,
        "description": "20B MXFP4 model with configurable reasoning",
        "thinking_tags": ["<thinking>", "</thinking>"]  # Adjust based on actual model behavior
    }
}

# Default model selection
DEFAULT_MODEL = "seed-oss"  # Change to "gpt-oss" to test the new model

def get_model_config(model_key=None):
    """Get model configuration"""
    if model_key is None:
        model_key = DEFAULT_MODEL
    
    if model_key not in VLLM_MODELS:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(VLLM_MODELS.keys())}")
    
    return VLLM_MODELS[model_key]