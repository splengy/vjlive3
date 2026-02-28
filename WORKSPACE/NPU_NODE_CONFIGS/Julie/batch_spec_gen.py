#!/usr/bin/env python3
"""
VJLive3 Batch Spec Generator v3 — Qdrant-Powered, Dual Template

Queries Qdrant for real legacy code, feeds it to Qwen3-4B via rkllama,
generates specs using either the CORE or PLUGIN template.

Usage:
    python3 batch_spec_gen.py                    # Generate all pending core specs
    python3 batch_spec_gen.py --type plugin      # Generate plugin specs
    python3 batch_spec_gen.py --items 5          # Generate only 5 specs
    python3 batch_spec_gen.py --dry-run          # Show what would be generated
"""
import os
import json
import time
import urllib.request
import urllib.error
import sys

# ─── Configuration ───────────────────────────────────────────────────
RKLLAMA_URL = "http://localhost:8888"
MODEL = "Qwen3-4B-Instruct-2507_w8a8_g128_1.2.2_rk3588"
QDRANT_URL = "http://localhost:6333"
COLLECTION = "vjlive_code"
OUTPUT_DIR = "/home/happy/generated_specs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Core Architecture Items (Priority 1) ───────────────────────────
CORE_ITEMS = [
    # (task_id, module_name, qdrant_queries)
    ("P1-R3", "VideoSourceAbstraction", ["VideoSource", "camera", "depth", "astra", "realsense", "webcam"]),
    ("P1-R2", "RenderPipeline", ["render", "framebuffer", "shader", "opengl", "gpu", "pipeline"]),
    ("P1-P1", "PluginSystem", ["Effect", "plugin", "registry", "loader", "sandbox"]),
    ("P1-R4", "AudioMIDIEngine", ["audio", "midi", "beat", "frequency", "bpm", "fft"]),
    ("P1-R5", "DMXHardwareOutput", ["dmx", "artnet", "laser", "led", "fixture"]),
    ("P1-R6", "SyncTimecode", ["timecode", "ltc", "mtc", "ntp", "sync", "clock"]),
    ("P1-R7", "WebUIServer", ["websocket", "web_server", "web_ui", "flask", "remote"]),
    ("P1-C1", "StateManager", ["state", "persistence", "save", "load", "config", "preset"]),
    ("P1-C2", "DepthProcessor", ["depth", "depth_map", "depth_process", "point_cloud", "distance"]),
    ("P1-C3", "VisionPipeline", ["vision", "tracking", "skeleton", "pose", "body", "hand"]),
    ("P1-C4", "AgentSystem", ["agent", "auto_vj", "crowd_reader", "autonomous"]),
    ("P1-C5", "NetworkTransport", ["spout", "ndi", "network", "stream", "rtmp", "syphon"]),
]

# ─── Plugin Items (Priority 2 — extracted from BOARD.md patterns) ──
# These will be auto-discovered from BOARD.md eventually,
# but here are the key ones for the first batch
PLUGIN_ITEMS = [
    ("P3-VD01", "DepthBlur", ["depth_blur", "DepthBlurEffect", "blur"]),
    ("P3-VD02", "DepthEdgeGlow", ["depth_edge", "edge_glow", "DepthEdgeGlow"]),
    ("P3-VD03", "DepthColorGrade", ["depth_color", "color_grade", "DepthColorGrade"]),
    ("P3-VD04", "DepthPointCloud", ["point_cloud", "PointCloud", "depth_point"]),
    ("P3-VD05", "DepthDataMux", ["depth_mux", "DepthDataMux", "data_mux"]),
    ("P3-EXT01", "AudioReactiveWave", ["audio_reactive", "wave", "AudioWave"]),
    ("P3-EXT02", "BeatPulse", ["beat_pulse", "BeatPulse", "pulse"]),
    ("P3-EXT03", "ParticleField", ["particle", "ParticleField", "emitter"]),
    ("P3-EXT04", "GlitchDatamosh", ["glitch", "datamosh", "Datamosh"]),
    ("P3-EXT05", "FractalGenerator", ["fractal", "mandelbrot", "julia", "Fractal"]),
]


