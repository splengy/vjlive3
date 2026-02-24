#!/usr/bin/env python3
"""
VJLive Code RAG Ingestion Script — Runs on Julie-Winters (Orange Pi 5)

Ingests both VJLive-2 and VJLive3 codebases into a fresh Qdrant
collection for semantic code search. This gives agents instant access
to "find me all legacy code related to depth effects" without
filename-based guessing.

Usage:
    scp this to Julie-Winters, then:
    /home/happy/ai_env/bin/python3 ingest_codebases.py

Requires: qdrant_client, sentence_transformers (both already on Julie)
"""

import os
import sys
import hashlib
import time
from pathlib import Path
from typing import List, Dict

# Use Julie's AI environment
sys.path.insert(0, '/home/happy/ai_env/lib/python3.12/site-packages')

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Configuration
COLLECTION_NAME = "vjlive_code"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Same model julie_rag.py uses
VECTOR_SIZE = 384  # Dimension for all-MiniLM-L6-v2
QDRANT_PATH = "/home/happy/qdrant_data/vjlive_code"

# Codebases to index — mounted via NFS or copied
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

# File extensions to index — Python, shaders, web nodes, configs, docs
INDEX_EXTENSIONS = {
    ".py", ".md", ".yaml", ".yml", ".json",
    ".glsl", ".frag", ".vert",
    ".js", ".jsx", ".ts", ".tsx",
    ".html", ".css",
    ".sh", ".txt",
}

# Directories to skip — virtualenvs and binary artifact dirs
SKIP_DIRS = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache",
    "eggs", ".eggs", "dist", "build",
    # Python virtualenvs (these contain torch/nvidia/cublas .so files)
    ".venv", "venv", "env", "vjlive-env", "ai_env",
    "site-packages", "lib64",
    # Compiled artifacts
    ".tox", "htmlcov", "*.egg-info",
}

# Binary extensions to NEVER index (even if in allowed dirs)
SKIP_EXTENSIONS = {
    ".so", ".o", ".a", ".dylib", ".whl", ".egg", ".tar", ".gz",
    ".zip", ".wasm", ".bin", ".dat", ".pkl", ".pt", ".pth",
    ".onnx", ".rkllm", ".rknn", ".png", ".jpg", ".jpeg",
    ".gif", ".ico", ".svg", ".mp4", ".mp3", ".wav",
}

# Max file size to index (skip huge files)
MAX_FILE_SIZE = 30_000  # 30KB — keeps it fast on ARM


def chunk_code(content: str, filepath: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
    """
    Split a source file into overlapping chunks for embedding.

    Each chunk includes metadata about which file and line range it came from.
    """
    lines = content.splitlines()
    chunks = []
    i = 0

    while i < len(lines):
        end = min(i + chunk_size // 50, len(lines))  # ~50 chars per line avg
        chunk_lines = lines[i:end]
        chunk_text = "\n".join(chunk_lines)

        if chunk_text.strip():  # Skip empty chunks
            chunks.append({
                "text": chunk_text,
                "filepath": filepath,
                "start_line": i + 1,
                "end_line": end,
                "total_lines": len(lines),
            })

        # Move forward with overlap
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

    for filepath in base.rglob("*"):
        # Skip directories in the skip list
        if any(skip in filepath.parts for skip in SKIP_DIRS):
            continue

        # Skip binary files
        if filepath.suffix in SKIP_EXTENSIONS:
            continue

        # Only index known extensions
        if filepath.suffix not in INDEX_EXTENSIONS:
            continue

        # Skip files that are too large
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


def main():
    print("=" * 60)
    print("VJLive Code RAG Ingestion")
    print("=" * 60)

    # Initialize embedding model
    print(f"\n📦 Loading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("   ✅ Model loaded")

    # Initialize Qdrant (local storage mode)
    print(f"\n📦 Initializing Qdrant at: {QDRANT_PATH}")
    os.makedirs(QDRANT_PATH, exist_ok=True)
    client = QdrantClient(path=QDRANT_PATH)

    # Delete existing collection if it exists (fresh start)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"   🗑️  Deleted existing '{COLLECTION_NAME}' collection")
    except Exception:
        pass

    # Create fresh collection
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )
    print(f"   ✅ Created fresh '{COLLECTION_NAME}' collection")

    # Collect and index files from each codebase
    total_chunks = 0
    total_files = 0
    point_id = 0

    for codebase_name, config in CODEBASES.items():
        print(f"\n📂 Indexing: {config['label']}")
        print(f"   Path: {config['path']}")

        files = collect_files(config["path"], codebase_name)
        print(f"   Found: {len(files)} files")
        total_files += len(files)

        # Process files in batches
        batch_points = []
        for file_info in files:
            chunks = chunk_code(
                file_info["content"],
                file_info["filepath"],
            )

            for chunk in chunks:
                # Build the text to embed: filepath context + code
                embed_text = (
                    f"File: {file_info['filepath']} "
                    f"(lines {chunk['start_line']}-{chunk['end_line']})\n"
                    f"Codebase: {config['label']}\n\n"
                    f"{chunk['text']}"
                )

                # Generate embedding
                embedding = model.encode(embed_text).tolist()

                # Create Qdrant point
                batch_points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk["text"],
                        "filepath": file_info["filepath"],
                        "codebase": codebase_name,
                        "codebase_label": config["label"],
                        "extension": file_info["extension"],
                        "start_line": chunk["start_line"],
                        "end_line": chunk["end_line"],
                        "total_lines": chunk["total_lines"],
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
                    total_chunks += len(batch_points)
                    print(f"   📤 Indexed {total_chunks} chunks...")
                    batch_points = []

        # Flush remaining
        if batch_points:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch_points,
            )
            total_chunks += len(batch_points)

        print(f"   ✅ {codebase_name}: {len(files)} files indexed")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"✅ INGESTION COMPLETE")
    print(f"   Files: {total_files}")
    print(f"   Chunks: {total_chunks}")
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Storage: {QDRANT_PATH}")
    print(f"{'=' * 60}")

    # Quick test search
    print(f"\n🔍 Test search: 'depth acid fractal shader'")
    test_embedding = model.encode("depth acid fractal shader").tolist()
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=test_embedding,
        limit=3,
    )
    for r in results:
        print(f"   [{r.score:.3f}] {r.payload['codebase_label']} — {r.payload['filepath']}:{r.payload['start_line']}")


if __name__ == "__main__":
    main()
