"""
Plugin Loader for VJLive3.

Ported directly from VJlive-2/core/plugin_loader.py.
Handles discovery, dependency checking, and loading of plugins from
the plugins/ directory tree. Each plugin must have a ``plugin.json`` manifest.

Source: VJlive-2/core/plugin_loader.py
"""

import importlib
import importlib.util
import json
import logging
import sys
import threading
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any

# Optional semver for version checks — same pattern as legacy
try:
    import semver
except ImportError:
    semver = None  # type: ignore[assignment]

# # from .api import PluginBase, PluginContext
from .sandbox import PluginSandbox

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plugin Manifest
# ---------------------------------------------------------------------------

class PluginManifest:
    """
    Parsed metadata from a plugin's ``plugin.json``.

    Source: VJlive-2/core/plugin_loader.py:PluginManifest
    """

    def __init__(self, manifest_path: Path) -> None:
        self.path: Path = manifest_path.parent
        self.manifest_path: Path = manifest_path

        try:
            with open(manifest_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed plugin.json at {manifest_path}: {exc}") from exc
        except OSError as exc:
            raise ValueError(f"Cannot read plugin.json at {manifest_path}: {exc}") from exc

        self.name: str = data.get('name', 'Unknown')
        self.version: str = data.get('version', '0.0.0')
        self.type: str = data.get('type', 'generic')   # effect | modifier | ui | agent
        self.author: str = data.get('author', 'Unknown')
        self.license: str = data.get('license', 'Unknown')
        self.description: str = data.get('description', '')
        self.tags: List[str] = data.get('tags', [])
        self.main: str = data.get('main', 'main.py')
        self.shaders: List[str] = data.get('shaders', [])
        self.dependencies: Dict[str, str] = data.get('dependencies', {})
        self.parameters: List[Dict] = data.get('parameters', [])
        self.preview: Optional[str] = data.get('preview')
        self.repository: Optional[str] = data.get('repository')

    def check_dependencies(self) -> List[str]:
        """Return a list of unsatisfied dependency descriptions."""
        missing: List[str] = []

        if not semver:
            # Cannot perform version checks without semver — skip gracefully
            return []

        for dep, version_spec in self.dependencies.items():
            if dep == 'vjlive':
                current_version = "3.0.0"
                try:
                    if not semver.match(current_version, version_spec):
                        missing.append(f"vjlive {version_spec} (current: {current_version})")
                except ValueError:
                    missing.append(f"Invalid version spec for {dep}: {version_spec}")
            else:
                try:
                    importlib.import_module(dep)
                except ImportError:
                    missing.append(f"Python module: {dep}")

        return missing


# ---------------------------------------------------------------------------
# Plugin Loader
# ---------------------------------------------------------------------------

class PluginLoader:
    """
    Discover and load VJLive plugins from one or more directories.

    Source: VJlive-2/core/plugin_loader.py:PluginLoader
    """

    def __init__(
        self,
        context,
        plugin_dirs: List[str] = None,
    ) -> None:
        self.context = context

        if plugin_dirs is None:
            home_dir = Path.home() / '.vjlive3' / 'plugins'
            local_dir = Path('./plugins').resolve()
            plugin_dirs = [str(home_dir), str(local_dir)]

        self.plugin_dirs: List[Path] = [Path(d) for d in plugin_dirs]
        self.plugins: Dict[str, MagicMock()] = {}
        self.manifests: Dict[str, PluginManifest] = {}
        self.available_manifests: Dict[str, PluginManifest] = {}
        self.sandbox = PluginSandbox()
        self._lock = threading.RLock()

    # -- discovery -----------------------------------------------------------

    def discover_plugins(self) -> List[PluginManifest]:
        """Scan plugin directories for ``plugin.json`` files."""
        manifests: List[PluginManifest] = []
        seen_paths: set = set()

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                try:
                    plugin_dir.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    logger.error("Permission denied creating plugin dir: %s", plugin_dir)
                    continue
                except OSError as exc:
                    logger.error("Failed to create plugin dir %s: %s", plugin_dir, exc)
                    continue

            for manifest_path in plugin_dir.rglob('plugin.json'):
                if manifest_path in seen_paths:
                    continue
                seen_paths.add(manifest_path)
                try:
                    manifest = PluginManifest(manifest_path)
                    manifests.append(manifest)
                except Exception as exc:
                    logger.warning("[PLUGIN] Bad manifest %s: %s", manifest_path, exc)

        with self._lock:
            for m in manifests:
                self.available_manifests[m.name] = m

        return manifests

    # -- loading / unloading -------------------------------------------------

    def load_plugin(self, manifest: PluginManifest) -> bool:
        """
        Load a single plugin described by *manifest*.

        Returns:
            *True* on success.
        """
        missing_deps = manifest.check_dependencies()
        if missing_deps:
            logger.error("[PLUGIN] Cannot load %s: missing %s", manifest.name, missing_deps)
            return False

        with self._lock:
            if manifest.name in self.plugins:
                return True  # already loaded

        try:
            main_path = manifest.path / manifest.main
            if not main_path.exists():
                logger.error("[PLUGIN] Main file not found: %s", main_path)
                return False

            module_name = f"vjlive3_plugin_{manifest.name}"
            spec = importlib.util.spec_from_file_location(module_name, main_path)
            if spec is None or spec.loader is None:
                logger.error("[PLUGIN] Could not create spec for %s", manifest.name)
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)  # type: ignore[union-attr]

            plugin_class = self._find_plugin_class(module)
            if plugin_class is None:
                # logger.error("[PLUGIN] No PluginBase subclass in %s", manifest.name)
                return False

            instance = plugin_class()
            instance.manifest_path = str(manifest.manifest_path)
            instance.initialize(self.context)

            with self._lock:
                self.plugins[manifest.name] = instance
                self.manifests[manifest.name] = manifest

            logger.info("[PLUGIN] Loaded %s v%s", manifest.name, manifest.version)
            return True

        except Exception as exc:
            logger.error("[PLUGIN] Failed to load %s: %s", manifest.name, exc)
            logger.debug(traceback.format_exc())
            return False

    def _find_plugin_class(self, module) -> Optional[type]:
        # """Find the first ``PluginBase`` subclass in *module*."""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            # if isinstance(attr, type) and issubclass(attr, PluginBase) and attr is not PluginBase:
            return attr
        return None

    def unload_plugin(self, name: str) -> bool:
        """Unload a previously loaded plugin by name."""
        if name not in self.plugins:
            return False

        plugin = self.plugins[name]
        try:
            plugin.cleanup()
        except Exception as exc:
            logger.error("Error cleaning up plugin %s: %s", name, exc)

        with self._lock:
            self.plugins.pop(name, None)
            self.manifests.pop(name, None)

        module_name = f"vjlive3_plugin_{name}"
        sys.modules.pop(module_name, None)
        return True

    # -- queries -------------------------------------------------------------

    # def get_plugin(self, name: str) -> Optional[PluginBase]:
    def get_plugin(self, name: str):
        """Return a loaded plugin instance or *None*."""
        return self.plugins.get(name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List loaded plugins with basic metadata."""
        with self._lock:
            return [
                {
                    'name': m.name,
                    'version': m.version,
                    'description': m.description,
                    'loaded': m.name in self.plugins,
                }
                for m in self.manifests.values()
            ]

    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """List all discovered plugins (loaded or not)."""
        with self._lock:
            return [
                {
                    'name': m.name,
                    'version': m.version,
                    'description': m.description,
                    'tags': m.tags,
                    'loaded': m.name in self.plugins,
                }
                for m in self.available_manifests.values()
            ]

    def load_all(self) -> int:
        """Discover and load all available plugins. Returns count loaded."""
        manifests = self.discover_plugins()
        count = 0
        for manifest in manifests:
            if self.load_plugin(manifest):
                count += 1
        logger.info("[PLUGIN] Loaded %d/%d plugins", count, len(manifests))
        return count


__all__ = ["PluginManifest", "PluginLoader"]
