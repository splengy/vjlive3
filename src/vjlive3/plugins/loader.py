"""P1-P2 — Plugin Loader

Reads manifest.json, validates it, imports the plugin module, registers class.
Never raises on a bad plugin — all errors are logged and False is returned.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from vjlive3.plugins.registry import PluginRegistry

_log = logging.getLogger(__name__)

# Required fields every manifest.json must have
_REQUIRED_FIELDS = {"id", "name", "version", "description", "author", "category"}


class ManifestValidator:
    """Validates a parsed manifest dict against required schema."""

    def __init__(self) -> None:
        self._errors: List[str] = []

    def validate(self, manifest: Dict[str, Any]) -> bool:
        self._errors = []
        for field in _REQUIRED_FIELDS:
            if field not in manifest:
                self._errors.append(f"Missing required field: '{field}'")
        if not self._errors and len(str(manifest.get("description", ""))) < 5:
            self._errors.append("'description' too short (min 5 chars)")
        return len(self._errors) == 0

    def errors(self) -> List[str]:
        return list(self._errors)


class PluginLoader:
    """Loads plugins from manifest.json files into a PluginRegistry.

    Each manifest.json must live beside a Python file that exposes
    a class attribute named ``plugin_class``.
    """

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry
        self._validator = ManifestValidator()

    # ── Single manifest load ──────────────────────────────────────────────────

    def load_from_manifest(self, manifest_path: Path) -> bool:
        """Load one plugin from its manifest.json.

        Returns True on success, False on any error.  Never raises.
        """
        try:
            return self._load(manifest_path)
        except Exception as exc:  # safety net — should not be reached
            _log.error("Unexpected error loading %s: %s", manifest_path, exc, exc_info=True)
            return False

    def _load(self, manifest_path: Path) -> bool:
        # 1. Read JSON
        if not manifest_path.exists():
            _log.warning("Manifest not found: %s", manifest_path)
            return False

        try:
            raw = manifest_path.read_text(encoding="utf-8")
        except OSError as exc:
            _log.error("Cannot read %s: %s", manifest_path, exc)
            return False

        try:
            manifest: Dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError as exc:
            _log.error("Invalid JSON in %s: %s", manifest_path.name, exc)
            return False

        # 2. Validate required fields
        if not self._validator.validate(manifest):
            _log.error(
                "Manifest validation failed for %s: %s",
                manifest_path.name,
                "; ".join(self._validator.errors()),
            )
            return False

        name: str = manifest["name"]

        # 3. Find the Python module alongside the manifest
        plugin_module_path = self._find_module_path(manifest_path)
        if plugin_module_path is None:
            _log.warning("No Python module found for plugin '%s' (looked beside %s)", name, manifest_path)
            return False

        # 4. Import the module
        module = self._import_module(name, plugin_module_path)
        if module is None:
            return False

        # 5. Get plugin_class attribute
        if not hasattr(module, "plugin_class"):
            _log.warning("Plugin '%s' module missing 'plugin_class' attribute", name)
            return False

        plugin_cls = module.plugin_class

        # 6. Register
        self._registry.register(name, plugin_cls, manifest)
        return True

    def _find_module_path(self, manifest_path: Path) -> Optional[Path]:
        """Return path to .py file beside the manifest, or None."""
        # Try <manifest_stem>.py first, then __init__.py in same dir
        candidates = [
            manifest_path.with_suffix(".py"),
            manifest_path.parent / "__init__.py",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def _import_module(self, plugin_name: str, module_path: Path):
        """Import a Python file by path. Returns module or None on failure."""
        module_name = f"vjlive3_plugin_{plugin_name.replace(' ', '_').lower()}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                _log.error("Cannot create module spec for %s", module_path)
                return None
            mod = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
        except ImportError as exc:
            _log.error("ImportError loading plugin '%s': %s", plugin_name, exc)
        except Exception as exc:
            _log.error("Error executing plugin module '%s': %s", plugin_name, exc, exc_info=True)
        return None

    # ── Directory loading ─────────────────────────────────────────────────────

    def load_directory(self, plugins_dir: Path) -> Dict[str, bool]:
        """Load all plugins in a directory (non-recursive).

        Returns {plugin_name: success} for each manifest found.
        """
        return self._load_from_paths(
            plugins_dir.glob("manifest.json") if plugins_dir.exists() else []
        )

    def load_directory_recursive(self, plugins_root: Path) -> Dict[str, bool]:
        """Recursively load all plugins under plugins_root."""
        return self._load_from_paths(
            plugins_root.rglob("manifest.json") if plugins_root.exists() else []
        )

    def _load_from_paths(self, paths) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for p in paths:
            success = self.load_from_manifest(p)
            results[str(p)] = success
        return results


__all__ = ["PluginLoader", "ManifestValidator"]
