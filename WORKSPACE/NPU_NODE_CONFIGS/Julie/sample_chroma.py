import chromadb
import sys
import random

DB_PATH = "/home/happy/ai_library_stable/vector_db"

def sample_collection(client, col_name, n=3):
    try:
        col = client.get_collection(col_name)
        count = col.count()
        if count == 0:
            print(f"Collection '{col_name}' is empty.")
            return

        print(f"--- Sampling '{col_name}' ({count} docs) ---")
        # Get random items if possible, or just first few
        res = col.peek(limit=n) 
        
        for i in range(len(res['documents'])):
            doc = res['documents'][i]
            meta = res['metadatas'][i]
            print(f"Doc {i+1}:")
            print(f"  Metadata: {meta}")
            print(f"  Content specific len: {len(doc)}")
            print(f"  Snippet: {doc[:100]}...")
            print("")
            
    except Exception as e:
        print(f"Error sampling {col_name}: {e}")

try:
    client = chromadb.PersistentClient(path=DB_PATH)
    # Sample meaningful collections
    sample_collection(client, "history_modern") # Likely Gutenberg
    sample_collection(client, "biology_genetics") # Likely Wiki
    sample_collection(client, "general") # Fallback
except Exception as e:
    print(f"DB Error: {e}")
