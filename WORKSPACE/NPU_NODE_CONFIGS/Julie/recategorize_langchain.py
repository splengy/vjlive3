import chromadb
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor

# Configuration
CHROMA_PATH = "/home/happy/ai_library_stable/vector_db"
OLLAMA_URL = "http://192.168.1.112:11434/api/generate"
MODEL = "qwen2.5-coder:7b" # User requested speed
BATCH_SIZE = 10

CATEGORIES = [
    "physics_classical", "physics_quantum", "physics_astro", "chemistry_organic", "chemistry_material", 
    "earth_sciences", "biology_genetics", "biology_zoology", "biology_botany", "medicine_anatomy", 
    "medicine_pathology", "neuroscience", "cs_ai_machine_learning", "cs_software_engineering", 
    "cs_cybersecurity", "engineering_mechanical", "engineering_electrical", "engineering_civil", 
    "mathematics_pure", "mathematics_applied", "history_ancient", "history_medieval", "history_modern", 
    "archaeology_anthropology", "philosophy_ethics", "philosophy_metaphysics", "religion_theology", 
    "mythology_folklore", "literature_fiction", "literature_poetry", "visual_arts_classic", "design_fashion", 
    "music_theory", "cinema_theatre", "economics_finance", "business_management", "politics_law", 
    "psychology_clinical", "sociology_culture", "general"
]

def classify_batch(titles):
    prompt = f"""
Input: List of article titles.
Output: JSON list of categories from the following allowed list: {CATEGORIES}
Titles:
{json.dumps(titles)}

Return ONLY the JSON list of strings, in the same order.
"""
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=30)
        
        if r.status_code == 200:
            res = r.json().get("response")
            return json.loads(res)
    except Exception as e:
        print(f"Classification Error: {e}")
    
    return ["general"] * len(titles)

def process_migration():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    src_col = client.get_collection("langchain")
    
    # Get all IDs and Metadata (don't fetch full content yet to save RAM)
    # Chroma peek/get might crash on 48k. Using limit based iteration.
    total = src_col.count()
    print(f"Found {total} misplaced items...")
    
    offset = 0
    limit = 100
    
    moved_count = 0
    
    while offset < total:
        batch = src_col.get(limit=limit, offset=offset, include=["metadatas", "documents"])
        ids = batch['ids']
        metas = batch['metadatas']
        docs = batch['documents']
        
        if not ids: break
        
        # Sub-batch for LLM
        for i in range(0, len(ids), BATCH_SIZE):
            chunk_ids = ids[i:i+BATCH_SIZE]
            chunk_metas = metas[i:i+BATCH_SIZE]
            chunk_docs = docs[i:i+BATCH_SIZE]
            
            titles = [m.get('title', d[:50]) for m, d in zip(chunk_metas, chunk_docs)]
            
            categories = classify_batch(titles)
            
            # Move items
            for j, cat in enumerate(categories):
                if cat not in CATEGORIES: cat = "general"
                
                target_col = client.get_or_create_collection(cat)
                
                # Add to new, Delete from old? 
                # Doing Add first safer.
                try:
                    target_col.add(
                        ids=[chunk_ids[j]],
                        metadatas=[chunk_metas[j]],
                        documents=[chunk_docs[j]]
                    )
                    # src_col.delete(ids=[chunk_ids[j]]) # Optional: Delete immediately or later
                    print(f"Moved '{titles[j]}' -> {cat}")
                    moved_count += 1
                except Exception as e:
                    print(f"Failed to move {chunk_ids[j]}: {e}")

        offset += limit
        print(f"Processed {offset}/{total}")

if __name__ == "__main__":
    process_migration()
