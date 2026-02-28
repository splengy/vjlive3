import requests
import sys
import os

# Add /home/happy/outback to path to find classifier if needed
sys.path.append("/home/happy/outback")
import classifier

# Config
TARGET_FILE = "/home/happy/fix_freq_rk3588.sh"
RAG_API = "http://127.0.0.1:8080/ingest"

def ingest_weird():
    if not os.path.exists(TARGET_FILE):
        print(f"File {TARGET_FILE} not found!")
        return

    print(f"Reading {TARGET_FILE}...")
    with open(TARGET_FILE, 'r') as f:
        content = f.read()

    print("Classifying content via TheMaxx...")
    category = classifier.classify_text("fix_freq_rk3588.sh", content[:500]) # Summary limit
    print(f"Category assigned: {category}")

    print("Ingesting to Julie RAG...")
    payload = {
        "content": content,
        "subject": "System Script: fix_freq_rk3588.sh",
        "source": TARGET_FILE,
        "media_type": "text/code",
        "collection": category
    }

    try:
        r = requests.post(RAG_API, json=payload, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Ingest Error: {e}")

if __name__ == "__main__":
    ingest_weird()
