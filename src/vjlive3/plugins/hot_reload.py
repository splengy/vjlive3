"""P1-P3 — Hot-Reloadable Plugin System

Watches plugin directories for filesystem changes and reloads changed plugins
without restarting the engine.  Uses watchdog if available, falls back to polling.
"""
from __future__ import annotations

import importlib
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from vjlive3.plugins.loader import PluginLoader
from vjlive3.plugins.registry import PluginRegistry

_log = logging.getLogger(__name__)

# Try to import watchdog — it's optional
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    _HAS_WATCHDOG = True
except ImportError:
    _HAS_WATCHDOG = False
    _log.warning("watchdog not installed — hot-reload will use polling mode (slower)")


class HotReloader:
    """Watches plugin directories and reloads changed plugins.

    Usage::

        reloader = HotReloader(registry, loader)
        reloader.on_reload(lambda name: print(f"Reloaded: {name}"))
        reloader.watch(Path("plugins/"))
        reloader.start()
        # ... app runs ...
        reloader.stop()
    """

    def __init__(
        self,
        registry: PluginRegistry,
        loader: PluginLoader,
        poll_interval: float = 1.0,
    ) -> None:
        self._registry = registry
        self._loader = loader
        self._poll_interval = poll_interval
        self._watched_dirs: List[Path] = []
        self._callbacks: List[Callable[[str], None]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        # For polling fallback: track mtime per manifest path
        self._mtimes: Dict[Path, float] = {}
        # watchdog observer (used only if watchdog available)
        self._observer = None

    # ── Public API ────────────────────────────────────────────────────────────

    def watch(self, plugins_dir: Path) -> None:
        """Add a directory to watch.  De-duplicates."""
        if plugins_dir not in self._watched_dirs:
            self._watched_dirs.append(plugins_dir)
            _log.debug("HotReloader: watching %s", plugins_dir)

    def on_reload(self, callback: Callable[[str], None]) -> None:
        """Register a callback fired with plugin name after each reload."""
        self._callbacks.append(callback)

    def start(self) -> None:
        """Start background watch thread (non-blocking)."""
        if self._running:
            return
        self._running = True
        if _HAS_WATCHDOG:
            self._start_watchdog()
        else:
            self._start_polling()

    def stop(self) -> None:
        """Stop the watcher.  Blocks until background thread exits."""
        if not self._running:
            return
        self._running = False
        if _HAS_WATCHDOG and self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        _log.debug("HotReloader stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Watchdog backend ──────────────────────────────────────────────────────

    def _start_watchdog(self) -> None:
        handler = _WatchdogHandler(self._reload_manifest)
        self._observer = Observer()
        for d in self._watched_dirs:
            if d.exists():
                self._observer.schedule(handler, str(d), recursive=True)
        self._observer.start()
        _log.info("HotReloader: watchdog mode active")

    # ── Polling backend ───────────────────────────────────────────────────────

    def _start_polling(self) -> None:
        self._thread = threading.Thread(
            target=self._polling_loop,
            name="PluginHotReloadPoller",
            daemon=True,
        )
        self._thread.start()
        _log.info("HotReloader: polling mode active (interval=%.1fs)", self._poll_interval)

    def _polling_loop(self) -> None:
        while self._running:
            self._poll_once()
            time.sleep(self._poll_interval)

    def _poll_once(self) -> None:
        for d in self._watched_dirs:
            if not d.exists():
                continue
            for manifest in d.rglob("manifest.json"):
                try:
                    mtime = manifest.stat().st_mtime
                except OSError:
                    continue
                if self._mtimes.get(manifest) != mtime:
                    self._mtimes[manifest] = mtime
                    if manifest in self._mtimes:  # skip first-seen (initial scan)
                        self._reload_manifest(manifest)
                    else:
                        self._mtimes[manifest] = mtime  # record first seen

    # ── Reload logic ──────────────────────────────────────────────────────────

    def _reload_manifest(self, manifest_path: Path) -> None:
        """Core reload sequence: unregister → force-reimport → re-register."""
        _log.info("HotReloader: change detected — %s", manifest_path)
        import json
        try:
            data = json.loads(manifest_path.read_text())
        except Exception as exc:
            _log.error("HotReloader: cannot read manifest %s: %s", manifest_path, exc)
            return

        name = data.get("name", "")
        if not name:
            return

        # Unregister old class
        self._registry.unregister(name)

        # Force-reimport: remove cached module so importlib picks up source changes
        stale_key = f"vjlive3_plugin_{name.replace(' ', '_').lower()}"
        sys.modules.pop(stale_key, None)

        # Re-register from updated manifest
        ok = self._loader.load_from_manifest(manifest_path)
        if ok:
            _log.info("Hot-reloaded plugin: %s", name)
            self._fire_callbacks(name)
        else:
            _log.error("HotReloader: reload failed for '%s' (syntax error?)", name)

    def _fire_callbacks(self, name: str) -> None:
        for cb in self._callbacks:
            try:
                cb(name)
            except Exception as exc:
                _log.error("on_reload callback error: %s", exc)


# ── Watchdog event handler (only defined when watchdog is available) ──────────

if _HAS_WATCHDOG:
    class _WatchdogHandler(FileSystemEventHandler):  # type: ignore[misc]
        def __init__(self, reload_fn: Callable[[Path], None]) -> None:
            super().__init__()
            self._reload = reload_fn

        def on_modified(self, event: "FileSystemEvent") -> None:
            p = Path(event.src_path)
            if p.name in ("manifest.json", "manifest.json.bundled") or p.suffix == ".py":
                # Find the manifest
                manifest = p if p.name.startswith("manifest") else p.parent / "manifest.json"
                if manifest.exists():
                    self._reload(manifest)

        on_created = on_modified


__all__ = ["HotReloader"]
