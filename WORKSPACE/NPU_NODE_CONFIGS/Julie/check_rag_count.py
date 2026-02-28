#!/usr/bin/env python3
import sys
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

print("Checking Library Vector DB status...")
DB_DIR = "/mnt/ai_library/vector_db"

try:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vdb = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    count = vdb._collection.count()
    print(f"Total documents/chunks in library: {count}")
    
    # Show some sample metadata
    if count > 0:
        print("\nRecent sources:")
        results = vdb.get(limit=5)
        for i, meta in enumerate(results['metadatas']):
            print(f"  [{i+1}] {meta.get('source', 'Unknown')} ({meta.get('format', 'N/A')})")
except Exception as e:
    print(f"Error: {e}")
