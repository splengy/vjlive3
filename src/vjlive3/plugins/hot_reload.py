"""
Plugin Hot Reload Watcher for VJLive3.

Ported from VJlive-2/core/hot_reload_watcher.py.
File watching system for hot-reloading plugins when their source changes.

Requires: watchdog >= 2.0
"""

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# watchdog is optional at import time so tests can run without it
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler as _FSEventHandler
    _HAS_WATCHDOG = True
except ImportError:
    _HAS_WATCHDOG = False
    Observer = None  # type: ignore[assignment,misc]
    _FSEventHandler = object  # type: ignore[assignment,misc]
    logger.warning(
        "[HOT RELOAD] watchdog not installed — hot reload unavailable. "
        "Install with: pip install watchdog"
    )


# ---------------------------------------------------------------------------
# File event handler
# ---------------------------------------------------------------------------

class PluginFileHandler(_FSEventHandler):
    """
    Watches a plugin directory for source file changes.

    Debounces rapid filesystem events (e.g. editors writing temp files)
    using a 500ms cooldown per path.

    Source: VJlive-2/core/hot_reload_watcher.py:ShaderFileHandler
    """

    PLUGIN_EXTENSIONS = ('.py', '.json')   # plugin source + manifest

    def __init__(self, on_modified: Callable[[str], None]) -> None:
        if _HAS_WATCHDOG:
            super().__init__()
        self._on_modified = on_modified
        self._last_modified: Dict[str, float] = {}
        self._debounce_secs: float = 0.5

    def on_modified(self, event) -> None:
        if event.is_directory:
            return

        path = getattr(event, 'src_path', '')
        if not any(path.endswith(ext) for ext in self.PLUGIN_EXTENSIONS):
            return

        now = time.time()
        last = self._last_modified.get(path, 0.0)
        if now - last < self._debounce_secs:
            return

        self._last_modified[path] = now
        self._on_modified(path)

    def on_created(self, event) -> None:
        """Treat newly-created plugin files the same as modifications."""
        self.on_modified(event)


# ---------------------------------------------------------------------------
# Hot reload watcher
# ---------------------------------------------------------------------------

class PluginHotReloadWatcher:
    """
    Watches one or more plugin directories and triggers reload callbacks
    when Python source files or manifests change.

    Usage::

        def on_reload(path: str):
            plugin_loader.reload_from_path(path)

        watcher = PluginHotReloadWatcher(
            plugin_dirs=['./plugins', '~/.vjlive3/plugins'],
            on_change=on_reload,
        )
        watcher.start()
        ...
        watcher.stop()

    Source: VJlive-2/core/hot_reload_watcher.py:HotReloadWatcher
    """

    def __init__(
        self,
        plugin_dirs: List[str],
        on_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.plugin_dirs = [Path(d) for d in plugin_dirs]
        self._on_change = on_change or (lambda path: None)

        self._observer = Observer() if _HAS_WATCHDOG else None
        self._file_handler = PluginFileHandler(self._on_file_changed)

        self._reload_lock = threading.Lock()
        self._pending_path: Optional[str] = None
        self._reload_thread: Optional[threading.Thread] = None

        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for d in self.plugin_dirs:
            if not d.exists():
                try:
                    d.mkdir(parents=True, exist_ok=True)
                    logger.info("[HOT RELOAD] Created plugin dir: %s", d)
                except Exception as exc:
                    logger.warning("[HOT RELOAD] Could not create %s: %s", d, exc)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start watching all plugin directories."""
        if not _HAS_WATCHDOG or self._observer is None:
            logger.warning("[HOT RELOAD] watchdog unavailable — not watching")
            return

        for d in self.plugin_dirs:
            if d.exists():
                self._observer.schedule(self._file_handler, str(d), recursive=True)
                logger.info("[HOT RELOAD] Watching %s", d)

        self._observer.start()
        logger.info("[HOT RELOAD] Started")

    def stop(self) -> None:
        """Stop watching and clean up threads."""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join()
        logger.info("[HOT RELOAD] Stopped")

    # ── Callbacks ────────────────────────────────────────────────────────────

    def _on_file_changed(self, path: str) -> None:
        """Handle a debounced file-change event."""
        logger.info("[HOT RELOAD] Changed: %s", path)

        with self._reload_lock:
            self._pending_path = path
            if self._reload_thread is None or not self._reload_thread.is_alive():
                self._reload_thread = threading.Thread(
                    target=self._reload_async,
                    args=(path,),
                    daemon=True,
                )
                self._reload_thread.start()

    def _reload_async(self, path: str) -> None:
        """Asynchronously invoke the on_change callback."""
        try:
            # Small delay to let the editor finish writing
            time.sleep(0.1)
            self._on_change(path)
        except Exception as exc:
            logger.error("[HOT RELOAD] Reload error for %s: %s", path, exc)
        finally:
            with self._reload_lock:
                self._pending_path = None

    # ── Config ───────────────────────────────────────────────────────────────

    def set_on_change(self, callback: Callable[[str], None]) -> None:
        """Replace the on-change callback at runtime."""
        self._on_change = callback

    def add_plugin_dir(self, path: str) -> None:
        """Add a new directory to watch (hot-add, works while running)."""
        p = Path(path)
        if p not in self.plugin_dirs:
            self.plugin_dirs.append(p)
            if self._observer and self._observer.is_alive() and p.exists():
                self._observer.schedule(self._file_handler, str(p), recursive=True)
                logger.info("[HOT RELOAD] Added watch: %s", p)

    @property
    def is_running(self) -> bool:
        """True if the observer thread is alive."""
        return bool(self._observer and self._observer.is_alive())


__all__ = ["PluginFileHandler", "PluginHotReloadWatcher"]
