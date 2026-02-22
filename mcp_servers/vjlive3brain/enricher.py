# enricher.py
"""
Enrichment rules for the VJLive Brain knowledge base.

This module defines PORTING_MAP and NAV_GUIDES which provide
structured guidance for agents porting legacy code to the new
plugin-based architecture.

CURRENT STATE:
- Only src/vjlive3/plugins/ exists
- All other modules (rendering, audio, node_graph, hardware, etc.) have been deleted
- Plugin system (P1-P1 through P1-P5) is complete with 81%+ test coverage
- Specs exist for all deleted modules in docs/specs/
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from mcp_servers.vjlive3brain.schema import ConceptEntry, ConceptDB

# ---------------------------------------------------------------------------
# PORTING MAP: Legacy module -> Target plugin infrastructure
# ---------------------------------------------------------------------------
#
# Each entry maps a deleted legacy module to the plugin infrastructure
# that should be used when porting functionality. The "task" field
# indicates which plugin system component to focus on.
#
# Current state: only plugins/ exists, so all porting targets are
# within the plugin system.

PORTING_MAP: list[dict[str, str]] = [
    # Legacy rendering module -> plugin effects system
    {
        "module": "rendering",
        "target": "src/vjlive3/plugins/effects/",
        "task": "Implement effect plugins (P1-P2/P1-P3)",
        "reason": "Rendering pipeline replaced by effect plugins",
    },
    # Legacy audio module -> plugin audio effects
    {
        "module": "audio",
        "target": "src/vjlive3/plugins/effects/",
        "task": "Implement audio effect plugins (P1-A1/P1-A2)",
        "reason": "Audio analysis moved to effect plugins",
    },
    # Legacy node_graph module -> plugin registry + loader
    {
        "module": "node_graph",
        "target": "src/vjlive3/plugins/",
        "task": "Use plugin registry and loader (P1-P1/P1-P2)",
        "reason": "Node graph functionality distributed across plugin system",
    },
    # Legacy hardware module -> plugin sandbox
    {
        "module": "hardware",
        "target": "src/vjlive3/plugins/sandbox.py",
        "task": "Implement hardware access via sandbox (P1-P5)",
        "reason": "Hardware access controlled through plugin sandbox",
    },
    # Legacy dmx module -> plugin effects
    {
        "module": "dmx",
        "target": "src/vjlive3/plugins/effects/",
        "task": "Implement DMX effect plugins",
        "reason": "DMX control as effect plugin",
    },
    # Legacy depth module -> plugin effects
    {
        "module": "depth",
        "target": "src/vjlive3/plugins/effects/",
        "task": "Implement depth effect plugins",
        "reason": "Depth processing as effect plugin",
    },
    # Legacy datamosh module -> plugin effects
    {
        "module": "datamosh",
        "target": "src/vjlive3/plugins/effects/",
        "task": "Implement datamosh effect plugins",
        "reason": "Datamosh as effect plugin",
    },
    # Legacy audio_plugins -> plugin effects (audio-specific)
    {
        "module": "audio_plugins",
        "target": "src/vjlive3/plugins/effects/",
        "task": "Implement audio effect plugins (P1-A* specs)",
        "reason": "Audio plugins merged into effect plugin system",
    },
    # Legacy core.sigil -> plugin registry
    {
        "module": "core.sigil",
        "target": "src/vjlive3/plugins/registry.py",
        "task": "Use plugin registry for sigil management",
        "reason": "Sigil management moved to plugin registry",
    },
    # Legacy network.coordinator -> plugin loader
    {
        "module": "network.coordinator",
        "target": "src/vjlive3/plugins/loader.py",
        "task": "Use plugin loader for coordination",
        "reason": "Network coordination via plugin loader",
    },
    # Legacy osc.* -> plugin sandbox
    {
        "module": "osc",
        "target": "src/vjlive3/plugins/sandbox.py",
        "task": "Implement OSC via sandbox (P1-P5)",
        "reason": "OSC access through sandboxed plugins",
    },
    # Legacy sync.* -> plugin effects
    {
        "module": "sync",
        "target": "src/vjlive3/plugins/effects/",
        "task": "Implement sync effect plugins",
        "reason": "Timecode sync as effect plugin",
    },
]

# ---------------------------------------------------------------------------
# NAVIGATION GUIDES: Quick-start paths for common tasks
# ---------------------------------------------------------------------------
#
# These guides provide direct navigation to relevant code/docs for
# specific tasks. They reflect the current state where only the plugin
# system exists; all other modules must be rebuilt.

NAV_GUIDES: list[dict[str, str]] = [
    {
        "id": "plugin-system",
        "title": "Plugin System Architecture",
        "url": "src/vjlive3/plugins/",
        "category": "core",
        "description": "Complete plugin infrastructure: registry, loader, hot-reload, sandbox, validator, and GPU detection. All P1-P* specs implemented with 81%+ test coverage. This is the ONLY existing module in src/vjlive3/.",
        "priority": "1",
        "tags": "plugins,architecture,core",
    },
    {
        "id": "plugin-effects",
        "title": "Plugin Effects System",
        "url": "src/vjlive3/plugins/effects/",
        "category": "plugins",
        "description": "Effect plugin implementations. Currently empty - ready for new effect plugins following the P1-P2 and P1-P3 specifications. This is where all visual/audio effects will live.",
        "priority": "2",
        "tags": "plugins,effects,audio,visual",
    },
    {
        "id": "plugin-manifests",
        "title": "Plugin Manifest Format",
        "url": "docs/specs/plugin_manifest_examples.md",
        "category": "plugins",
        "description": "Complete guide to plugin manifest structure, metadata fields, and examples. Required for all plugin packages. See also: P1-P1_package_skeleton.md, P1-P2_plugin_loader.md, P1-P3_plugin_hot_reload.md, P1-P4_plugin_scanner.md, P1-P5_plugin_sandbox.md.",
        "priority": "3",
        "tags": "plugins,manifest,spec",
    },
    {
        "id": "rebuild-rendering",
        "title": "Rebuild: Rendering Pipeline (FUTURE WORK)",
        "url": "docs/specs/P1-R1_opengl_context.md,P1-R2_gpu_pipeline.md,P1-R3_shader_compiler.md,P1-R4_texture_manager.md,P1-R5_render_engine.md",
        "category": "future",
        "description": "FUTURE WORK: Rendering module (P1-R1 through P1-R5) needs to be rebuilt from specs. Current state: deleted, specs exist. Start with P1-R1 for OpenGL context management.",
        "priority": "4",
        "tags": "rendering,rebuild,future",
    },
    {
        "id": "rebuild-audio",
        "title": "Rebuild: Audio Engine (FUTURE WORK)",
        "url": "docs/specs/P1-A1_audio_analyzer.md,P1-A2_beat_detector.md,P1-A3_reactivity_bus.md,P1-A4_audio_sources.md",
        "category": "future",
        "description": "FUTURE WORK: Audio module (P1-A1 through P1-A4) needs to be rebuilt from specs. Current state: deleted, specs exist. Start with P1-A1 for audio analysis.",
        "priority": "5",
        "tags": "audio,rebuild,future",
    },
    {
        "id": "rebuild-node-graph",
        "title": "Rebuild: Node Graph System (FUTURE WORK)",
        "url": "docs/specs/P1-N1_node_registry.md,P1-N2_node_types.md,P1-N3_state_persistence.md,P1-N4_node_graph_ui.md",
        "category": "future",
        "description": "FUTURE WORK: Node graph module (P1-N1 through P1-N4) needs to be rebuilt from specs. Current state: deleted, specs exist. Start with P1-N1 for node registry.",
        "priority": "6",
        "tags": "node-graph,rebuild,future",
    },
    {
        "id": "plugin-development",
        "title": "How to Develop Plugins",
        "url": "docs/implementation_plan.md,ARCHITECTURE.md",
        "category": "guides",
        "description": "Guide for developing new plugins. Covers plugin manifest format, effect implementation, sandboxing, and testing. All development should target src/vjlive3/plugins/.",
        "priority": "7",
        "tags": "plugins,development,guide",
    },
    {
        "id": "spec-first-workflow",
        "title": "Spec-First Development Workflow",
        "url": "docs/specs/_TEMPLATE.md,DEFINITION_OF_DONE.md",
        "category": "process",
        "description": "How to work with specs in this project. All new work must start with a spec in docs/specs/ and follow the spec-first workflow. See verify_spec_exists.py for enforcement.",
        "priority": "8",
        "tags": "process,specs,workflow",
    },
]

# ---------------------------------------------------------------------------
# Enrichment functions
# ---------------------------------------------------------------------------


def _make_porting_entry(item: dict[str, str]) -> ConceptEntry:
    """Convert a PORTING_MAP item into a ConceptEntry."""
    return ConceptEntry(
        concept_id=f"porting:{item['module']}",
        title=f"Porting Guide: {item['module']}",
        description=f"{item['reason']} Target: {item['target']} Task: {item['task']}",
        tags=f"porting,{item['module']}",
        category="porting",
        source_files=[],
        dreamer_flag=False,
        dreamer_analysis="",
        dreamer_verdict="NEUTRAL",
        logic_purity="CLEAN",
        kitten_status=True,
        performance_impact="NONE",
        ported_to=item["target"],
        ported_date=None,
    )


def _make_nav_entry(item: dict[str, str]) -> ConceptEntry:
    """Convert a NAV_GUIDES item into a ConceptEntry."""
    return ConceptEntry(
        concept_id=f"nav:{item['id']}",
        title=item["title"],
        description=item["description"],
        tags=item["tags"],
        category=item["category"],
        source_files=[item["url"]],
        dreamer_flag=False,
        dreamer_analysis="",
        dreamer_verdict="NEUTRAL",
        logic_purity="CLEAN",
        kitten_status=True,
        performance_impact="NONE",
        ported_to="",
        ported_date=None,
    )


def seed_plugin_manifests(db: ConceptDB) -> int:
    """Seed entries for all plugin manifest files found in docs/specs/."""
    count = 0
    manifest_dir = Path("docs/specs")
    if not manifest_dir.exists():
        return 0

    manifest_names = set()
    for fpath in manifest_dir.glob("*_plugin_*.md"):
        manifest_names.add(fpath.name)
        content = fpath.read_text(encoding="utf-8", errors="ignore")

        # Extract title from first heading
        m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = m.group(1).strip() if m else fpath.stem.replace("_", " ").title()

        entry = ConceptEntry(
            concept_id=f"spec:{fpath.stem}",
            title=title,
            description=f"Plugin manifest specification: {title}",
            tags="spec,plugin,manifest",
            category="specs",
            source_files=[f"docs/specs/{fpath.name}"],
            dreamer_flag=False,
            dreamer_analysis="",
            dreamer_verdict="NEUTRAL",
            logic_purity="CLEAN",
            kitten_status=True,
            performance_impact="NONE",
            ported_to="",
            ported_date=None,
        )
        db[entry.concept_id] = entry
        count += 1

    # Also seed the plugin manifest examples file
    examples_path = manifest_dir / "plugin_manifest_examples.md"
    if examples_path.exists():
        manifest_names.add(examples_path.name)
        entry = ConceptEntry(
            concept_id="spec:plugin_manifest_examples",
            title="Plugin Manifest Examples",
            description="Complete examples of plugin manifest files for different plugin types",
            tags="spec,plugin,manifest,examples",
            category="specs",
            source_files=["docs/specs/plugin_manifest_examples.md"],
            dreamer_flag=False,
            dreamer_analysis="",
            dreamer_verdict="NEUTRAL",
            logic_purity="CLEAN",
            kitten_status=True,
            performance_impact="NONE",
            ported_to="",
            ported_date=None,
        )
        db[entry.concept_id] = entry
        count += 1

    return count


def run_enrichment(db: ConceptDB) -> None:
    """Apply enrichment rules to the knowledge base."""
    # Add porting map entries
    for item in PORTING_MAP:
        entry = _make_porting_entry(item)
        db[entry.concept_id] = entry

    # Add navigation guide entries
    for item in NAV_GUIDES:
        entry = _make_nav_entry(item)
        db[entry.concept_id] = entry

    # Seed plugin manifests from docs/specs/
    seed_plugin_manifests(db)


def main() -> None:
    """CLI entrypoint for running enrichment (for debugging)."""
    import sys
    from mcp_servers.vjlive3brain.db import open_db

    if len(sys.argv) > 1 and sys.argv[1] == "--seed-only":
        # Just seed plugin manifests
        db = open_db()
        count = seed_plugin_manifests(db)
        print(f"Seeded {count} plugin manifest entries")
        return

    print("Running full enrichment...")
    db = open_db()
    run_enrichment(db)
    print(f"Enriched database with {len(db)} concepts")
