"""
qdrant-legacy — MCP server for querying legacy VJLive code from Qdrant.

Exposes tools for agents to search real legacy code from VJlive-1, VJlive-2,
and VJlive-3 codebases stored in Qdrant on Julie (192.168.1.60:6333).

NO local embedding model — queries use Qdrant scroll + keyword matching,
or optionally call Julie's embedding service for vector search.

Tools:
  search_legacy  — keyword or vector search for legacy code
  get_file_chunks — get all chunks from a specific legacy file
  legacy_stats   — collection statistics (point count, index status)
  list_files     — list unique files in the collection (by codebase)

Run: python run_qdrant_legacy.py
"""
from __future__ import annotations

import json
import logging
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# Resolve repo root
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_logger = logging.getLogger("vjlive3.mcp.qdrant_legacy")

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://192.168.1.60:6333")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "vjlive_code")

# Remote embedding via Julie's Python environment (optional)
EMBED_HOST = os.environ.get("EMBED_HOST", "192.168.1.60")


def _qdrant_request(endpoint: str, method: str = "GET",
                     payload: dict = None, timeout: int = 30) -> dict:
    """Make a request to the Qdrant REST API."""
    url = f"{QDRANT_URL}/{endpoint}"
    data = json.dumps(payload).encode() if payload else None
    headers = {"Content-Type": "application/json"} if data else {}

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        _logger.error(f"Qdrant request failed: {e}")
        return {"error": str(e)}


