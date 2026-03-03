"""
P1-R3 — WGSL Shader Hot-Reload
Spec: docs/specs/_01_skeletons/P1-R3_WGSL_hot_reload.md
Tier: 🖥️ Pro-Tier Native (filesystem watcher) + 🌐 Bifurcated-Safe (WGSL strings)

Three responsibilities:
  1. ShaderCache      — compile-once cache keyed by WGSL content hash.
  2. reload_shader()  — ADR-018 compliant hot-swap: compile new, then destroy old.
  3. watch_shader_file() — background mtime poller; calls reload_shader on change.
"""

import hashlib
import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ShaderCache:
    """
    Compile-once shader cache keyed by WGSL content SHA-256 hash.

    compile_fn signature: compile_fn(wgsl_source: str, name: str) -> Any
    In production:  lambda src, n: device.create_shader_module(code=src, label=n)
    In tests:       any callable that validates source and returns a mock object.

    Thread-safe via RLock — safe to call from render thread and watcher thread.
    """

    METADATA: dict = {
        "spec": "P1-R3",
        "module": "vjlive3.render.hot_reload",
        "tier": "Pro-Tier Native",
    }

    def __init__(self, compile_fn: Callable[[str, str], Any]) -> None:
        """
        Args:
            compile_fn: Called on cache miss. Must raise on invalid WGSL.
        """
        self._compile_fn = compile_fn
        self._cache: dict[str, Any] = {}   # hash → compiled pipeline
        self._lock = threading.RLock()

    @staticmethod
    def _hash(source: str) -> str:
        return hashlib.sha256(source.encode("utf-8")).hexdigest()

    def get_or_compile(self, wgsl_source: str, name: str = "unnamed") -> Any:
        """
        Return cached compiled pipeline, or compile and cache it.

        Raises:
            RuntimeError: If compile_fn raises (WGSL is invalid).
        """
        key = self._hash(wgsl_source)
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            try:
                compiled = self._compile_fn(wgsl_source, name)
            except Exception as exc:
                raise RuntimeError(
                    f"ShaderCache: WGSL compilation failed for '{name}': {exc}"
                ) from exc
            self._cache[key] = compiled
            logger.debug("ShaderCache: compiled '%s' (hash=%s..)", name, key[:8])
            return compiled

    def invalidate(self, wgsl_source: str) -> None:
        """Remove cached entry for wgsl_source. No-op if not cached."""
        key = self._hash(wgsl_source)
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Flush entire cache. Live effect references are NOT affected."""
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        """Number of entries currently in cache."""
        with self._lock:
            return len(self._cache)


# ---------------------------------------------------------------------------
# reload_shader — ADR-018 compliant hot-swap
# ---------------------------------------------------------------------------

def reload_shader(effect: Any, wgsl_source: str) -> bool:
    """
    Hot-swap the fragment shader on a live Effect.

    ADR-018: compiles NEW pipeline first, then swaps, then destroys old.
    Legacy bug: vjlive/core/effects/shader_base.py line 596 deletes old before
    confirming new compiles — this function is the correct replacement.

    effect must expose:
        .cache:    ShaderCache instance
        .pipeline: current compiled pipeline (Any, or None)
        .name:     str (for logging and pipeline label)

    Returns:
        True if reload succeeded, False if compilation failed (old intact).
    """
    name: str = getattr(effect, "name", "unnamed-effect")
    cache: ShaderCache = effect.cache
    old_pipeline: Any = getattr(effect, "pipeline", None)

    # Force recompile even if source hash was cached (change detection).
    cache.invalidate(wgsl_source)

    # Step 1: Compile NEW pipeline — old stays active.
    try:
        new_pipeline = cache.get_or_compile(wgsl_source, name=name)
    except RuntimeError as exc:
        logger.error("reload_shader: compile failed for '%s': %s", name, exc)
        return False

    # Step 2: Install new pipeline atomically.
    effect.pipeline = new_pipeline

    # Step 3: Destroy old pipeline — AFTER new is confirmed.
    if old_pipeline is not None:
        _safe_destroy(old_pipeline, context=name)

    logger.info("reload_shader: '%s' OK", name)
    return True


def _safe_destroy(pipeline: Any, context: str = "") -> None:
    """Attempt to destroy/release a GPU pipeline without crashing the caller."""
    fn = getattr(pipeline, "destroy", None) or getattr(pipeline, "release", None)
    if fn is not None:
        try:
            fn()
        except Exception as exc:
            logger.warning(
                "_safe_destroy: could not destroy pipeline (%s): %s", context, exc
            )


# ---------------------------------------------------------------------------
# ShaderWatcher — background mtime polling
# ---------------------------------------------------------------------------

class ShaderWatcher:
    """
    Background thread that polls a single .wgsl file for mtime changes
    and calls reload_shader on modification.

    Created by watch_shader_file(); stopped via stop().
    """

    def __init__(
        self,
        path: Path,
        effect: Any,
        poll_interval: float,
    ) -> None:
        self._path = path
        self._effect = effect
        self._interval = poll_interval
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._last_mtime: float = 0.0

    def _poll_loop(self) -> None:
        try:
            self._last_mtime = self._path.stat().st_mtime
        except FileNotFoundError:
            logger.warning("ShaderWatcher: file not found at start: %s", self._path)
            self._last_mtime = 0.0

        while self._running:
            time.sleep(self._interval)
            try:
                current_mtime = self._path.stat().st_mtime
            except FileNotFoundError:
                logger.warning("ShaderWatcher: file deleted: %s", self._path)
                continue

            if current_mtime != self._last_mtime:
                self._last_mtime = current_mtime
                try:
                    source = self._path.read_text(encoding="utf-8")
                except OSError as exc:
                    logger.error("ShaderWatcher: could not read %s: %s", self._path, exc)
                    continue
                logger.info(
                    "ShaderWatcher: change detected in %s — reloading", self._path.name
                )
                reload_shader(self._effect, source)

        logger.debug("ShaderWatcher: poll loop exited for %s", self._path)

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop,
            name=f"shader-watcher-{self._path.name}",
            daemon=True,
        )
        self._thread.start()
        logger.debug("ShaderWatcher: started watching %s", self._path)

    def stop(self) -> None:
        """Stop the background watcher thread. Blocks until thread exits."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self._interval * 2 + 1.0)
            self._thread = None
        logger.debug("ShaderWatcher: stopped watching %s", self._path)

    def is_running(self) -> bool:
        """True if the watcher thread is alive."""
        return self._running and (
            self._thread is not None and self._thread.is_alive()
        )


def watch_shader_file(
    path: "str | Path",
    effect: Any,
    poll_interval: float = 0.5,
) -> ShaderWatcher:
    """
    Start a background watcher that calls reload_shader when path changes.

    Args:
        path:          Filesystem path to a .wgsl file.
        effect:        Live effect (must expose .cache, .pipeline, .name).
        poll_interval: File-check frequency in seconds. Default 0.5s.

    Returns:
        ShaderWatcher with .stop() and .is_running() methods.
    """
    watcher = ShaderWatcher(path=Path(path), effect=effect, poll_interval=poll_interval)
    watcher.start()
    return watcher
