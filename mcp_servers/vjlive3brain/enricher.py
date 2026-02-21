"""
vjlive3brain — Brain Enricher

Adds rich, agent-navigable content to the brain.db beyond raw file indexing:

1. PLUGIN MANIFESTS: Indexes every plugin.json / manifest.json from both
   legacy codebases — giving agents exact paths, descriptions, and effect lists.

2. PORTING MAP: Cross-references each legacy plugin/module with the exact
   BOARD.md Task ID it maps to, and the target location in VJLive3.

3. AGENT NAVIGATION GUIDES: Top-level concept entries that answer "where do
   I start?" for each major porting area — a curated entry point for agents.

4. FEATURE MATRIX: Indexes VJlive-2's FEATURE_MATRIX.md and any crosswalk
   documentation as authoritative synthesis decisions.

Usage:
    # Enrich brain with all metadata (fast, ~5s):
    python -m mcp_servers.vjlive3brain.enricher --enrich

Run after seeder to give agents maximum context.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

from mcp_servers.vjlive3brain.db import ConceptDB
from mcp_servers.vjlive3brain.schema import (
    ConceptEntry,
    DreamerVerdict,
    LogicPurity,
    RoleAssignment,
)

_logger = logging.getLogger("vjlive3.mcp.vjlive3brain.enricher")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_LEGACY_V1 = _REPO_ROOT.parent / "vjlive"
_LEGACY_V2 = _REPO_ROOT.parent / "VJlive-2"
_DB_PATH = os.environ.get(
    "VJLIVE3_BRAIN_DB",
    str(_REPO_ROOT / "mcp_servers" / "vjlive3brain" / "brain.db"),
)

# ─── BOARD.md Task ID → Port Target Map ──────────────────────────────────────
# Maps legacy plugin directories / module patterns to their VJLive3 task and
# target location. Agents use this to know WHERE to put ported code.
PORTING_MAP: list[dict[str, str]] = [
    # 1C — Node Graph
    {
        "task_id": "P1-N1",
        "description": "UnifiedMatrix + node registry (manifest-based)",
        "legacy_v1_path": "core/matrix/",
        "legacy_v2_path": "core/matrix/",
        "vjl3_target": "src/vjlive3/matrix/",
        "spec": "docs/specs/P1-N1_node_registry.md",
        "tags": ["matrix", "node-registry", "manifest"],
    },
    {
        "task_id": "P1-N2",
        "description": "Node types — full collection from both codebases",
        "legacy_v1_path": "core/nodes/",
        "legacy_v2_path": "core/matrix/matrix_nodes.py",
        "vjl3_target": "src/vjlive3/matrix/nodes/",
        "spec": "docs/specs/P1-N2_node_types.md",
        "tags": ["nodes", "effects", "generators"],
    },
    {
        "task_id": "P1-N3",
        "description": "State persistence (save/load)",
        "legacy_v1_path": "core/project/",
        "legacy_v2_path": "core/project_manager.py",
        "vjl3_target": "src/vjlive3/persistence/",
        "spec": "docs/specs/P1-N3_state_persistence.md",
        "tags": ["persistence", "save", "load", "project"],
    },
    {
        "task_id": "P1-N4",
        "description": "Visual node graph UI",
        "legacy_v1_path": "frontend/src/",
        "legacy_v2_path": "frontend/src/",
        "vjl3_target": "src/vjlive3/ui/node_graph/",
        "spec": "docs/specs/P1-N4_node_graph_ui.md",
        "tags": ["ui", "node-graph", "frontend"],
    },
    # 1A — Rendering
    {
        "task_id": "P1-R1",
        "description": "OpenGL rendering context (ModernGL)",
        "legacy_v1_path": "core/gl_utils.py",
        "legacy_v2_path": "core/rendering/",
        "vjl3_target": "src/vjlive3/rendering/context.py",
        "spec": "docs/specs/P1-R1_opengl_context.md",
        "tags": ["opengl", "moderngl", "rendering", "context"],
    },
    {
        "task_id": "P1-R2",
        "description": "GPU pipeline + framebuffer management (RAII)",
        "legacy_v1_path": "core/gl_utils.py",
        "legacy_v2_path": "core/framebuffer_manager.py",
        "vjl3_target": "src/vjlive3/rendering/framebuffer.py",
        "spec": "docs/specs/P1-R2_gpu_pipeline.md",
        "tags": ["framebuffer", "gpu", "pipeline", "raii", "opengl"],
    },
    {
        "task_id": "P1-R3",
        "description": "Shader compilation system (GLSL + Milkdrop)",
        "legacy_v1_path": "core/shader_utils.py",
        "legacy_v2_path": "core/unified_shader_manager.py",
        "vjl3_target": "src/vjlive3/rendering/shaders.py",
        "spec": "docs/specs/P1-R3_shader_compiler.md",
        "tags": ["shader", "glsl", "compilation", "milkdrop"],
    },
    {
        "task_id": "P1-R4",
        "description": "Texture manager (pooled, leak-free)",
        "legacy_v1_path": "core/texture_manager.py",
        "legacy_v2_path": "core/texture_pool.py",
        "vjl3_target": "src/vjlive3/rendering/textures.py",
        "spec": "docs/specs/P1-R4_texture_manager.md",
        "tags": ["texture", "pool", "memory", "opengl"],
    },
    {
        "task_id": "P1-R5",
        "description": "Core rendering engine (60fps loop)",
        "legacy_v1_path": "core/main_loop.py",
        "legacy_v2_path": "core/render_engine.py",
        "vjl3_target": "src/vjlive3/rendering/engine.py",
        "spec": "docs/specs/P1-R5_render_engine.md",
        "tags": ["render-loop", "60fps", "engine", "main-loop"],
    },
    # 1B — Audio
    {
        "task_id": "P1-A1",
        "description": "FFT + waveform analysis engine",
        "legacy_v1_path": "core/audio_processor.py",
        "legacy_v2_path": "core/audio/audio_analyzer.py",
        "vjl3_target": "src/vjlive3/audio/analyzer.py",
        "spec": "docs/specs/P1-A1_audio_analyzer.md",
        "tags": ["audio", "fft", "waveform", "analysis"],
    },
    {
        "task_id": "P1-A2",
        "description": "Real-time beat detection",
        "legacy_v1_path": "core/beat_detector.py",
        "legacy_v2_path": "core/audio/beat_detector.py",
        "vjl3_target": "src/vjlive3/audio/beat_detector.py",
        "spec": "docs/specs/P1-A2_beat_detector.md",
        "tags": ["audio", "beat", "bpm", "detection"],
    },
    {
        "task_id": "P1-A3",
        "description": "Audio-reactive effect framework",
        "legacy_v1_path": "core/audio_reactive/",
        "legacy_v2_path": "core/audio/reactivity_bus.py",
        "vjl3_target": "src/vjlive3/audio/reactivity.py",
        "spec": "docs/specs/P1-A3_reactivity_bus.md",
        "tags": ["audio", "reactive", "bus", "effects"],
    },
    {
        "task_id": "P1-A4",
        "description": "Multi-source audio input",
        "legacy_v1_path": "core/audio_source.py",
        "legacy_v2_path": "core/audio/audio_sources.py",
        "vjl3_target": "src/vjlive3/audio/sources.py",
        "spec": "docs/specs/P1-A4_audio_sources.md",
        "tags": ["audio", "input", "sources", "multi-source"],
    },
    # 2A — DMX
    {
        "task_id": "P2-D1",
        "description": "DMX512 core engine + fixture profiles",
        "legacy_v1_path": "core/dmx/",
        "legacy_v2_path": "N/A (missing from VJlive-2)",
        "vjl3_target": "src/vjlive3/dmx/engine.py",
        "spec": "docs/specs/P2-D1_dmx_engine.md (TO BE WRITTEN)",
        "tags": ["dmx", "dmx512", "fixtures", "lighting"],
    },
    {
        "task_id": "P2-D2",
        "description": "ArtNet + sACN output",
        "legacy_v1_path": "core/dmx/artnet_output.py",
        "legacy_v2_path": "N/A (missing from VJlive-2)",
        "vjl3_target": "src/vjlive3/dmx/artnet.py",
        "spec": "docs/specs/P2-D2_artnet_output.md (TO BE WRITTEN)",
        "tags": ["dmx", "artnet", "sacn", "network"],
    },
    # 2B — Hardware
    {
        "task_id": "P2-H1",
        "description": "MIDI controller input",
        "legacy_v1_path": "core/midi/",
        "legacy_v2_path": "core/input/midi_controller.py",
        "vjl3_target": "src/vjlive3/input/midi.py",
        "spec": "docs/specs/P2-H1_midi_controller.md (TO BE WRITTEN)",
        "tags": ["midi", "input", "controller", "hardware"],
    },
    {
        "task_id": "P2-H3",
        "description": "Astra depth camera integration",
        "legacy_v1_path": "astracam/",
        "legacy_v2_path": "core/camera/",
        "vjl3_target": "src/vjlive3/hardware/astra.py",
        "spec": "docs/specs/P2-H3_astra.md (TO BE WRITTEN)",
        "tags": ["astra", "depth-camera", "orbbec", "hardware"],
    },
    # 2C — Distributed
    {
        "task_id": "P2-X1",
        "description": "Multi-node coordination (ZeroMQ)",
        "legacy_v1_path": "core/network/zmq_coordinator.py",
        "legacy_v2_path": "N/A",
        "vjl3_target": "src/vjlive3/network/coordinator.py",
        "spec": "docs/specs/P2-X1_zmq_coordinator.md (TO BE WRITTEN)",
        "tags": ["zmq", "zeromq", "distributed", "multi-node"],
    },
    # Plugins — V-* collection
    {
        "task_id": "P5-V01",
        "description": "V-Shadertoy Extra — Shadertoy effect bridge",
        "legacy_v1_path": "plugins/vshadertoy_extra/",
        "legacy_v2_path": "plugins/vshadertoy_extra/",
        "vjl3_target": "src/vjlive3/plugins/effects/vshadertoy_extra/",
        "spec": "BOARD.md P5-V01",
        "tags": ["plugin", "shadertoy", "glsl", "effect"],
    },
    {
        "task_id": "P5-V02",
        "description": "Silver Visions visual effect",
        "legacy_v1_path": "plugins/vvimana/",
        "legacy_v2_path": "plugins/vvimana/",
        "vjl3_target": "src/vjlive3/plugins/effects/silver_visions/",
        "spec": "BOARD.md P5-V02",
        "tags": ["plugin", "vimana", "effect", "visual"],
    },
    {
        "task_id": "P5-V13",
        "description": "V-Vimana — primary visual synthesis plugin",
        "legacy_v1_path": "plugins/vvimana/",
        "legacy_v2_path": "plugins/vvimana/",
        "vjl3_target": "src/vjlive3/plugins/effects/vvimana/",
        "spec": "BOARD.md P5-V13",
        "tags": ["plugin", "vimana", "effect", "synthesis"],
    },
    {
        "task_id": "P5-V14",
        "description": "V-Voxglitch — glitch effects collection",
        "legacy_v1_path": "plugins/vvoxglitch/",
        "legacy_v2_path": "plugins/vvoxglitch/",
        "vjl3_target": "src/vjlive3/plugins/effects/vvoxglitch/",
        "spec": "BOARD.md P5-V14",
        "tags": ["plugin", "voxglitch", "glitch", "effect"],
    },
    # Datamosh family
    {
        "task_id": "P5-D",
        "description": "Datamosh family — all datamosh effects from both codebases",
        "legacy_v1_path": "plugins/vdatamosh/",
        "legacy_v2_path": "plugins/core/ (datamosh_ prefixed dirs)",
        "vjl3_target": "src/vjlive3/plugins/effects/datamosh/",
        "spec": "BOARD.md Phase 5D",
        "tags": ["plugin", "datamosh", "glitch", "mosh", "effect"],
    },
    # Depth plugins
    {
        "task_id": "P3-VD",
        "description": "Depth plugin collection — all vdepth effects",
        "legacy_v1_path": "plugins/vdepth/",
        "legacy_v2_path": "plugins/vdepth/",
        "vjl3_target": "src/vjlive3/plugins/effects/depth/",
        "spec": "BOARD.md Phase 3A",
        "tags": ["plugin", "depth", "astra", "3d", "effect"],
    },
    # Audio plugins
    {
        "task_id": "P4-BA",
        "description": "Bogaudio collection — all vbogaudio audio-reactive modules",
        "legacy_v1_path": "plugins/vbogaudio/",
        "legacy_v2_path": "plugins/vbogaudio/ + plugins/core/vbogaudio_*/",
        "vjl3_target": "src/vjlive3/plugins/effects/bogaudio/",
        "spec": "BOARD.md Phase 4A",
        "tags": ["plugin", "bogaudio", "audio-reactive", "modulator"],
    },
    {
        "task_id": "P4-BF",
        "description": "Befaco collection — vbefaco modulators",
        "legacy_v1_path": "plugins/vbefaco/",
        "legacy_v2_path": "plugins/vbefaco/",
        "vjl3_target": "src/vjlive3/plugins/effects/befaco/",
        "spec": "BOARD.md Phase 4B",
        "tags": ["plugin", "befaco", "modulator", "audio"],
    },
    # Business / Licensing
    {
        "task_id": "P7-B",
        "description": "License server + burst credit system",
        "legacy_v1_path": "core/license/ + WORKER_33_BURST_CREDIT_LICENSING.md",
        "legacy_v2_path": "core/license_server/ + core/burst_credit/",
        "vjl3_target": "src/vjlive3/licensing/",
        "spec": "BOARD.md Phase 7B",
        "tags": ["license", "business", "jwt", "rbac", "burst-credit"],
    },
    # AI systems
    {
        "task_id": "P6-AI1",
        "description": "Neural Style Transfer (ML effects)",
        "legacy_v1_path": "plugins/vml/",
        "legacy_v2_path": "core/extensions/neural/",
        "vjl3_target": "src/vjlive3/ai/neural_style.py",
        "spec": "BOARD.md P6-AI1",
        "tags": ["ai", "neural", "style-transfer", "ml"],
    },
    {
        "task_id": "P6-Q",
        "description": "Quantum Consciousness system",
        "legacy_v1_path": "core/extensions/quantum/",
        "legacy_v2_path": "core/extensions/quantum/",
        "vjl3_target": "src/vjlive3/quantum/",
        "spec": "BOARD.md Phase 6B — DREAMER territory",
        "tags": ["quantum", "consciousness", "dreamer", "experimental"],
    },
]

# ─── Agent Navigation Guides ─────────────────────────────────────────────────
# These are top-level "start here" entries for agents beginning a new area.
NAV_GUIDES: list[dict[str, str]] = [
    {
        "concept_id": "nav--rendering-pipeline",
        "name": "NAVIGATION: Rendering Pipeline Porting Guide",
        "category": "governance",
        "description": (
            "START HERE for rendering work. "
            "PRIMARY source: VJlive-2/core/rendering/ and VJlive-2/core/gl_utils.py. "
            "SUPPLEMENTARY: vjlive/core/gl_utils.py, vjlive/core/shader_utils.py. "
            "Tasks: P1-R1 (context), P1-R2 (framebuffer), P1-R3 (shaders), "
            "P1-R4 (textures), P1-R5 (engine). "
            "Target: src/vjlive3/rendering/. "
            "CRITICAL: ModernGL not PyOpenGL. RAII semantics. 60fps mandatory."
        ),
        "tags": ["navigation", "rendering", "opengl", "moderngl", "gpu"],
    },
    {
        "concept_id": "nav--audio-engine",
        "name": "NAVIGATION: Audio Engine Porting Guide",
        "category": "governance",
        "description": (
            "START HERE for audio work. "
            "PRIMARY source: VJlive-2/core/audio/ (audio_analyzer.py, beat_detector.py, "
            "audio_sources.py, reactivity_bus.py). "
            "SUPPLEMENTARY: vjlive/core/audio_processor.py, vjlive/core/beat_detector.py. "
            "Tasks: P1-A1 (FFT), P1-A2 (beat), P1-A3 (reactivity bus), P1-A4 (multi-source). "
            "Target: src/vjlive3/audio/. "
            "Read spec BEFORE coding. Sounddevice + librosa in v2. numpy FFT in v1."
        ),
        "tags": ["navigation", "audio", "fft", "beat", "reactivity"],
    },
    {
        "concept_id": "nav--plugin-system",
        "name": "NAVIGATION: Plugin System — What's Done and What's Next",
        "category": "governance",
        "description": (
            "Plugin system (P1-P1 through P1-P5) is COMPLETE at 81%+ coverage. "
            "DO NOT re-implement registry, loader, hot_reload, or sandbox. "
            "Next: port the actual plugins. "
            "Read /path/to/docs/specs/ for each plugin area. "
            "Plugin directories: vjlive/plugins/* (v1 source) and VJlive-2/plugins/core/* (v2 source). "
            "Every plugin is a BESPOKE SNOWFLAKE — no batch processing."
        ),
        "tags": ["navigation", "plugin", "done", "next-steps"],
    },
    {
        "concept_id": "nav--node-graph",
        "name": "NAVIGATION: Node Graph / UnifiedMatrix Porting Guide",
        "category": "governance",
        "description": (
            "START HERE for node graph work. "
            "PRIMARY source: VJlive-2/core/matrix/ (unified_matrix.py, matrix_nodes.py). "
            "SUPPLEMENTARY: vjlive/core/matrix/ — same concept, different architecture. "
            "Tasks: P1-N1 (node registry), P1-N2 (node types), "
            "P1-N3 (state persistence), P1-N4 (node graph UI). "
            "Target: src/vjlive3/matrix/. "
            "The UnifiedMatrix is the spine of the app — all signals flow through it."
        ),
        "tags": ["navigation", "matrix", "node-graph", "nodes"],
    },
    {
        "concept_id": "nav--dmx-system",
        "name": "NAVIGATION: DMX System — v1 Only (CRITICAL MISSING from v2)",
        "category": "governance",
        "description": (
            "START HERE for DMX work. WARNING: VJlive-2 does NOT have DMX. "
            "PRIMARY (and ONLY) source: vjlive/core/dmx/ — read every file. "
            "Also read: vjlive/WORKER_25_HARDWARE_INTEGRATION.md for full context. "
            "Tasks: P2-D1 (core engine), P2-D2 (ArtNet/sACN), P2-D3 (FX engine), "
            "P2-D4 (show control), P2-D5 (audio-reactive DMX). "
            "Spec must be written BEFORE any code. See docs/specs/P2-D1_dmx_engine.md."
        ),
        "tags": ["navigation", "dmx", "artnet", "sacn", "lighting", "missing-from-v2"],
    },
    {
        "concept_id": "nav--depth-plugins",
        "name": "NAVIGATION: Depth Plugin Collection Porting Guide",
        "category": "governance",
        "description": (
            "START HERE for depth plugin porting. "
            "PRIMARY source: vjlive/plugins/vdepth/ — large collection, every plugin unique. "
            "SECONDARY source: VJlive-2/plugins/vdepth/ — some overlap, verify quality. "
            "Phase 3A: P3-VD01 through P3-VD09+. "
            "RULE: Read each plugin's __init__.py AND manifest.json individually. "
            "RULE: No batch processing — bespoke snowflake treatment for EVERY plugin. "
            "Target: src/vjlive3/plugins/effects/depth/"
        ),
        "tags": ["navigation", "depth", "astra", "plugins", "phase-3"],
    },
    {
        "concept_id": "nav--datamosh-family",
        "name": "NAVIGATION: Datamosh Family — Both Codebases",
        "category": "governance",
        "description": (
            "START HERE for datamosh porting. "
            "V1 source: vjlive/plugins/vdatamosh/ — contains all datamosh variant __init__.py files. "
            "V2 source: VJlive-2/plugins/core/ — look for *_datamosh dirs "
            "(bass_cannon_datamosh, spirit_aura_datamosh, volumetric_datamosh, etc.). "
            "V2 implementation is CLEANER — prefer v2 when it exists, port unique v1 variants. "
            "Full list in BOARD.md Phase 5D. "
            "Target: src/vjlive3/plugins/effects/datamosh/"
        ),
        "tags": ["navigation", "datamosh", "glitch", "plugins", "phase-5"],
    },
    {
        "concept_id": "nav--audio-plugins",
        "name": "NAVIGATION: Audio Plugin Collections (Bogaudio + Befaco)",
        "category": "governance",
        "description": (
            "START HERE for audio-reactive plugin porting. "
            "BOGAUDIO (P4-BA): vjlive/plugins/vbogaudio/ (v1) and VJlive-2/plugins/core/vbogaudio_*/ (v2). "
            "10 plugins: B1to8, BLFO, BMatrix81, BPEQ6, BSwitch, BVCF, BVCO, BVELO, NMix4, NXFade. "
            "BEFACO (P4-BF): vjlive/plugins/vbefaco/ and VJlive-2/plugins/vbefaco/. "
            "6 plugins: V-Even, V-Morphader, V-Outs, V-Pony, V-Scope, V-Voltio. "
            "Target: src/vjlive3/plugins/effects/bogaudio/ and .../befaco/"
        ),
        "tags": ["navigation", "bogaudio", "befaco", "audio-reactive", "plugins", "phase-4"],
    },
    {
        "concept_id": "nav--feature-matrix",
        "name": "NAVIGATION: Feature Synthesis Decisions — Read This First",
        "category": "governance",
        "description": (
            "AUTHORITATIVE synthesis decisions are in VJlive-2/FEATURE_MATRIX.md. "
            "This file documents which codebase leads for each feature area. "
            "RULE: VJlive-2's clean architecture is the BASE for ALL features. "
            "RULE: vjlive's unique features are ported WITH VJlive-2's quality standards applied. "
            "Read before making any architectural decisions. "
            "Also see BOARD.md for the full task list and WORKSPACE/COMMS/DECISIONS.md for ADRs."
        ),
        "tags": ["navigation", "feature-matrix", "synthesis", "architecture", "decisions"],
    },
    {
        "concept_id": "nav--how-to-work",
        "name": "NAVIGATION: How To Work — Agent Process Rules",
        "category": "governance",
        "description": (
            "READ THIS before starting any task: WORKSPACE/HOW_TO_WORK.md. "
            "Process: (1) Check COMMS/DISPATCH.md for active tasks. "
            "(2) Read COMMS/LOCKS.md before editing files. "
            "(3) SPEC must exist before code — see docs/specs/. "
            "(4) Consult this brain (vjlive3brain) via search_concepts() BEFORE writing. "
            "(5) Log architectural decisions in COMMS/DECISIONS.md. "
            "(6) Run tests. 80% coverage required. "
            "Safety rails: WORKSPACE/SAFETY_RAILS.md and SAFETY_RAILS.md (root)."
        ),
        "tags": ["navigation", "process", "workflow", "how-to-work", "rules"],
    },
    {
        "concept_id": "nav--business-model",
        "name": "NAVIGATION: Business Model — Licensing, Marketplace, Portal",
        "category": "business",
        "description": (
            "Business layer tasks are in BOARD.md Phase 7B. "
            "PRIMARY source for licensing: VJlive-2/core/license_server/ and "
            "VJlive-2/core/burst_credit/. "
            "SUPPLEMENTARY: vjlive/WORKER_33_BURST_CREDIT_LICENSING.md (full spec). "
            "vjlive/core/license/ has original implementation. "
            "Tasks: P7-B1 (license server JWT+RBAC), P7-B2 (plugin marketplace), "
            "P7-B3 (developer portal), P7-B4 (burst credits). "
            "Target: src/vjlive3/licensing/"
        ),
        "tags": ["navigation", "license", "marketplace", "jwt", "business", "phase-7"],
    },
    {
        "concept_id": "nav--quantum-dreamer",
        "name": "NAVIGATION: Quantum / Dreamer Systems — Handle With Care",
        "category": "governance",
        "description": (
            "DREAMER territory — these are experimental systems. "
            "Primary source: VJlive-2/core/extensions/quantum/ and "
            "VJlive-2/core/extensions/consciousness/. "
            "vjlive also has quantum tunnel effects in plugins/. "
            "Phase 6B tasks: P6-Q1 (Quantum Nexus), P6-Q2 (Quantum Explorer), "
            "P6-Q3 (Quantum Tunnel), P6-Q4 (Living Fractal Consciousness). "
            "DO NOT sandbox or break their 'soul' — port with DREAMER_VERDICT in mind. "
            "Flag all [DREAMER_LOGIC] found. See WORKSPACE/KNOWLEDGE/DREAMER_LOG.md."
        ),
        "tags": ["navigation", "quantum", "dreamer", "consciousness", "experimental", "phase-6"],
    },
    {
        "concept_id": "nav--agent-system",
        "name": "NAVIGATION: Agent Physics / 16D Manifold System",
        "category": "governance",
        "description": (
            "Agent system tasks in BOARD.md Phase 6C. "
            "This is vjlive-ONLY — VJlive-2 does NOT have this. "
            "Primary source: vjlive/plugins/vagent/ and vjlive/core/agent*. "
            "16D manifold + gravity wells is DREAMER territory — preserve the soul. "
            "Tasks: P6-AG1 (Agent Bridge), P6-AG2 (16D Manifold), "
            "P6-AG3 (50-snapshot memory), P6-AG4 (Agent Control UI). "
            "This is Phase 6 — do not start until Phase 2 hardware is done."
        ),
        "tags": ["navigation", "agent", "16d", "manifold", "physics", "dreamer", "phase-6"],
    },
]


def _make_porting_entry(item: dict[str, str]) -> ConceptEntry:
    """Create a ConceptEntry from a porting map item."""
    task_id = item["task_id"]
    concept_id = f"porting-map--{task_id.lower().replace(' ', '-')}"
    desc = (
        f"{item['description']}. "
        f"V1 source: {item['legacy_v1_path']}. "
        f"V2 source: {item['legacy_v2_path']}. "
        f"VJLive3 target: {item['vjl3_target']}. "
        f"Spec: {item['spec']}."
    )
    tags = list(item.get("tags", [])) + ["porting-map", task_id.lower()]
    return ConceptEntry(
        concept_id=concept_id,
        name=f"PORTING MAP: {task_id} — {item['description'][:60]}",
        description=desc[:500],
        origin_ref="vjlive3-porting-map",
        source_files=[],
        dreamer_flag=False,
        dreamer_analysis="",
        dreamer_verdict=DreamerVerdict.PENDING,
        logic_purity=LogicPurity.UNKNOWN,
        role_assignment=RoleAssignment.MANAGER,
        kitten_status=False,
        tags=tags,
        category="governance",
        performance_impact="low",
        ported_to="",
    )


def _make_nav_entry(item: dict[str, str]) -> ConceptEntry:
    """Create a ConceptEntry from a nav guide item."""
    tags = list(item.get("tags", [])) + ["navigation-guide"]
    return ConceptEntry(
        concept_id=item["concept_id"],
        name=item["name"],
        description=item["description"][:500],
        origin_ref="vjlive3-nav-guide",
        source_files=[],
        dreamer_flag=False,
        dreamer_analysis="",
        dreamer_verdict=DreamerVerdict.PENDING,
        logic_purity=LogicPurity.CLEAN,
        role_assignment=RoleAssignment.MANAGER,
        kitten_status=False,
        tags=tags,
        category=item.get("category", "governance"),
        performance_impact="low",
        ported_to="",
    )


def seed_plugin_manifests(db: ConceptDB) -> int:
    """
    Index every plugin.json / manifest.json from both legacy codebases.
    Creates rich concept entries with plugin names, descriptions, effects.
    """
    count = 0
    manifest_names = {"manifest.json", "plugin.json"}
    skip_dirs = {".git", ".venv", "venv", "test_env", "node_modules", "moved",
                 "JUNK", "__pycache__", "lib", "site-packages"}

    for root, origin in [(_LEGACY_V1, "vjlive-v1"), (_LEGACY_V2, "vjlive-v2")]:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for fname in filenames:
                if fname not in manifest_names:
                    continue
                fpath = Path(dirpath) / fname
                try:
                    data: dict[str, Any] = json.loads(
                        fpath.read_text(encoding="utf-8", errors="replace")
                    )
                except (OSError, json.JSONDecodeError):
                    continue

                plugin_name = (
                    data.get("name") or data.get("plugin_name") or fpath.parent.name
                )
                plugin_desc = (
                    data.get("description") or data.get("summary") or ""
                )
                effects = data.get("effects", data.get("modules", []))
                if effects and isinstance(effects, list):
                    effect_names = [
                        e.get("name", str(e)) if isinstance(e, dict) else str(e)
                        for e in effects[:10]
                    ]
                    plugin_desc += f" Effects: {', '.join(effect_names)}."

                category = data.get("category", "plugin")
                tags = [origin, "manifest", "plugin"] + (
                    list(data.get("tags", []))[:5] if data.get("tags") else []
                )

                rel = fpath.parent.relative_to(root)
                concept_id = f"{origin}--manifest--{str(rel).replace(os.sep, '-').replace(' ', '_')}"[:120]

                entry = ConceptEntry(
                    concept_id=concept_id,
                    name=f"[MANIFEST] {plugin_name} ({origin})",
                    description=(plugin_desc or f"Plugin manifest: {plugin_name}")[:500],
                    origin_ref=origin,
                    source_files=[str(fpath)],
                    dreamer_flag=False,
                    dreamer_analysis="",
                    dreamer_verdict=DreamerVerdict.PENDING,
                    logic_purity=LogicPurity.UNKNOWN,
                    role_assignment=RoleAssignment.WORKER,
                    kitten_status=False,
                    tags=tags,
                    category=category,
                    performance_impact="low",
                    ported_to="",
                )
                db.upsert(entry)
                count += 1

    _logger.info("Seeded %d plugin manifests", count)
    return count


def run_enrichment(db: ConceptDB) -> None:
    """Full enrichment: porting map + nav guides + plugin manifests."""
    total = 0

    # 1. Porting map entries
    for item in PORTING_MAP:
        db.upsert(_make_porting_entry(item))
        total += 1
    _logger.info("Seeded %d porting map entries", len(PORTING_MAP))

    # 2. Agent navigation guides
    for item in NAV_GUIDES:
        db.upsert(_make_nav_entry(item))
        total += 1
    _logger.info("Seeded %d agent navigation guides", len(NAV_GUIDES))

    # 3. Plugin manifests
    manifest_count = seed_plugin_manifests(db)
    total += manifest_count

    stats = db.stats()
    _logger.info(
        "Enrichment complete. +%d entries. Total DB: %d concepts (%d dreamer)",
        total, stats["total"], stats["dreamer"],
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="vjlive3brain enricher")
    parser.add_argument("--enrich", action="store_true", help="Run full enrichment")
    parser.add_argument("--db", default=_DB_PATH, help="Override DB path")
    args = parser.parse_args()

    db = ConceptDB(args.db)
    db.initialize()

    if args.enrich:
        run_enrichment(db)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
