#!/usr/bin/env python3
"""
Test script to compare vLLM models performance
Tests both Seed-OSS-36B-AWQ and GPT-OSS-20B
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any

# Test queries in Korean
TEST_QUERIES = [
    "파킨슨병 환자의 보행 특징은 무엇인가요?",
    "뇌졸중 후 보행 재활 방법에 대해 설명해주세요",
    "정상 보행 주기의 각 단계를 설명해주세요",
]

async def test_model(api_url: str, model_name: str, query: str) -> Dict[str, Any]:
    """Test a single model with a query"""
    
    payload = {
        "model": model_name,
        "prompt": f"""You are a medical AI assistant. Answer in Korean.

### User:
{query}

### Assistant (in Korean):""",
        "max_tokens": 1000,
        "temperature": 0.1,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            start_time = time.time()
            response = await client.post(
                f"{api_url}/completions",
                json=payload
            )
            response.raise_for_status()
            elapsed_time = time.time() - start_time
            
            result = response.json()
            generated_text = result["choices"][0]["text"]
            
            # Get token counts
            prompt_tokens = result.get("usage", {}).get("prompt_tokens", 0)
            completion_tokens = result.get("usage", {}).get("completion_tokens", 0)
            
            return {
                "success": True,
                "response": generated_text[:500],  # First 500 chars
                "full_response": generated_text,
                "time": elapsed_time,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "tokens_per_second": completion_tokens / elapsed_time if elapsed_time > 0 else 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "time": 0
            }

async def compare_models():
    """Compare both models"""
    
    models = [
        {
            "name": "Seed-OSS-36B-AWQ",
            "api_url": "http://localhost:8000/v1",
            "port": 8000
        },
        {
            "name": "gpt-oss-20b",
            "api_url": "http://localhost:8002/v1",
            "port": 8002
        }
    ]
    
    print("=" * 80)
    print("vLLM Model Comparison Test")
    print("=" * 80)
    
    for model_config in models:
        print(f"\n📊 Testing {model_config['name']} on port {model_config['port']}")
        print("-" * 40)
        
        # Check if model server is running
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                health_resp = await client.get(f"{model_config['api_url']}/models")
                if health_resp.status_code != 200:
                    print(f"❌ Model server not available on port {model_config['port']}")
                    print(f"   Start with: ./start_vllm_{'gptoss' if 'gpt-oss' in model_config['name'] else 'server'}.sh")
                    continue
        except:
            print(f"❌ Model server not available on port {model_config['port']}")
            print(f"   Start with: ./start_vllm_{'gptoss' if 'gpt-oss' in model_config['name'] else 'server'}.sh")
            continue
        
        total_time = 0
        total_tokens = 0
        
        for i, query in enumerate(TEST_QUERIES, 1):
            print(f"\nQuery {i}: {query[:50]}...")
            result = await test_model(
                model_config['api_url'],
                model_config['name'],
                query
            )
            
            if result['success']:
                print(f"✅ Response time: {result['time']:.2f}s")
                print(f"   Tokens: {result['completion_tokens']} @ {result['tokens_per_second']:.1f} tok/s")
                print(f"   Answer preview: {result['response'][:100]}...")
                
                total_time += result['time']
                total_tokens += result['completion_tokens']
            else:
                print(f"❌ Error: {result['error']}")
        
        if total_time > 0:
            print(f"\n📈 Model Summary:")
            print(f"   Average response time: {total_time/len(TEST_QUERIES):.2f}s")
            print(f"   Average tokens/second: {total_tokens/total_time:.1f}")
    
    print("\n" + "=" * 80)
    print("Comparison complete!")
    print("=" * 80)

async def test_memory_usage():
    """Check GPU memory usage for each model"""
    import subprocess
    
    print("\n🔍 GPU Memory Usage:")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                parts = line.split(', ')
                if len(parts) >= 4:
                    gpu_id = parts[0]
                    gpu_name = parts[1]
                    mem_used = float(parts[2])
                    mem_total = float(parts[3])
                    usage_pct = (mem_used / mem_total) * 100
                    
                    if gpu_id in ['4', '5']:  # Your GPUs
                        print(f"GPU {gpu_id} ({gpu_name}): {mem_used:.0f}/{mem_total:.0f} MB ({usage_pct:.1f}%)")
    except Exception as e:
        print(f"Could not get GPU memory info: {e}")

if __name__ == "__main__":
    # Run comparison
    asyncio.run(compare_models())
    asyncio.run(test_memory_usage())