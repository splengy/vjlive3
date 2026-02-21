"""P1-P4 — Plugin Scanner (auto-discovery)

Walks plugin directory trees, finds manifest.json files, passes each to PluginLoader.
Supports VJlive-2 .bundled manifest format for backward compatibility.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Generator, Iterator, List, Optional, Set

from vjlive3.plugins.loader import PluginLoader
from vjlive3.plugins.registry import PluginRegistry

_log = logging.getLogger(__name__)

_SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".tox", ".venv", "venv"}


@dataclass
class DiscoveredPlugin:
    manifest_path: Path
    plugin_id:     str
    name:          str
    version:       str
    category:      str
    loaded:        bool = False
    load_error:    Optional[str] = None


class PluginScanner:
    """Recursively discovers manifest.json files and optionally loads them."""

    def __init__(self, registry: PluginRegistry, loader: PluginLoader) -> None:
        self._registry = registry
        self._loader = loader

    # ── Public API ────────────────────────────────────────────────────────────

    def scan(self, plugins_root: Path) -> List[DiscoveredPlugin]:
        """Scan for manifests without loading.  Metadata-only pass."""
        return list(self._iter_discovered(plugins_root))

    def scan_and_load(self, plugins_root: Path) -> List[DiscoveredPlugin]:
        """Scan and load each discovered plugin."""
        discovered = list(self._iter_discovered(plugins_root))
        for dp in discovered:
            ok = self._loader.load_from_manifest(dp.manifest_path)
            dp.loaded = ok
            if not ok:
                dp.load_error = "load_from_manifest returned False"
        return discovered

    def scan_vjlive2_compat(self, plugins_root: Path) -> List[DiscoveredPlugin]:
        """Same as scan() but also finds .bundled manifest files from VJlive-2."""
        return list(self._iter_discovered(plugins_root, include_bundled=True))

    # ── Internal ──────────────────────────────────────────────────────────────

    def _iter_discovered(
        self,
        plugins_root: Path,
        include_bundled: bool = False,
    ) -> Iterator[DiscoveredPlugin]:
        if not plugins_root.exists():
            _log.warning("Plugin root does not exist: %s", plugins_root)
            return

        seen_real: Set[Path] = set()  # guard against circular symlinks

        for manifest_path in self._find_manifests(plugins_root, include_bundled):
            real = manifest_path.resolve()
            if real in seen_real:
                _log.debug("Skipping already-seen path (symlink?): %s", manifest_path)
                continue
            seen_real.add(real)

            dp = self._read_manifest_metadata(manifest_path)
            if dp is not None:
                yield dp

    def _find_manifests(
        self,
        root: Path,
        include_bundled: bool,
    ) -> Generator[Path, None, None]:
        """Walk root, skipping known non-plugin dirs."""
        for path in root.rglob("*"):
            # Skip directories
            if path.is_dir():
                continue
            # Skip files inside ignored dirs
            if any(skip in path.parts for skip in _SKIP_DIRS):
                continue

            if path.name == "manifest.json":
                yield path
            elif include_bundled and path.name == "manifest.json.bundled":
                _log.debug("Found bundled manifest: %s", path)
                yield path  # loader handles .bundled transparently

    def _read_manifest_metadata(self, manifest_path: Path) -> Optional[DiscoveredPlugin]:
        """Parse just enough from manifest to create a DiscoveredPlugin."""
        try:
            raw = manifest_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except OSError as exc:
            _log.error("Cannot read manifest %s: %s", manifest_path, exc)
            return None
        except json.JSONDecodeError as exc:
            _log.warning("Invalid JSON in %s: %s", manifest_path.name, exc)
            return None

        name = data.get("name", "").strip()
        plugin_id = data.get("id", "").strip()

        if not name:
            _log.warning("Manifest missing 'name' field: %s — skipping", manifest_path)
            return None

        return DiscoveredPlugin(
            manifest_path=manifest_path,
            plugin_id=plugin_id or name,
            name=name,
            version=data.get("version", "1.0.0"),
            category=data.get("category", "unknown"),
        )


__all__ = ["PluginScanner", "DiscoveredPlugin"]
