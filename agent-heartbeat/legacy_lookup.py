#!/usr/bin/env python3
"""
Legacy Code Lookup — queries Qdrant for legacy VJLive code.

Usage:
    python3 legacy_lookup.py ascii_effect
    python3 legacy_lookup.py analog_tv --limit 20
    python3 legacy_lookup.py "datamosh bad trip" --collection vjlive_code
"""

import argparse
import json
import sys
import urllib.request

QDRANT_URL = "http://192.168.1.60:6333"
COLLECTION = "vjlive_code"


def search_by_filepath(query: str, limit: int = 10, collection: str = COLLECTION) -> list:
    """Search Qdrant by filepath substring match."""
    url = f"{QDRANT_URL}/collections/{collection}/points/scroll"
    payload = json.dumps({
        "limit": limit,
        "with_payload": True,
        "filter": {
            "must": [{
                "key": "filepath",
                "match": {"text": query}
            }]
        }
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result", {}).get("points", [])
    except Exception as e:
        print(f"ERROR: Qdrant query failed: {e}", file=sys.stderr)
        return []


def search_by_content(query: str, limit: int = 10, collection: str = COLLECTION) -> list:
    """Search Qdrant by text content substring match."""
    url = f"{QDRANT_URL}/collections/{collection}/points/scroll"
    payload = json.dumps({
        "limit": limit,
        "with_payload": True,
        "filter": {
            "must": [{
                "key": "text",
                "match": {"text": query}
            }]
        }
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result", {}).get("points", [])
    except Exception as e:
        print(f"ERROR: Qdrant content search failed: {e}", file=sys.stderr)
        return []


def normalize_query(query: str) -> list[str]:
    """Turn 'class AdaptiveContrastEffect' into useful search terms."""
    import re
    # Strip 'class ' prefix
    q = re.sub(r'^class\s+', '', query.strip())
    terms = [q]
    
    # CamelCase → snake_case
    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', q).lower()
    if snake != q.lower():
        terms.append(snake)
    
    # Remove common suffixes for broader search
    for suffix in ('_effect', '_engine', '_node', '_plugin'):
        if snake.endswith(suffix):
            terms.append(snake[:-len(suffix)])
            break
    
    return list(dict.fromkeys(terms))  # dedupe preserving order


def main():
    parser = argparse.ArgumentParser(description="Legacy Code Lookup via Qdrant")
    parser.add_argument("query", help="Module name or search term (e.g. ascii_effect, datamosh)")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--collection", default=COLLECTION, help="Qdrant collection")
    parser.add_argument("--content", action="store_true", help="Search by content instead of filepath")
    args = parser.parse_args()

    search_terms = normalize_query(args.query) if not args.content else [args.query]
    results = []

    for term in search_terms:
        if not results:
            results = search_by_filepath(term, args.limit, args.collection)
        if not results:
            results = search_by_content(term, args.limit, args.collection)
        if results:
            break

    if not results:
        print(f"NO RESULTS for '{args.query}' (tried: {', '.join(search_terms)})")
        sys.exit(1)

    print(f"# Found {len(results)} legacy code snippets for '{args.query}'\n")
    for i, point in enumerate(results, 1):
        payload = point.get("payload", {})
        filepath = payload.get("filepath", "unknown")
        codebase = payload.get("codebase_label", payload.get("codebase", ""))
        start = payload.get("start_line", "?")
        end = payload.get("end_line", "?")
        text = payload.get("text", payload.get("content", ""))

        print(f"## [{i}] {filepath} (L{start}-{end}) [{codebase}]")
        print(f"```")
        # Trim to first 60 lines to avoid flooding
        lines = text.split("\n")
        print("\n".join(lines[:60]))
        if len(lines) > 60:
            print(f"... ({len(lines) - 60} more lines)")
        print(f"```\n")


if __name__ == "__main__":
    main()
