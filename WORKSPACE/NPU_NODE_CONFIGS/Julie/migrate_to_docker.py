"""Migrate 180K vectors from SQLite embedded Qdrant to Docker Qdrant server."""
import sys, time
sys.path.insert(0, '/home/happy/ai_env/lib/python3.12/site-packages')

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

BATCH_SIZE = 1000
SRC_PATH = '/home/happy/qdrant_data/vjlive_code'
DST_URL = 'http://localhost:6333'
COLLECTION = 'vjlive_code'

print('Connecting to source (SQLite)...')
src = QdrantClient(path=SRC_PATH)
info = src.get_collection(COLLECTION)
total = info.points_count
print(f'Source: {total} points')

# Get vector config from source
vec_size = info.config.params.vectors.size
print(f'Vector size: {vec_size}')

print('Connecting to Docker Qdrant...')
dst = QdrantClient(url=DST_URL)

# Create collection in Docker
dst.recreate_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=vec_size, distance=Distance.COSINE)
)
print(f'Created collection in Docker Qdrant')

# Batch migrate
offset = None
migrated = 0
start = time.time()

while True:
    result = src.scroll(
        collection_name=COLLECTION,
        limit=BATCH_SIZE,
        offset=offset,
        with_vectors=True,
        with_payload=True
    )
    points, next_offset = result
    if not points:
        break
    
    dst.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(
            id=p.id,
            vector=p.vector,
            payload=p.payload
        ) for p in points]
    )
    
    migrated += len(points)
    elapsed = time.time() - start
    rate = migrated / elapsed if elapsed > 0 else 0
    eta = (total - migrated) / rate if rate > 0 else 0
    print(f'  Migrated {migrated}/{total} ({rate:.0f}/s, ETA {eta:.0f}s)')
    
    offset = next_offset
    if next_offset is None:
        break

print(f'\nDone! Migrated {migrated} points in {time.time()-start:.1f}s')

# Verify
dst_info = dst.get_collection(COLLECTION)
print(f'Docker Qdrant: {dst_info.points_count} points')
