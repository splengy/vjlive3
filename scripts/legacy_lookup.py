#!/usr/bin/env python3
"""
Legacy Code Lookup — Query Qdrant for relevant legacy code.

Usage:
    python scripts/legacy_lookup.py "VideoSource"
    python scripts/legacy_lookup.py "depth camera astra" --limit 5
    python scripts/legacy_lookup.py "render pipeline" --codebase vjlive2

Requires: sentence-transformers, qdrant running on Julie (192.168.1.60:6333)
Falls back to REST API if qdrant-client not installed.
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

QDRANT_URL = "http://192.168.1.60:6333"
COLLECTION = "vjlive_code"

# Try to use sentence-transformers for embedding, fall back to keyword search
try:
    from sentence_transformers import SentenceTransformer
    _model = None

    def get_model():
        global _model
        if _model is None:
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        return _model

    def embed_query(text):
        return get_model().encode(text).tolist()

    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


def search_qdrant_vector(query_text, limit=10, codebase_filter=None):
    """Search using vector similarity (requires sentence-transformers)."""
    vector = embed_query(query_text)

    payload = {
        "vector": vector,
        "limit": limit,
        "with_payload": True,
    }

    if codebase_filter:
        payload["filter"] = {
            "must": [
                {"key": "codebase", "match": {"value": codebase_filter}}
            ]
        }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get("result", [])
    except urllib.error.URLError as e:
        print(f"ERROR: Cannot reach Qdrant at {QDRANT_URL}: {e}", file=sys.stderr)
        sys.exit(1)


def search_qdrant_scroll(query_text, limit=10, codebase_filter=None):
    """Fallback: scroll through points and filter by text match."""
    print("WARNING: No sentence-transformers installed. Using scroll fallback (slower).",
          file=sys.stderr)

    payload = {
        "limit": limit,
        "with_payload": True,
    }

    if codebase_filter:
        payload["filter"] = {
            "must": [
                {"key": "codebase", "match": {"value": codebase_filter}}
            ]
        }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            points = result.get("result", {}).get("points", [])
            # Filter by text content
            query_lower = query_text.lower()
            matching = []
            for p in points:
                content = p.get("payload", {}).get("content", "")
                if query_lower in content.lower():
                    matching.append(p)
            return matching[:limit]
    except urllib.error.URLError as e:
        print(f"ERROR: Cannot reach Qdrant at {QDRANT_URL}: {e}", file=sys.stderr)
        sys.exit(1)


def format_result(point, index):
    """Format a single search result for display."""
    payload = point.get("payload", {})
    score = point.get("score", "N/A")
    filepath = payload.get("filepath", "unknown")
    codebase = payload.get("codebase", "unknown")
    chunk_idx = payload.get("chunk_index", "?")
    content = payload.get("content", "")

    # Truncate content for display
    lines = content.strip().split("\n")
    preview = "\n".join(lines[:15])
    if len(lines) > 15:
        preview += f"\n    ... ({len(lines) - 15} more lines)"

    return f"""
--- Result {index + 1} (score: {score}) ---
File: {filepath}
Codebase: {codebase} | Chunk: {chunk_idx}

{preview}
"""


def check_collection():
    """Verify Qdrant collection exists and has data."""
    try:
        req = urllib.request.Request(f"{QDRANT_URL}/collections/{COLLECTION}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            count = data.get("result", {}).get("points_count", 0)
            indexed = data.get("result", {}).get("indexed_vectors_count", 0)
            return count, indexed
    except urllib.error.URLError:
        return 0, 0


def main():
    parser = argparse.ArgumentParser(
        description="Search legacy VJLive codebases via Qdrant"
    )
    parser.add_argument("query", help="Search query (class name, function, concept)")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Max results")
    parser.add_argument("--codebase", "-c", choices=["vjlive1", "vjlive2", "vjlive3"],
                        help="Filter to specific codebase")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON")
    parser.add_argument("--status", action="store_true", help="Show collection status")
    args = parser.parse_args()

    # Status check
    count, indexed = check_collection()
    if args.status or count == 0:
        print(f"Qdrant collection '{COLLECTION}': {count} points, {indexed} indexed")
        if count == 0:
            print("ERROR: Collection is empty. Is ingestion running?")
            sys.exit(1)
        if args.status:
            sys.exit(0)

    # Search
    if HAS_EMBEDDINGS:
        results = search_qdrant_vector(args.query, args.limit, args.codebase)
    else:
        results = search_qdrant_scroll(args.query, args.limit, args.codebase)

    if not results:
        print(f"No results for '{args.query}'")
        sys.exit(0)

    if args.raw:
        print(json.dumps(results, indent=2))
    else:
        print(f"Found {len(results)} results for '{args.query}'"
              f" ({count} total points, {indexed} indexed)")
        for i, r in enumerate(results):
            print(format_result(r, i))


if __name__ == "__main__":
    main()
