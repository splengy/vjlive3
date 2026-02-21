"""Plugin directory scanner for VJLive3.

Recursively scans a directory tree for manifest.json files, loads and
validates them, and optionally bridges them into a NodeRegistry.

Usage::

    from vjlive3.plugins.scanner import PluginScanner
    from vjlive3.graph import global_registry

    scanner = PluginScanner(registry=global_registry)
    result = scanner.scan("/home/happy/Desktop/claude projects/VJlive-2/plugins")
    print(f"Loaded {result['loaded']} manifests, "
          f"registered {result['registered']} nodes")
"""
from __future__ import annotations

from pathlib import Path

from vjlive3.graph.registry import NodeRegistry
from vjlive3.plugins.manifest import PluginManifest
from vjlive3.plugins.node_bridge import bridge_all
from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)


class PluginScanner:
    """Scans directories for manifest.json plugin definitions.

    Args:
        registry: NodeRegistry to register discovered nodes into.
                  Pass None to scan without registering.
    """

    def __init__(self, registry: NodeRegistry | None = None) -> None:
        self._registry = registry
        self._loaded: list[PluginManifest] = []

    @property
    def loaded_manifests(self) -> list[PluginManifest]:
        """All successfully loaded manifests (across all scan calls)."""
        return list(self._loaded)

    def scan(self, directory: str | Path) -> dict:
        """Recursively scan ``directory`` for manifest.json files.

        Args:
            directory: Root directory to search.

        Returns:
            Summary dict with keys: loaded, skipped, registered
        """
        root = Path(directory)
        if not root.is_dir():
            logger.warning("scan: not a directory: %s", root)
            return {"loaded": 0, "skipped": 0, "registered": 0}

        manifest_paths = sorted(root.rglob("manifest.json"))
        logger.info("scan: found %d manifest.json in %s", len(manifest_paths), root)

        fresh: list[PluginManifest] = []
        skipped = 0

        for mp in manifest_paths:
            pm = PluginManifest.load(mp)
            if pm and pm.modules:
                fresh.append(pm)
            else:
                skipped += 1
                logger.debug("Skipped empty/invalid manifest: %s", mp)

        self._loaded.extend(fresh)
        logger.info(
            "scan: loaded=%d skipped=%d (dir=%s)", len(fresh), skipped, root
        )

        registered = 0
        if self._registry is not None and fresh:
            result = bridge_all(fresh, self._registry)
            registered = result.get("registered", 0)

        return {
            "loaded":     len(fresh),
            "skipped":    skipped,
            "registered": registered,
        }

    def reset(self) -> None:
        """Clear the list of loaded manifests."""
        self._loaded.clear()
