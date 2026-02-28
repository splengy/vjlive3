import chromadb
import sys

DB_PATH = "/home/happy/ai_library_stable/vector_db"

print(f"Connecting to ChromaDB at {DB_PATH}...")
sys.stdout.flush()

try:
    client = chromadb.PersistentClient(path=DB_PATH)
    print("Listing collections...")
    collections = client.list_collections()
    print(f"Found {len(collections)} collections.")
    sys.stdout.flush()
    
    total = 0
    sorted_cols = sorted(collections, key=lambda c: c.name)
    
    print("| Category | Article Count |")
    print("|----------|---------------|")
    
    for col in sorted_cols:
        try:
            count = col.count()
            print(f"| {col.name} | {count} |")
            total += count
            sys.stdout.flush()
        except Exception as e:
            print(f"| {col.name} | ERROR: {e} |")
            sys.stdout.flush()
            
    print(f"\n**TOTAL DOCUMENTS: {total}**")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
