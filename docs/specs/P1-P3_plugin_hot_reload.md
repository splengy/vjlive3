# Spec: P1-P3 — Hot-Reloadable Plugin System

**Phase:** Phase 1 / P1-P3
**Assigned To:** Antigravity (Agent 2)
**Authorized By:** Roo Code via DISPATCH.md — SPEC-P1-P3
**Depends On:** P1-P1 (registry), P1-P2 (loader)
**Date:** 2026-02-21

---

## What This Module Does

Watches plugin directories for filesystem changes and automatically reloads changed plugins
without restarting the engine. Uses `watchdog` library (or polling fallback). When a
`manifest.json` or plugin `.py` file changes on disk, the hot-reloader unregisters the old
plugin from the registry and reloads from the updated manifest.

## What It Does NOT Do

- Does NOT sandbox execution (P1-P5)
- Does NOT handle crashes in the reloaded plugin — log and skip (no crash)
- Does NOT work with compiled extensions (`.so`, `.pyd`) — Python source only
- Does NOT block the main thread

## Public Interface

```python
from pathlib import Path
from typing import Callable, Optional
from vjlive3.plugins.loader import PluginLoader
from vjlive3.plugins.registry import PluginRegistry

class HotReloader:
    def __init__(
        self,
        registry: PluginRegistry,
        loader: PluginLoader,
        poll_interval: float = 1.0,
    ) -> None: ...

    def watch(self, plugins_dir: Path) -> None:
        """Add a directory to watch. Can be called multiple times."""

    def start(self) -> None:
        """Start the background watcher thread. Non-blocking."""

    def stop(self) -> None:
        """Stop the watcher thread. Blocks until thread exits."""

    def on_reload(self, callback: Callable[[str], None]) -> None:
        """Register a callback called with plugin name after each reload."""

    @property
    def is_running(self) -> bool: ...
```

## Reload Sequence (on file change detected)

1. Identify which `manifest.json` changed (or find manifest for changed `.py`)
2. Get plugin name from manifest
3. Call `registry.unregister(name)` — removes old class
4. Call `importlib.reload()` on the plugin module to pick up source changes
5. Call `loader.load_from_manifest(manifest_path)` — re-registers fresh class
6. Fire `on_reload` callbacks with plugin name
7. Log: `"Hot-reloaded plugin: {name}"`

## Fallback (no watchdog)

If `watchdog` is not installed, use a polling loop:
- Every `poll_interval` seconds, check `mtime` on all watched files
- Same reload sequence on change
- Log a one-time warning that polling mode is active

## Edge Cases

- Plugin reloads with a syntax error: log error, plugin remains unregistered until fixed
- Directory added after `start()`: `watch()` can be called at any time
- `stop()` called before `start()`: no-op
- Same directory watched twice: de-duplicate

## Dependencies

- `vjlive3.plugins.registry` (P1-P1)
- `vjlive3.plugins.loader` (P1-P2)
- `watchdog` (optional — fallback to polling if absent)
- Standard library: `threading`, `importlib`, `pathlib`, `time`

## Test Plan

| Test | What It Verifies |
|------|-----------------|
| `test_start_stop` | start/stop cycle without errors |
| `test_is_running` | True after start, False after stop |
| `test_reload_on_manifest_change` | modify manifest → plugin re-registered |
| `test_reload_callback_fired` | on_reload callback receives plugin name |
| `test_reload_syntax_error` | bad Python source → logged, no crash |
| `test_watch_multiple_dirs` | two watched dirs both trigger reloads |
| `test_stop_before_start` | no-op, no exception |
| `test_polling_fallback` | works when watchdog absent (mock import) |

**Minimum coverage:** 80%

## Definition of Done

- [ ] Spec reviewed by Roo Code before code starts
- [ ] `src/vjlive3/plugins/hot_reload.py` written, < 750 lines
- [ ] All 8 tests pass
- [ ] BOARD.md P1-P3 updated to ✅ Done
- [ ] Lock released, AGENT_SYNC.md handoff written
