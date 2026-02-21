# Spec: P1-P2 — Plugin Loader

**Phase:** Phase 1 / P1-P2
**Assigned To:** Antigravity (Agent 2)
**Authorized By:** Roo Code via DISPATCH.md — SPEC-P1-P2
**Depends On:** P1-P1 (PluginRegistry must exist)
**Date:** 2026-02-21

---

## What This Module Does

Reads plugin `manifest.json` files from disk, validates them against the manifest schema,
imports the plugin Python module, and registers the plugin class into `PluginRegistry`.
This is the bridge between filesystem and the in-memory registry.

## What It Does NOT Do

- Does NOT scan for plugin directories (that is P1-P4 PluginScanner)
- Does NOT sandbox execution (that is P1-P5)
- Does NOT hot-reload (that is P1-P3)
- Does NOT hit any network or cloud API

## Public Interface

```python
from pathlib import Path
from typing import Dict, Any, Optional
from vjlive3.plugins.registry import PluginRegistry

class ManifestValidator:
    """Validates manifest.json content against schema."""
    def validate(self, manifest: Dict[str, Any]) -> bool: ...
    def errors(self) -> List[str]: ...

class PluginLoader:
    def __init__(self, registry: PluginRegistry) -> None: ...
    
    def load_from_manifest(self, manifest_path: Path) -> bool:
        """Load a single plugin from its manifest.json path.
        Returns True if loaded successfully, False otherwise.
        Never raises — all errors are logged."""
    
    def load_directory(self, plugins_dir: Path) -> Dict[str, bool]:
        """Load all plugins found in plugins_dir (non-recursive).
        Returns {plugin_name: success_bool} for each manifest found."""
    
    def load_directory_recursive(self, plugins_root: Path) -> Dict[str, bool]:
        """Recursively load all plugins under plugins_root."""
```

## Manifest Schema

Required fields in every `manifest.json`:
```json
{
  "id": "com.vjlive.plugin_name",
  "name": "Human Name",
  "version": "1.0.0",
  "description": "≥ 10 chars",
  "author": "string",
  "category": "effect | generator | modulator | utility",
  "plugin_class": "ClassName"
}
```

Optional fields:
- `modules: []` — multi-module plugin (vbogaudio pattern)
- `tags: []`
- `parameters: []`
- `inputs: []`
- `outputs: []`

## Loading Sequence (per manifest)

1. Read and parse JSON — on error: log, return False
2. Validate required fields — on error: log, return False
3. Look for `<manifest_stem>.py` (or `__init__.py` in same directory)
4. `importlib.import_module()` the plugin module
5. Get `plugin_class` attribute from module
6. Call `registry.register(name, cls, manifest)`
7. Return True

## Edge Cases

- Missing manifest file: log warning, return False
- Invalid JSON: log error with filename, return False
- Missing `plugin_class` attribute on module: log warning, return False
- Import error: log error, return False — does NOT crash the app
- Directory with no manifests: return empty dict (not an error)

## Dependencies

- `vjlive3.plugins.registry` (P1-P1)
- Standard library: `importlib`, `json`, `pathlib`, `logging`
- No external libraries required

## Test Plan

| Test | What It Verifies |
|------|-----------------|
| `test_load_valid_manifest` | happy path: manifest + module → registered in registry |
| `test_load_missing_file` | returns False, no crash |
| `test_load_invalid_json` | returns False, error logged |
| `test_load_missing_required_field` | returns False, error logged |
| `test_load_missing_plugin_class` | returns False, warning logged |
| `test_load_import_error` | returns False, error logged, app continues |
| `test_load_directory` | loads all valid manifests in a dir |
| `test_load_directory_recursive` | traverses subdirectories |
| `test_multi_module_manifest` | vbogaudio-style manifest loads correctly |

**Minimum coverage:** 80%

## Definition of Done

- [ ] Spec reviewed by Roo Code before code starts
- [ ] `src/vjlive3/plugins/loader.py` written, < 750 lines
- [ ] All 9 tests pass with tmp_path fixtures (no real filesystem)
- [ ] BOARD.md P1-P2 updated to ✅ Done
- [ ] Lock released, AGENT_SYNC.md handoff written