def _remote_embed(text: str) -> Optional[list]:
    """
    Get embedding vector from Julie's embedding service.
    Falls back to None if unavailable.
    """
    # Try calling Julie's Python environment for embedding
    import subprocess
    try:
        cmd = [
            "ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
            f"happy@{EMBED_HOST}",
            f'/home/happy/ai_env/bin/python3 -c "'
            f'from sentence_transformers import SentenceTransformer; '
            f'import json; '
            f'm = SentenceTransformer(\"all-MiniLM-L6-v2\"); '
            f'v = m.encode(\"{text}\").tolist(); '
            f'print(json.dumps(v))'
            f'"'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return json.loads(result.stdout.strip())
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        _logger.warning(f"Remote embedding failed: {e}")
    return None


# ─── FastMCP Server ─────────────────────────────────────────────────

mcp = FastMCP(
    name="qdrant-legacy",
    instructions=(
        "Query real legacy VJLive code from Qdrant. "
        "Use search_legacy to find relevant code from VJlive-1, VJlive-2, and VJlive-3 codebases. "
        "Results include actual file paths and code content — use these as references, not hallucinations."
    ),
)


@mcp.tool()
def search_legacy(
    query: str,
    limit: int = 5,
    codebase: str = "",
    use_vector: bool = False,
) -> list[dict]:
    """
    Search legacy VJLive codebases for relevant code.

    Args:
        query: Search query — class name, function name, concept, or description.
               Examples: "VideoSource", "depth camera astra", "render pipeline shader"
        limit: Maximum number of results (default 10, max 50)
        codebase: Filter to specific codebase: "vjlive1", "vjlive2", "vjlive3", or "" for all.
        use_vector: If True, use semantic vector search via Julie's embedding model.
                    If False (default), use fast keyword matching.

    Returns:
        List of matching code chunks with file path, codebase, score, and content.
    """
    limit = min(limit, 15)

    if use_vector:
        vector = _remote_embed(query)
        if vector:
            payload = {
                "vector": vector,
                "limit": limit,
                "with_payload": True,
            }
            if codebase:
                payload["filter"] = {
                    "must": [{"key": "codebase", "match": {"value": codebase}}]
                }

            result = _qdrant_request(
                f"collections/{COLLECTION}/points/search",
                method="POST", payload=payload
            )

            if "error" not in result:
                return [
                    {
                        "filepath": p.get("payload", {}).get("filepath", "unknown"),
                        "codebase": p.get("payload", {}).get("codebase", "unknown"),
                        "chunk_index": p.get("payload", {}).get("chunk_index", 0),
                        "score": round(p.get("score", 0), 4),
                        "content": p.get("payload", {}).get("content", "")[:1000] + "\n...[TRUNCATED]",
                    }
                    for p in result.get("result", [])
                ]
            # Fall through to keyword search if vector fails

    # Keyword scroll — fast, no embedding needed
    payload = {
        "limit": min(limit * 20, 500),  # over-fetch then filter
        "with_payload": True,
    }
    if codebase:
        payload["filter"] = {
            "must": [{"key": "codebase", "match": {"value": codebase}}]
        }

    result = _qdrant_request(
        f"collections/{COLLECTION}/points/scroll",
        method="POST", payload=payload
    )

    if "error" in result:
        return [{"error": result["error"]}]

    points = result.get("result", {}).get("points", [])
    query_terms = query.lower().split()
    matching = []

    for p in points:
        content = p.get("payload", {}).get("content", "").lower()
        filepath = p.get("payload", {}).get("filepath", "").lower()
        searchable = content + " " + filepath

        # Score by how many query terms match
        hits = sum(1 for term in query_terms if term in searchable)
        if hits > 0:
            matching.append({
                "filepath": p.get("payload", {}).get("filepath", "unknown"),
                "codebase": p.get("payload", {}).get("codebase", "unknown"),
                "chunk_index": p.get("payload", {}).get("chunk_index", 0),
                "score": round(hits / len(query_terms), 2),
                "content": p.get("payload", {}).get("content", "")[:2000],
            })

    # Sort by score descending
    matching.sort(key=lambda x: x["score"], reverse=True)
    return matching[:limit]


@mcp.tool()
def get_file_chunks(
    filepath: str,
    codebase: str = "",
    max_chunks: int = 20,
) -> list[dict]:
    """
    Get all code chunks from a specific legacy file.

    Args:
        filepath: Full or partial file path to search for.
        codebase: Optional codebase filter: "vjlive1", "vjlive2", "vjlive3"
        max_chunks: Maximum number of chunks to return (default 20).

    Returns:
        List of all chunks from the matching file, ordered by chunk index.
    """
    filter_conditions = [
        {"key": "filepath", "match": {"value": filepath}}
    ]
    if codebase:
        filter_conditions.append(
            {"key": "codebase", "match": {"value": codebase}}
        )

    payload = {
        "limit": 100,
        "with_payload": True,
        "filter": {"must": filter_conditions},
    }

    result = _qdrant_request(
        f"collections/{COLLECTION}/points/scroll",
        method="POST", payload=payload
    )

    if "error" in result:
        return [{"error": result["error"]}]

    points = result.get("result", {}).get("points", [])
    chunks = sorted(
        [
            {
                "filepath": p.get("payload", {}).get("filepath", ""),
                "codebase": p.get("payload", {}).get("codebase", ""),
                "chunk_index": p.get("payload", {}).get("chunk_index", 0),
                "content": p.get("payload", {}).get("content", "")[:1000] + "\n...[TRUNCATED]",
            }
            for p in points
        ],
        key=lambda x: x["chunk_index"],
    )
    return chunks[:max_chunks]


@mcp.tool()
def legacy_stats() -> dict:
    """
    Get Qdrant collection statistics — point count, index status.

    Returns:
        Dictionary with total points, indexed points, and collection status.
    """
    result = _qdrant_request(f"collections/{COLLECTION}")

    if "error" in result:
        return {"error": result["error"]}

    r = result.get("result", {})
    return {
        "collection": COLLECTION,
        "qdrant_url": QDRANT_URL,
        "total_points": r.get("points_count", 0),
        "indexed_points": r.get("indexed_vectors_count", 0),
        "status": r.get("status", "unknown"),
    }


@mcp.tool()
def list_files(
    codebase: str = "",
    path_contains: str = "",
    limit: int = 50,
) -> list[str]:
    """
    List unique file paths in the Qdrant collection.

    Args:
        codebase: Filter by codebase: "vjlive1", "vjlive2", "vjlive3", or "" for all.
        path_contains: Filter to files whose path contains this string.
                       Example: "core/" to list only core modules.
        limit: Maximum files to return (default 50).

    Returns:
        List of unique file paths.
    """
    filter_conditions = []
    if codebase:
        filter_conditions.append(
            {"key": "codebase", "match": {"value": codebase}}
        )

    payload = {
        "limit": 500,
        "with_payload": ["filepath"],
    }
    if filter_conditions:
        payload["filter"] = {"must": filter_conditions}

    result = _qdrant_request(
        f"collections/{COLLECTION}/points/scroll",
        method="POST", payload=payload
    )

    if "error" in result:
        return [f"Error: {result['error']}"]

    points = result.get("result", {}).get("points", [])
    files = set()
    for p in points:
        fp = p.get("payload", {}).get("filepath", "")
        if path_contains and path_contains not in fp:
            continue
        files.add(fp)

    return sorted(files)[:limit]


def main() -> None:
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1] == "--test":
        _logger.info("Running Qdrant legacy smoke test...")
        stats = legacy_stats()
        _logger.info(f"Stats: {stats}")
        _logger.info("Smoke test: %s",
                      "PASS" if stats.get("total_points", 0) > 0 else "FAIL")
        _sys.exit(0 if stats.get("total_points", 0) > 0 else 1)

    port = 8002
    try:
        import uvicorn
        import starlette
    except ImportError:
        _logger.error("SSE transport requires 'uvicorn' and 'starlette'.")
        _sys.exit(1)

    _logger.info("qdrant-legacy MCP server starting (stdio)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
