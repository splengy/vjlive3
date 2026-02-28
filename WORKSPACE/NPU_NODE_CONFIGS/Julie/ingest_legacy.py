#!/usr/bin/env python3
"""
VJLive Code RAG Ingestion Script — Runs on Julie-Winters (Orange Pi 5)

Ingests VJLive-1 and VJLive-2 codebases into Qdrant (Docker) for
semantic code search. Agents query this to find real legacy code.

RESUME-CAPABLE: Queries Qdrant for already-ingested filepaths and
skips them. Safe to re-run after interruption (power outage, crash).

Usage:
    scp this to Julie-Winters, then:
    nohup /home/happy/ai_env/bin/python3 ingest_codebases.py > ingest.log 2>&1 &

Requires: qdrant_client, sentence_transformers (both already on Julie)
"""

import os
import sys
import hashlib
import time
import json
from pathlib import Path
from typing import List, Dict, Set

# Use Julie's AI environment
sys.path.insert(0, '/home/happy/ai_env/lib/python3.12/site-packages')

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

# Configuration
COLLECTION_NAME = "vjlive_code"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_SIZE = 384
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

# Checkpoint file — saves progress so we can resume
CHECKPOINT_FILE = "/home/happy/ingest_checkpoint.json"

# Codebases to index
CODEBASES = {
    "vjlive1": {
        "path": "/home/happy/vjlive_codebases/vjlive1",
        "label": "VJlive (Original)",
    },
    "vjlive2": {
        "path": "/home/happy/vjlive_codebases/vjlive2",
        "label": "VJlive-2 (Legacy)",
    },
}

# File extensions to index
INDEX_EXTENSIONS = {
    ".py", ".md", ".yaml", ".yml", ".json",
    ".glsl", ".frag", ".vert",
    ".js", ".jsx", ".ts", ".tsx",
    ".html", ".css",
    ".sh", ".txt",
}

# Directories to skip
SKIP_DIRS = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache",
    "eggs", ".eggs", "dist", "build",
    ".venv", "venv", "env", "vjlive-env", "ai_env",
    "site-packages", "lib64",
    ".tox", "htmlcov",
    "node_modules",
}

# Binary extensions to never index
SKIP_EXTENSIONS = {
    ".so", ".o", ".a", ".dylib", ".whl", ".egg", ".tar", ".gz",
    ".zip", ".wasm", ".bin", ".dat", ".pkl", ".pt", ".pth",
    ".onnx", ".rkllm", ".rknn", ".png", ".jpg", ".jpeg",
    ".gif", ".ico", ".svg", ".mp4", ".mp3", ".wav",
    ".pyc", ".pyo",
}

MAX_FILE_SIZE = 30_000  # 30KB


def chunk_code(content: str, filepath: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
    """Split a source file into overlapping chunks for embedding."""
    lines = content.splitlines()
    chunks = []
    i = 0

    while i < len(lines):
        end = min(i + chunk_size // 50, len(lines))
        chunk_lines = lines[i:end]
        chunk_text = "\n".join(chunk_lines)

        if chunk_text.strip():
            chunks.append({
                "text": chunk_text,
                "filepath": filepath,
                "start_line": i + 1,
                "end_line": end,
                "total_lines": len(lines),
            })

        step = max(1, (end - i) - overlap // 50)
        i += step
        if i >= len(lines):
            break

    return chunks


def collect_files(base_path: str, codebase_name: str) -> List[Dict]:
    """Collect all indexable files from a codebase."""
    files = []
    base = Path(base_path)

    if not base.exists():
        print(f"  ⚠️  Path not found: {base_path}")
        return files

    for filepath in sorted(base.rglob("*")):
        if any(skip in filepath.parts for skip in SKIP_DIRS):
            continue
        if filepath.suffix in SKIP_EXTENSIONS:
            continue
        if filepath.suffix not in INDEX_EXTENSIONS:
            continue

        try:
            size = filepath.stat().st_size
            if size > MAX_FILE_SIZE or size == 0:
                continue
        except OSError:
            continue

        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
            rel_path = str(filepath.relative_to(base))
            files.append({
                "content": content,
                "filepath": rel_path,
                "codebase": codebase_name,
                "absolute_path": str(filepath),
                "extension": filepath.suffix,
                "size_bytes": size,
            })
        except Exception as e:
            print(f"  ⚠️  Could not read {filepath}: {e}")

    return files


def get_existing_filepaths(client: QdrantClient, codebase: str) -> Set[str]:
    """
    Query Qdrant for all filepaths already ingested for a codebase.
    THIS IS THE RESUME LOGIC — skip files we've already done.
    """
    existing = set()
    offset = None

    print(f"  📋 Querying Qdrant for already-ingested files ({codebase})...")

    while True:
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key="codebase", match=MatchValue(value=codebase))]
            ),
            limit=1000,
            offset=offset,
            with_payload=["filepath"],
            with_vectors=False,
        )

        points, next_offset = results
        for point in points:
            fp = point.payload.get("filepath", "")
            if fp:
                existing.add(fp)

        if next_offset is None:
            break
        offset = next_offset

    print(f"  📋 Found {len(existing)} already-ingested files for {codebase}")
    return existing


def save_checkpoint(data: dict):
    """Save progress checkpoint to disk."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_checkpoint() -> dict:
    """Load progress checkpoint if it exists."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {}


