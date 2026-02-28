import requests
import json
import os

url = 'http://localhost:5002/chat'
prompt = "What's in this image?"
image_path = "/AI-ENV/tools/rknn-llm/examples/multimodal_model_demo/data/demo.jpg"

print(f"Testing text-only chat...")
try:
    r = requests.post(url, json={'prompt': 'Hello, what can you do?'}, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Text test failed: {e}")

print(f"\nTesting multimodal chat with {image_path}...")
try:
    payload = {'prompt': prompt, 'image_path': image_path}
    r = requests.post(url, json=payload, timeout=60)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Multimodal test failed: {e}")
