"""P1-P1 — Plugin Registry

Thread-safe in-memory registry mapping plugin names to classes and metadata.
Plugins register at import time via register(); the host calls get() to retrieve.

METADATA SELF-DOCUMENTATION RULE (PRIME_DIRECTIVE §2):
Every plugin class stored here MUST expose a METADATA dict constant.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

_log = logging.getLogger(__name__)


class PluginStatus(Enum):
    REGISTERED = "registered"
    LOADED     = "loaded"
    ERROR      = "error"
    DISABLED   = "disabled"


@dataclass
class PluginInfo:
    name:          str
    version:       str
    description:   str
    author:        str
    category:      str
    tags:          List[str]
    status:        PluginStatus
    parameters:    List[Dict[str, Any]] = field(default_factory=list)
    inputs:        List[Dict[str, Any]] = field(default_factory=list)
    outputs:       List[Dict[str, Any]] = field(default_factory=list)
    raw_manifest:  Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    instance_count: int = 0


class PluginRegistry:
    """Thread-safe registry for plugin classes and metadata.

    >>> reg = PluginRegistry()
    >>> class FakePlugin:
    ...     METADATA = {"name": "Fake", "description": "x" * 50}
    >>> reg.register("fake", FakePlugin, {"name": "Fake", "version": "1.0.0",
    ...     "description": "x"*50, "author": "A", "category": "effect", "tags": []})
    True
    >>> reg.get("fake") is FakePlugin
    True
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, Type] = {}
        self._info:    Dict[str, PluginInfo] = {}
        self._lock = threading.RLock()

    # ── Registration ─────────────────────────────────────────────────────────

    def register(
        self,
        name: str,
        cls: Type,
        manifest: Dict[str, Any],
    ) -> bool:
        """Register a plugin. Returns True on success, False on error."""
        if not name or not name.strip():
            raise ValueError(f"Plugin name cannot be empty: {name!r}")
        if not callable(cls):
            raise ValueError(f"Plugin class must be callable: {cls!r}")

        with self._lock:
            if name in self._plugins:
                _log.warning("Plugin %r already registered — overwriting", name)

            self._plugins[name] = cls
            self._info[name] = PluginInfo(
                name=manifest.get("name", name),   # prefer manifest display name
                version=manifest.get("version", "1.0.0"),
                description=manifest.get("description", ""),
                author=manifest.get("author", "Unknown"),
                category=manifest.get("category", "effect"),
                tags=manifest.get("tags", []),
                status=PluginStatus.REGISTERED,
                parameters=manifest.get("parameters", []),
                inputs=manifest.get("inputs", []),
                outputs=manifest.get("outputs", []),
                raw_manifest=manifest,
            )
            _log.info("Registered plugin: %s v%s", name, self._info[name].version)
            return True

    def unregister(self, name: str) -> bool:
        """Remove plugin from registry. Returns True if it existed."""
        with self._lock:
            if name not in self._plugins:
                _log.warning("Unregister: plugin %r not found", name)
                return False
            del self._plugins[name]
            if name in self._info:
                self._info[name].status = PluginStatus.DISABLED
            _log.info("Unregistered plugin: %s", name)
            return True

    def clear(self) -> None:
        """Remove all plugins from the registry."""
        with self._lock:
            self._plugins.clear()
            self._info.clear()
            _log.debug("Plugin registry cleared")

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def get(self, name: str) -> Optional[Type]:
        """Return plugin class or None if not found."""
        with self._lock:
            cls = self._plugins.get(name)
            if cls is None:
                _log.warning("Plugin not found: %r", name)
            return cls

    def get_info(self, name: str) -> Optional[PluginInfo]:
        """Return PluginInfo or None."""
        with self._lock:
            return self._info.get(name)

    def list_names(self) -> List[str]:
        """Return sorted list of all registered plugin names."""
        with self._lock:
            return sorted(self._plugins.keys())

    def list_all(self) -> List[PluginInfo]:
        """Return list of all PluginInfo objects."""
        with self._lock:
            return list(self._info.values())

    # ── Multi-module flat expansion ───────────────────────────────────────────

    def get_modules_flat(self) -> List[Dict[str, Any]]:
        """Return a flat list of all modules for the frontend node graph.

        Multi-module plugins (e.g. vbogaudio with modules:[]) are expanded so
        each module is a separate entry with compound ID: "{plugin_id}::{module_id}".
        Single-module plugins produce one entry with ID == plugin_id.
        """
        result: List[Dict[str, Any]] = []
        with self._lock:
            for name, info in self._info.items():
                if not info.raw_manifest:
                    continue
                manifest = info.raw_manifest
                plugin_id = manifest.get("id", name)
                modules = manifest.get("modules", [])
                if not modules:
                    modules = [manifest]  # treat as single-module

                for mod in modules:
                    module_id = mod.get("id", mod.get("slug", ""))
                    compound = (
                        f"{plugin_id}::{module_id}"
                        if module_id and module_id != plugin_id
                        else plugin_id
                    )
                    result.append({
                        "plugin_id":   plugin_id,
                        "module_id":   module_id or plugin_id,
                        "id":          compound,
                        "name":        mod.get("name", module_id or name),
                        "description": mod.get("description", manifest.get("description", "")),
                        "category":    mod.get("category", manifest.get("category", "effect")),
                        "type":        mod.get("type", manifest.get("type", "plugin")),
                        "author":      manifest.get("author", "VJLive"),
                        "version":     manifest.get("version", "1.0.0"),
                        "class_name":  mod.get("class_name", ""),
                        "parameters":  mod.get("parameters", manifest.get("parameters", [])),
                        "inputs":      mod.get("inputs",     manifest.get("inputs", [])),
                        "outputs":     mod.get("outputs",    manifest.get("outputs", [])),
                        "tags":        mod.get("tags",       manifest.get("tags", [])),
                        "icon":        mod.get("icon",       manifest.get("icon", "🔮")),
                    })
        return result

    # ── Instance counting ─────────────────────────────────────────────────────

    def increment_instance_count(self, name: str) -> None:
        """Called by Sandbox when a plugin instance is created."""
        with self._lock:
            if name in self._info:
                self._info[name].instance_count += 1
                self._info[name].status = PluginStatus.LOADED


__all__ = ["PluginRegistry", "PluginInfo", "PluginStatus"]
