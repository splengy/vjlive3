"""
vjlive3.plugins — Plugin system package.

Unified plugin infrastructure ported from VJlive-2:

# # # # #   api.py        — PluginBase, PluginContext, EffectPlugin, ModifierPlugin, AgentPlugin
  registry.py   — PluginRegistry (thread-safe, status tracking, get_all_modules)
  loader.py     — PluginLoader (plugin.json manifest discovery + importlib loading)
  sandbox.py    — PluginSandbox, PluginPermissions, PluginSecurityManager
  validator.py  — PluginValidator (AST static analysis)
  hot_reload.py — PluginHotReloadWatcher (watchdog-based, debounced)

Sources: VJlive-2/core/plugin_api.py, plugin_loader.py, vjlivest_plugin_system.py,
         plugin_sandbox.py, plugins/plugin_api.py, plugins/sandbox.py,
         plugins/plugin_validator.py, hot_reload_watcher.py
"""


from vjlive3.plugins.registry import (
    PluginStatus,
    PluginInfo,
    PluginRegistry,
    plugin_registry,
    register_plugin,
    get_plugin,
    list_plugins,
    get_plugin_info,
    create_plugin_instance,
    unload_plugin,
    reload_plugin,
    get_all_plugins,
)
from vjlive3.plugins.sandbox import (
    PluginPermissions,
    PluginSandbox,
    PluginSecurityManager,
    get_security_manager,
)

from vjlive3.plugins.loader import (
    PluginManifest,
    PluginLoader,
)
from vjlive3.plugins.hot_reload import (
    PluginFileHandler,
    PluginHotReloadWatcher,
)

__all__ = [
    # registry
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
    # sandbox
    "PluginPermissions",
    "PluginSandbox",
    "PluginSecurityManager",
    "get_security_manager",

    # loader
    "PluginManifest",
    "PluginLoader",
    # hot reload
    "PluginFileHandler",
    "PluginHotReloadWatcher",
]
