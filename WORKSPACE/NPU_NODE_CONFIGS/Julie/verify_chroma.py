import chromadb
import sys
DB_PATH = "/home/happy/ai_library_stable/vector_db"

print(f"Connecting to ChromaDB at {DB_PATH}...")
try:
    client = chromadb.PersistentClient(path=DB_PATH)
    collections = client.list_collections()
    print(f"Collections Found: {[c.name for c in collections]}")
    
    total = 0
    for col in collections:
        count = col.count()
        print(f"Collection '{col.name}': {count} docs")
        total += count
        
    print(f"TOTAL DOCUMENTS: {total}")
except Exception as e:
    print(f"Error reading DB: {e}")
