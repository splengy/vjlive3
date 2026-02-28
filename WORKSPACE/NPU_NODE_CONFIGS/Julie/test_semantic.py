#!/usr/bin/env python3
"""Test semantic search."""
import memory

print("Testing semantic search...")
print(f"Vector DB path: {memory.VECTOR_DIR}")

# Try to get vector DB
vdb = memory.get_vector_db()
if vdb is not None:
    print(f"Vector DB initialized: {vdb}")
    try:
        count = vdb._collection.count()
        print(f"Collection count: {count}")
    except Exception as e:
        print(f"Error getting count: {e}")
else:
    print("Vector DB is None")

# Test search
print("\nPerforming test search for 'France'...")
results = memory.semantic_search("France", limit=5)
print(f"Search results count: {len(results)}")
for i, res in enumerate(results):
    print(f"  Result {i+1}: [{res.get('conversation_name')}] {res.get('content')[:100]}...")

