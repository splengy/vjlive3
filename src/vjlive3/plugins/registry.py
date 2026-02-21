"""
Plugin Registry for VJLive3.

Ported from VJlive-2/core/plugins/plugin_api.py.
Thread-safe in-memory registry that maps plugin names to classes/factories.
Supports status tracking, error callbacks, reload, and the multi-module
get_all_modules() interface used by the node graph frontend.
"""

import importlib
import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

class PluginStatus(Enum):
    """Plugin lifecycle status.

    Source: VJlive-2/core/plugins/plugin_api.py:PluginStatus
    """
    REGISTERED = "registered"
    LOADED = "loaded"
    ERROR = "error"
    DISABLED = "disabled"


# ---------------------------------------------------------------------------
# Info container
# ---------------------------------------------------------------------------

@dataclass
class PluginInfo:
    """
    Metadata container for a registered plugin.

    Source: VJlive-2/core/plugins/plugin_api.py:PluginInfo
    """
    name: str
    class_path: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    status: PluginStatus
    error_message: Optional[str] = None
    load_time: Optional[float] = None
    instance_count: int = 0
    raw_manifest: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class PluginRegistry:
    """
    Enhanced thread-safe plugin registry with error handling and validation.

    Plugins call register_plugin() at import time to make themselves
    discoverable.  The host calls get_plugin() to obtain the class and
    instantiate it.

    Source: VJlive-2/core/plugins/plugin_api.py:PluginRegistry
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, Type] = {}
        self._metadata: Dict[str, PluginInfo] = {}
        self._lock = threading.RLock()
        self._error_callbacks: List[Callable[[str], None]] = []

    # ── Registration / unload / reload ──────────────────────────────────────

    def register_plugin(
        self,
        name: str,
        plugin_class: Type,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register a plugin with validation and error handling.

        Args:
            name: Plugin name / identifier.
            plugin_class: Plugin class or factory callable.
            metadata: Optional manifest dict.

        Returns:
            True if registration succeeded.
        """
        try:
            with self._lock:
                if not isinstance(name, str) or not name.strip():
                    raise ValueError(f"Invalid plugin name: {name!r}")
                if not callable(plugin_class):
                    raise ValueError(f"Plugin must be callable: {plugin_class}")

                if name in self._plugins:
                    logger.warning("Plugin %s already registered — overwriting", name)

                self._plugins[name] = plugin_class

                default: Dict[str, Any] = {
                    'name': name,
                    'class_path': f"{plugin_class.__module__}.{plugin_class.__qualname__}",
                    'version': '1.0.0',
                    'description': f'Plugin: {name}',
                    'author': 'Unknown',
                    'dependencies': [],
                    'status': PluginStatus.REGISTERED,
                    'error_message': None,
                    'load_time': None,
                    'instance_count': 0,
                }
                if metadata:
                    # Only pull keys that PluginInfo actually has
                    valid_fields = {f for f in PluginInfo.__dataclass_fields__}
                    default.update({k: v for k, v in metadata.items() if k in valid_fields})
                    default['raw_manifest'] = metadata

                self._metadata[name] = PluginInfo(**default)
                logger.info("Registered plugin: %s", name)
                return True

        except Exception as exc:
            logger.error("Failed to register plugin %s: %s", name, exc)
            self._metadata[name] = PluginInfo(
                name=name,
                class_path=str(plugin_class) if plugin_class else 'Unknown',
                version='1.0.0',
                description=f'Plugin: {name}',
                author='Unknown',
                dependencies=[],
                status=PluginStatus.ERROR,
                error_message=str(exc),
            )
            self._notify_error_callbacks(f"Plugin registration failed for {name}: {exc}")
            return False

    def unload_plugin(self, name: str) -> bool:
        """Unload a registered plugin by name."""
        try:
            with self._lock:
                if name not in self._plugins:
                    logger.warning("Plugin not found: %s", name)
                    return False
                del self._plugins[name]
                if name in self._metadata:
                    self._metadata[name].status = PluginStatus.DISABLED
                    self._metadata[name].instance_count = 0
                logger.info("Unloaded plugin: %s", name)
                return True
        except Exception as exc:
            logger.error("Failed to unload plugin %s: %s", name, exc)
            return False

    def reload_plugin(self, name: str) -> bool:
        """Reload a plugin by re-importing its module."""
        try:
            with self._lock:
                if name not in self._plugins:
                    logger.warning("Plugin not found: %s", name)
                    return False
                info = self._metadata.get(name)
                if not info:
                    return False
                module_path = info.class_path
                if '.' in module_path:
                    module_name = module_path.rsplit('.', 1)[0]
                    try:
                        importlib.reload(importlib.import_module(module_name))
                        logger.info("Reloaded plugin module: %s", module_name)
                        return True
                    except Exception as exc:
                        logger.error("Failed to reload %s: %s", module_name, exc)
                        return False
                return False
        except Exception as exc:
            logger.error("Failed to reload plugin %s: %s", name, exc)
            return False

    def cleanup_all_plugins(self) -> None:
        """Unload all plugins (for clean shutdown)."""
        with self._lock:
            for name in list(self._plugins.keys()):
                self.unload_plugin(name)
        logger.info("All plugins cleaned up")

    # ── Instantiation ────────────────────────────────────────────────────────

    def get_plugin(self, name: str) -> Optional[Type]:
        """Return the plugin class for *name*, or None."""
        try:
            with self._lock:
                cls = self._plugins.get(name)
                if cls is None:
                    logger.warning("Plugin not found: %s", name)
                    return None
                if name in self._metadata:
                    self._metadata[name].status = PluginStatus.REGISTERED
                    self._metadata[name].error_message = None
                return cls
        except Exception as exc:
            logger.error("Failed to get plugin %s: %s", name, exc)
            if name in self._metadata:
                self._metadata[name].status = PluginStatus.ERROR
                self._metadata[name].error_message = str(exc)
            return None

    def create_plugin_instance(self, name: str, *args, **kwargs) -> Optional[Any]:
        """Create and return a new instance of plugin *name*."""
        try:
            with self._lock:
                cls = self.get_plugin(name)
                if cls is None:
                    return None
                instance = cls(*args, **kwargs)
                if name in self._metadata:
                    self._metadata[name].status = PluginStatus.LOADED
                    self._metadata[name].load_time = time.time()
                    self._metadata[name].instance_count += 1
                logger.info("Created plugin instance: %s", name)
                return instance
        except Exception as exc:
            logger.error("Failed to create instance of %s: %s", name, exc)
            if name in self._metadata:
                self._metadata[name].status = PluginStatus.ERROR
                self._metadata[name].error_message = str(exc)
            self._notify_error_callbacks(f"Plugin instance creation failed for {name}: {exc}")
            return None

    # ── Queries ───────────────────────────────────────────────────────────────

    def list_plugins(self) -> List[str]:
        """Return names of all registered plugins."""
        with self._lock:
            return list(self._plugins.keys())

    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """Return detailed info for a plugin, or None."""
        with self._lock:
            return self._metadata.get(name)

    def get_all_plugin_info(self) -> Dict[str, PluginInfo]:
        """Return info for all registered plugins."""
        with self._lock:
            return dict(self._metadata)

    def get_plugins_by_status(self, status: PluginStatus) -> List[str]:
        """Return plugin names filtered by status."""
        with self._lock:
            return [n for n, info in self._metadata.items() if info.status == status]

    def get_error_plugins(self) -> List[str]:
        """Return names of all plugins currently in ERROR state."""
        return self.get_plugins_by_status(PluginStatus.ERROR)

    def validate_plugin_dependencies(self, name: str) -> Dict[str, bool]:
        """Return dict {dep_name: is_satisfied} for plugin *name*."""
        try:
            with self._lock:
                info = self._metadata.get(name)
                if not info:
                    return {}
                return {dep: (dep in self._plugins) for dep in info.dependencies}
        except Exception as exc:
            logger.error("Failed to validate dependencies for %s: %s", name, exc)
            return {}

    def get_all_modules(self) -> List[Dict[str, Any]]:
        """
        Return a flat list of all modules across all plugins for the frontend.

        Supports multi-module plugins (e.g. vbogaudio with 84 modules)
        by expanding the 'modules' array from each manifest.

        Source: VJlive-2/core/plugins/plugin_api.py:PluginRegistry.get_all_modules
        """
        result: List[Dict[str, Any]] = []
        with self._lock:
            for name, info in self._metadata.items():
                if not info.raw_manifest:
                    continue

                manifest = info.raw_manifest
                plugin_id = manifest.get('id', name)

                modules = manifest.get('modules', [])
                if not modules:
                    # Single-module plugin — treat the manifest itself as the module
                    modules = [manifest]

                for mod in modules:
                    module_id = mod.get('id', mod.get('slug', ''))
                    if not module_id:
                        module_id = plugin_id

                    compound_id = (
                        f"{plugin_id}::{module_id}"
                        if module_id != plugin_id
                        else plugin_id
                    )

                    entry: Dict[str, Any] = {
                        'plugin_id': plugin_id,
                        'module_id': module_id,
                        'id': compound_id,
                        'name': mod.get('name', module_id),
                        'description': mod.get('description', manifest.get('description', '')),
                        'category': mod.get('category', manifest.get('category', 'plugin')),
                        'type': mod.get('type', manifest.get('type', 'plugin')),
                        'author': manifest.get('author', 'VJLive'),
                        'version': manifest.get('version', '1.0.0'),
                        'class_name': mod.get('class_name', ''),
                        'parameters': mod.get('parameters', manifest.get('parameters', [])),
                        'inputs': mod.get('inputs', manifest.get('inputs', [])),
                        'outputs': mod.get('outputs', manifest.get('outputs', [])),
                        'tags': mod.get('tags', manifest.get('tags', [])),
                        'gpu_tier': manifest.get('gpu_tier', 'NONE'),
                        'icon': mod.get('icon', '🔮'),
                    }
                    result.append(entry)
        return result

    # ── Error callbacks ───────────────────────────────────────────────────────

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback to be called when plugin errors occur."""
        self._error_callbacks.append(callback)

    def _notify_error_callbacks(self, message: str) -> None:
        for cb in self._error_callbacks:
            try:
                cb(message)
            except Exception as exc:
                logger.error("Error callback raised: %s", exc)


# ---------------------------------------------------------------------------
# Module-level singleton + legacy shims
# ---------------------------------------------------------------------------

plugin_registry = PluginRegistry()


def register_plugin(name: str, cls: Type, metadata: Optional[Dict] = None) -> bool:
    """Module-level shim — delegates to global plugin_registry."""
    return plugin_registry.register_plugin(name, cls, metadata)


def get_plugin(name: str) -> Optional[Type]:
    """Module-level shim — delegates to global plugin_registry."""
    return plugin_registry.get_plugin(name)


def list_plugins() -> List[str]:
    """Module-level shim — delegates to global plugin_registry."""
    return plugin_registry.list_plugins()


def get_plugin_info(name: str) -> Optional[PluginInfo]:
    """Module-level shim — delegates to global plugin_registry."""
    return plugin_registry.get_plugin_info(name)


def create_plugin_instance(name: str, *args, **kwargs) -> Optional[Any]:
    """Module-level shim — delegates to global plugin_registry."""
    return plugin_registry.create_plugin_instance(name, *args, **kwargs)


def unload_plugin(name: str) -> bool:
    """Module-level shim — delegates to global plugin_registry."""
    return plugin_registry.unload_plugin(name)


def reload_plugin(name: str) -> bool:
    """Module-level shim — delegates to global plugin_registry."""
    return plugin_registry.reload_plugin(name)


def get_all_plugins() -> Dict[str, Type]:
    """Return all registered plugin classes keyed by name."""
    return {n: plugin_registry.get_plugin(n) for n in plugin_registry.list_plugins()}


__all__ = [
    "PluginStatus",
    "PluginInfo",
    "PluginRegistry",
    "plugin_registry",
    "register_plugin",
    "get_plugin",
    "list_plugins",
    "get_plugin_info",
    "create_plugin_instance",
    "unload_plugin",
    "reload_plugin",
    "get_all_plugins",
]
