import chromadb
import sys

DB_PATH = "/home/happy/ai_library_stable/vector_db"

def sample_langchain():
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        col = client.get_collection("langchain")
        count = col.count()
        print(f"--- Collection 'langchain' ({count} docs) ---")
        
        # Peek first 5
        res = col.peek(limit=5)
        
        for i in range(len(res['documents'])):
            doc = res['documents'][i]
            meta = res['metadatas'][i]
            print(f"Doc {i+1}:")
            print(f"  Metadata: {meta}")
            print(f"  Snippet: {doc[:200]}...")
            print("")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sample_langchain()
