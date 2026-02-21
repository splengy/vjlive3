# Spec: P1-P4 — Plugin Discovery (Auto-Scan)

**Phase:** Phase 1 / P1-P4
**Assigned To:** Antigravity (Agent 2)
**Authorized By:** Roo Code via DISPATCH.md — SPEC-P1-P4
**Depends On:** P1-P1 (registry), P1-P2 (loader)
**Date:** 2026-02-21

---

## What This Module Does

Walks the VJLive3 plugin directory tree, finds all `manifest.json` files, and passes
each to `PluginLoader` to register. This is the boot-time discovery sweep that populates
the registry from the filesystem. Also provides a utility to list all available plugins
without loading them (manifest-only scan).

## What It Does NOT Do

- Does NOT watch for changes (that is P1-P3 HotReloader)
- Does NOT load plugins from network
- Does NOT run plugin code during scan — scan is metadata-only until `load=True`

## Public Interface

```python
from pathlib import Path
from typing import List, Dict, Any
from vjlive3.plugins.loader import PluginLoader
from vjlive3.plugins.registry import PluginRegistry

@dataclass
class DiscoveredPlugin:
    manifest_path: Path
    plugin_id: str
    name: str
    version: str
    category: str
    loaded: bool = False
    load_error: Optional[str] = None

class PluginScanner:
    def __init__(
        self,
        registry: PluginRegistry,
        loader: PluginLoader,
    ) -> None: ...

    def scan(self, plugins_root: Path) -> List[DiscoveredPlugin]:
        """Recursively find all manifest.json files under plugins_root.
        Returns list of DiscoveredPlugin. Does NOT load — metadata only."""

    def scan_and_load(self, plugins_root: Path) -> List[DiscoveredPlugin]:
        """Scan + load each discovered plugin. Sets loaded=True on success."""

    def scan_vjlive2_compat(self, plugins_root: Path) -> List[DiscoveredPlugin]:
        """Same as scan() but also recognises VJlive-2 .bundled manifest files."""
```

## Scan Rules

- Find all files named `manifest.json` recursively under `plugins_root`
- Also accept `manifest.json.bundled` (VJlive-2 compatibility)
- Skip `__pycache__/`, `.git/`, `node_modules/`
- Skip manifests that cannot be parsed (log warning, continue)
- Skip manifests missing `id` or `name` fields (log warning, continue)
- No hard limit on number of plugins found

## VJlive-2 Compatibility

VJlive-2 shipped plugins with `manifest.json.bundled` files. The scanner must:
1. Try `manifest.json` first
2. If not found, try `manifest.json.bundled` (strip `.bundled` before loading)
3. Log if bundled format was used: `"Loading bundled manifest for {name}"`

## Edge Cases

- `plugins_root` does not exist: log warning, return empty list
- Zero manifests found: return empty list (not an error)
- Permission error reading a file: log error, continue
- Circular symlinks: detect via `Path.resolve()`, skip already-seen real paths

## Dependencies

- `vjlive3.plugins.registry` (P1-P1)
- `vjlive3.plugins.loader` (P1-P2)
- Standard library: `pathlib`, `json`, `logging`

## Test Plan

| Test | What It Verifies |
|------|-----------------|
| `test_scan_empty_dir` | returns empty list, no crash |
| `test_scan_single_plugin` | finds one manifest.json |
| `test_scan_recursive` | finds manifests in subdirectories |
| `test_scan_skips_pycache` | __pycache__ directories ignored |
| `test_scan_and_load` | loads plugins and sets loaded=True |
| `test_scan_and_load_invalid_manifest` | continues past invalid manifests |
| `test_vjlive2_compat_bundled` | finds .bundled manifest |
| `test_scan_nonexistent_root` | logs warning, returns [] |
| `test_missing_name_field` | skipped with warning |

**Minimum coverage:** 80%

## Definition of Done

- [ ] Spec reviewed by Roo Code before code starts
- [ ] `src/vjlive3/plugins/scanner.py` written, < 750 lines
- [ ] All 9 tests pass using `tmp_path` fixtures
- [ ] BOARD.md P1-P4 updated to ✅ Done
- [ ] Lock released, AGENT_SYNC.md handoff written