def qdrant_search(queries, limit_per_query=3):
    """Query Qdrant for legacy code matching multiple search terms."""
    all_results = []

    for query in queries:
        payload = {
            "limit": 200,
            "with_payload": True,
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "%s/collections/%s/points/scroll" % (QDRANT_URL, COLLECTION),
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                points = result.get("result", {}).get("points", [])

                query_lower = query.lower()
                matching = []
                for p in points:
                    content = p.get("payload", {}).get("content", "")
                    filepath = p.get("payload", {}).get("filepath", "")
                    if query_lower in content.lower() or query_lower in filepath.lower():
                        matching.append({
                            "filepath": filepath,
                            "codebase": p.get("payload", {}).get("codebase", "unknown"),
                            "content": content[:500],
                        })
                        if len(matching) >= limit_per_query:
                            break

                all_results.extend(matching)
        except Exception as e:
            print("  Warning: Qdrant query '%s' failed: %s" % (query, e))

    # Deduplicate by filepath
    seen = set()
    unique = []
    for r in all_results:
        if r["filepath"] not in seen:
            seen.add(r["filepath"])
            unique.append(r)

    return unique[:10]  # Cap at 10 references


def format_legacy_context(results):
    """Format Qdrant results into context for the prompt."""
    if not results:
        return "No legacy code found in Qdrant."

    lines = ["Here is REAL legacy code from previous VJLive versions:\n"]
    for r in results:
        lines.append("--- %s (%s) ---" % (r["filepath"], r["codebase"]))
        lines.append(r["content"])
        lines.append("")

    return "\n".join(lines)


def call_rkllama(prompt, max_retries=3):
    """Call rkllama API to generate text."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }
    data = json.dumps(payload).encode()

    for attempt in range(max_retries):
        req = urllib.request.Request(
            "%s/api/generate" % RKLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read())
                return result.get("response", "")
        except Exception as e:
            print("  Attempt %d failed: %s" % (attempt + 1, e))
            if attempt < max_retries - 1:
                time.sleep(5)

    return None


CORE_PROMPT = """You are writing a technical specification for VJLive3, a real-time Python/OpenGL visual performance application.

This is a CORE ARCHITECTURE module — it provides infrastructure that plugins and other systems depend on.

Write a spec for: {module_name} (Task ID: {task_id})

{legacy_context}

Use EXACTLY this format with ALL sections:

## Task: {task_id} -- {module_name}

**What This Module Does**
2-3 sentences describing the purpose.

---

## Architecture Decisions
- **Pattern:** [design pattern used]
- **Rationale:** Why this pattern
- **Constraints:** What this must guarantee

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
(Fill from the legacy code above — use REAL file paths)

---

## Public Interface

```python
# Real class/function signatures based on legacy code
```

---

## Platform Abstraction

| Platform | Implementation | Hardware | Notes |
|----------|---------------|----------|-------|

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|

---

## Dependencies
- External and internal dependencies

---

## What This Module Does NOT Do
- Explicit scope boundaries

---

## Edge Cases and Error Handling

| Scenario | Expected Behavior |
|----------|------------------|

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|

**Minimum coverage:** 80%

---

## Definition of Done
- [ ] Spec reviewed
- [ ] Legacy references verified
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs
"""

PLUGIN_PROMPT = """You are writing a technical specification for VJLive3, a real-time Python/OpenGL visual performance application. Each plugin processes video frames at 60 FPS.

This is a PLUGIN — it extends the visual pipeline with a specific effect.

Write a spec for: {module_name} (Task ID: {task_id})

{legacy_context}

Use EXACTLY this format with ALL sections:

## Task: {task_id} -- {module_name}

**What This Module Does**
2-3 sentences. What visual effect does it produce?

---

## Public Interface

```python
# Class extending EffectPlugin with process_frame method
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|

---

## What This Module Does NOT Do
- Scope boundaries

---

## Dependencies
- External and internal

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|

**Minimum coverage:** 80%

---

## Definition of Done
- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs
"""


def generate_spec(task_id, module_name, queries, spec_type="core"):
    """Generate a single spec."""
    output_file = os.path.join(OUTPUT_DIR, "%s_%s.md" % (task_id, module_name))

    if os.path.exists(output_file):
        print("  Skipping %s — already exists" % output_file)
        return True

    # Query Qdrant for legacy context
    print("  Querying Qdrant for: %s" % ", ".join(queries))
    results = qdrant_search(queries)
    legacy_context = format_legacy_context(results)
    print("  Found %d legacy references" % len(results))

    # Select template
    if spec_type == "core":
        prompt = CORE_PROMPT.format(
            task_id=task_id,
            module_name=module_name,
            legacy_context=legacy_context,
        )
    else:
        prompt = PLUGIN_PROMPT.format(
            task_id=task_id,
            module_name=module_name,
            legacy_context=legacy_context,
        )

    # Generate via rkllama
    print("  Generating spec via rkllama...")
    response = call_rkllama(prompt)

    if response:
        # Add header
        header = "# Spec: %s -- %s\n\n" % (task_id, module_name)
        header += "**Generated:** %s\n" % time.strftime("%%Y-%%m-%%d %%H:%%M")
        header += "**Model:** %s\n" % MODEL
        header += "**Legacy refs:** %d files from Qdrant\n" % len(results)
        header += "**Status:** FIRST PASS — needs Roo review\n\n---\n\n"

        with open(output_file, "w") as f:
            f.write(header + response)
        print("  Saved: %s" % output_file)
        return True
    else:
        print("  FAILED to generate spec for %s" % task_id)
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate specs from Qdrant + rkllama")
    parser.add_argument("--type", choices=["core", "plugin", "all"], default="core",
                        help="Type of specs to generate")
    parser.add_argument("--items", type=int, default=0, help="Max items (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without generating")
    args = parser.parse_args()

    items = []
    if args.type in ("core", "all"):
        items.extend([(t, m, q, "core") for t, m, q in CORE_ITEMS])
    if args.type in ("plugin", "all"):
        items.extend([(t, m, q, "plugin") for t, m, q in PLUGIN_ITEMS])

    if args.items > 0:
        items = items[:args.items]

    print("VJLive3 Spec Generator v3")
    print("=" * 50)
    print("Items: %d (%s)" % (len(items), args.type))
    print("Output: %s" % OUTPUT_DIR)
    print("Model: %s" % MODEL)
    print("")

    if args.dry_run:
        for task_id, module_name, queries, spec_type in items:
            print("  [%s] %s: %s — queries: %s" % (
                spec_type.upper(), task_id, module_name, ", ".join(queries[:3])
            ))
        print("\nDry run complete. Use without --dry-run to generate.")
        return

    # Check rkllama
    try:
        req = urllib.request.Request("%s/api/tags" % RKLLAMA_URL)
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        print("ERROR: rkllama not running at %s" % RKLLAMA_URL)
        print("Start it with: rkllama serve")
        sys.exit(1)

    # Check Qdrant
    try:
        req = urllib.request.Request("%s/collections/%s" % (QDRANT_URL, COLLECTION))
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            points = data.get("result", {}).get("points_count", 0)
            print("Qdrant: %d points indexed" % points)
    except Exception:
        print("ERROR: Qdrant not reachable at %s" % QDRANT_URL)
        sys.exit(1)

    # Generate specs
    success = 0
    failed = 0
    for i, (task_id, module_name, queries, spec_type) in enumerate(items, 1):
        print("\n[%d/%d] %s: %s (%s)" % (i, len(items), task_id, module_name, spec_type))
        if generate_spec(task_id, module_name, queries, spec_type):
            success += 1
        else:
            failed += 1
        # Brief pause between generations
        time.sleep(2)

    print("\n" + "=" * 50)
    print("Complete: %d success, %d failed" % (success, failed))
    print("Specs in: %s" % OUTPUT_DIR)


if __name__ == "__main__":
    main()