def get_next_point_id(client: QdrantClient) -> int:
    """Get the next available point ID by checking collection size."""
    try:
        info = client.get_collection(COLLECTION_NAME)
        return info.points_count + 1
    except Exception:
        return 0


def main():
    start_time = time.time()

    print("=" * 60)
    print("VJLive Code RAG Ingestion (RESUME-CAPABLE)")
    print("=" * 60)

    # Initialize embedding model
    print(f"\n📦 Loading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("   ✅ Model loaded")

    # Connect to Qdrant Docker instance (NOT local files)
    print(f"\n📦 Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Create collection ONLY if it doesn't exist
    try:
        info = client.get_collection(COLLECTION_NAME)
        existing_count = info.points_count
        print(f"   ✅ Collection '{COLLECTION_NAME}' exists: {existing_count} points")
    except Exception:
        print(f"   🆕 Creating new collection '{COLLECTION_NAME}'")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        existing_count = 0

    # Get next available point ID
    point_id = get_next_point_id(client)
    print(f"   Next point ID: {point_id}")

    # Process each codebase
    total_new_chunks = 0
    total_skipped_files = 0
    total_new_files = 0

    for codebase_name, config in CODEBASES.items():
        print(f"\n📂 Indexing: {config['label']}")
        print(f"   Path: {config['path']}")

        # RESUME LOGIC: Get already-ingested filepaths
        existing_fps = get_existing_filepaths(client, codebase_name)

        # Collect all files
        files = collect_files(config["path"], codebase_name)
        print(f"   Found: {len(files)} total files")

        # Filter out already-ingested files
        new_files = [f for f in files if f["filepath"] not in existing_fps]
        skipped = len(files) - len(new_files)
        print(f"   ⏭️  Skipping: {skipped} already-ingested files")
        print(f"   🆕 New files to process: {len(new_files)}")

        total_skipped_files += skipped
        total_new_files += len(new_files)

        if not new_files:
            print(f"   ✅ {codebase_name}: nothing new to ingest")
            continue

        # Process new files in batches
        batch_points = []
        files_done = 0

        for file_info in new_files:
            chunks = chunk_code(
                file_info["content"],
                file_info["filepath"],
            )

            for chunk in chunks:
                embed_text = (
                    f"File: {file_info['filepath']} "
                    f"(lines {chunk['start_line']}-{chunk['end_line']})\n"
                    f"Codebase: {config['label']}\n\n"
                    f"{chunk['text']}"
                )

                embedding = model.encode(embed_text).tolist()

                batch_points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk["text"],
                        "content": chunk["text"],  # alias for MCP server
                        "filepath": file_info["filepath"],
                        "codebase": codebase_name,
                        "codebase_label": config["label"],
                        "extension": file_info["extension"],
                        "start_line": chunk["start_line"],
                        "end_line": chunk["end_line"],
                        "total_lines": chunk["total_lines"],
                        "chunk_index": len([c for c in chunks if c["start_line"] <= chunk["start_line"]]) - 1,
                        "absolute_path": file_info["absolute_path"],
                    },
                ))
                point_id += 1

                # Upsert in batches of 100
                if len(batch_points) >= 100:
                    client.upsert(
                        collection_name=COLLECTION_NAME,
                        points=batch_points,
                    )
                    total_new_chunks += len(batch_points)
                    batch_points = []

                    # Progress log every 500 chunks
                    if total_new_chunks % 500 == 0:
                        elapsed = time.time() - start_time
                        rate = total_new_chunks / elapsed if elapsed > 0 else 0
                        print(f"   📤 {total_new_chunks} new chunks | "
                              f"{files_done}/{len(new_files)} files | "
                              f"{rate:.1f} chunks/sec")

                        # Save checkpoint
                        save_checkpoint({
                            "codebase": codebase_name,
                            "files_done": files_done,
                            "chunks_done": total_new_chunks,
                            "point_id": point_id,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        })

            files_done += 1

        # Flush remaining batch
        if batch_points:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch_points,
            )
            total_new_chunks += len(batch_points)

        print(f"   ✅ {codebase_name}: {len(new_files)} new files, "
              f"{total_new_chunks} new chunks indexed")

    # Final summary
    elapsed = time.time() - start_time
    final_info = client.get_collection(COLLECTION_NAME)

    print(f"\n{'=' * 60}")
    print(f"✅ INGESTION COMPLETE")
    print(f"   New files:     {total_new_files}")
    print(f"   Skipped files: {total_skipped_files}")
    print(f"   New chunks:    {total_new_chunks}")
    print(f"   Total points:  {final_info.points_count}")
    print(f"   Time:          {elapsed:.0f}s ({elapsed/60:.1f}m)")
    print(f"   Collection:    {COLLECTION_NAME}")
    print(f"{'=' * 60}")

    # Clean up checkpoint
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print("   🧹 Checkpoint file cleaned up")

    # Quick test search
    print(f"\n🔍 Test search: 'depth acid fractal shader'")
    test_embedding = model.encode("depth acid fractal shader").tolist()
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=test_embedding,
        limit=3,
    )
    for r in results:
        print(f"   [{r.score:.3f}] {r.payload['codebase_label']} — "
              f"{r.payload['filepath']}:{r.payload['start_line']}")


if __name__ == "__main__":
    main()
