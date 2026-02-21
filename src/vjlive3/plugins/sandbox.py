"""
Plugin Sandbox and Security for VJLive3.

Ported from two complementary legacy implementations:
  - VJlive-2/core/plugin_sandbox.py  (restricted exec + import guard)
  - VJlive-2/core/plugins/sandbox.py (PluginPermissions, context manager, PluginSecurityManager)

These two have been merged for maximum robustness.
"""

import builtins
import logging
import shutil
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

@dataclass
class PluginPermissions:
    """
    Defines what a plugin is allowed to do.

    Source: VJlive-2/core/plugins/sandbox.py:PluginPermissions
    """
    can_access_filesystem: bool = False
    can_access_network: bool = False
    can_access_hardware: bool = False
    can_load_external_modules: bool = False
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    allowed_paths: Set[str] = None
    blocked_paths: Set[str] = None

    def __post_init__(self) -> None:
        if self.allowed_paths is None:
            self.allowed_paths = set()
        if self.blocked_paths is None:
            self.blocked_paths = set()


# ---------------------------------------------------------------------------
# Sandbox
# ---------------------------------------------------------------------------

class PluginSandbox:
    """
    Sandbox environment for plugin execution with restricted permissions.

    Provides isolation by:
    - Restricting file system access to declared allowed_paths
    - Limiting network access
    - Controlling module imports via strict allowlist
    - Monitoring resource usage (memory/CPU limits recorded for future enforcement)
    - Context manager support for scope-based restrictions

    Also supports direct code execution via execute() (from plugin_sandbox.py).

    Limitations:
    - Python-level AST/import restrictor only — not an OS-level sandbox.
      Determined attackers using C-extensions or ctypes may bypass restrictions.

    Source: VJlive-2/core/plugins/sandbox.py + VJlive-2/core/plugin_sandbox.py
    """

    # Builtins safe to expose to plugins (union of both legacy lists)
    ALLOWED_BUILTINS = [
        'abs', 'all', 'any', 'bin', 'bool', 'chr', 'dict', 'enumerate',
        'filter', 'float', 'int', 'isinstance', 'len', 'list', 'map',
        'max', 'min', 'ord', 'range', 'round', 'sorted', 'str', 'sum',
        'tuple', 'zip', 'getattr', 'setattr', 'hasattr', 'print', 'type',
    ]

    # Allowlist for import restriction in execute() mode
    ALLOWED_MODULES = {
        'math', 'random', 'json', 'time', 'datetime', 'itertools',
        'functools', 'collections', 'struct', 're', 'typing',
        'dataclasses', 'logging', 'binascii', 'base64', 'hashlib',
        'string', 'vjlive3.plugins.api',
    }

    # Optional 3rd-party libs allowed for GPU/vision plugins
    ALLOWED_THIRD_PARTY = {'numpy', 'cv2'}

    def __init__(self, permissions: Optional[PluginPermissions] = None) -> None:
        self.permissions = permissions or PluginPermissions()
        self._original_path = list(sys.path)
        self._temp_dir: Optional[str] = None
        self._lock = threading.RLock()

        # Build restricted builtins dict for execute() mode
        self._restricted_builtins = {
            name: getattr(builtins, name)
            for name in self.ALLOWED_BUILTINS
            if hasattr(builtins, name)
        }
        # Allow Exception hierarchy (required for plugin error handling)
        for name in dir(builtins):
            if name.endswith('Error') or name.endswith('Exception') or name == 'Exception':
                self._restricted_builtins[name] = getattr(builtins, name)

    # ── Context manager ─────────────────────────────────────────────────────

    def __enter__(self) -> "PluginSandbox":
        self._enter_sandbox()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._exit_sandbox()

    def _enter_sandbox(self) -> None:
        """Set up sandbox restrictions."""
        with self._lock:
            self._temp_dir = tempfile.mkdtemp(prefix="vjlive3_plugin_")
            # Restrict sys.path to only safe directories
            safe_paths = [p for p in self._original_path if 'site-packages' in p or 'lib' in p]
            sys.path = safe_paths
            logger.debug("Sandbox entered: %s", self._temp_dir)

    def _exit_sandbox(self) -> None:
        """Clean up sandbox restrictions."""
        with self._lock:
            sys.path = self._original_path
            if self._temp_dir and Path(self._temp_dir).exists():
                try:
                    shutil.rmtree(self._temp_dir)
                except Exception as exc:
                    logger.warning("Failed to clean temp dir: %s", exc)
            logger.debug("Sandbox exited")

    # ── Execute mode (restricted exec + import) ─────────────────────────────

    def execute(self, code: str, globals_dict: dict = None, filename: str = "<plugin>") -> None:
        """
        Execute *code* inside the sandbox with restricted builtins and imports.

        Args:
            code: Python source code to execute.
            globals_dict: Optional namespace; will be modified in-place.
            filename: Label used in tracebacks.

        Raises:
            ImportError: If the plugin attempts to import a disallowed module.
            Exception: Any exception raised by the plugin code itself.

        Source: VJlive-2/core/plugin_sandbox.py:PluginSandbox.execute
        """
        if globals_dict is None:
            globals_dict = {}

        globals_dict['__builtins__'] = self._restricted_builtins
        original_import = builtins.__import__

        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            root = name.split('.')[0]
            if root in self.ALLOWED_MODULES or root in self.ALLOWED_THIRD_PARTY:
                return original_import(name, globals, locals, fromlist, level)
            raise ImportError(
                f"Import of '{name}' is not allowed in the VJLive3 plugin sandbox"
            )

        self._restricted_builtins['__import__'] = restricted_import

        try:
            code_obj = compile(code, filename, 'exec')
            exec(code_obj, globals_dict)  # noqa: S102
        except Exception as exc:
            logger.error("Sandbox execution error in %s: %s", filename, exc)
            raise

    # ── Permission checks ────────────────────────────────────────────────────

    def check_file_access(self, path: str) -> bool:
        """Return True if *path* is accessible under current permissions."""
        if not self.permissions.can_access_filesystem:
            return False

        path_obj = Path(path).resolve()

        for blocked in self.permissions.blocked_paths:
            if path_obj.is_relative_to(Path(blocked).resolve()):
                return False

        if self.permissions.allowed_paths:
            for allowed in self.permissions.allowed_paths:
                if path_obj.is_relative_to(Path(allowed).resolve()):
                    return True
            return False

        return True

    def check_network_access(self, host: str, port: int = None) -> bool:
        """Return True if network access to *host* is permitted."""
        return self.permissions.can_access_network

    def validate_import(self, module_name: str) -> bool:
        """Return True if importing *module_name* is permitted."""
        if not self.permissions.can_load_external_modules:
            return False

        root = module_name.split('.')[0]
        if root in self.ALLOWED_MODULES or root in self.ALLOWED_THIRD_PARTY:
            return True

        logger.warning("Sandbox blocked unauthorized import: %s", module_name)
        return False


# ---------------------------------------------------------------------------
# Security Manager
# ---------------------------------------------------------------------------

class PluginSecurityManager:
    """
    Manages sandbox instances and security policies for all plugins.

    Source: VJlive-2/core/plugins/sandbox.py:PluginSecurityManager
    """

    def __init__(self) -> None:
        self.sandboxes: Dict[str, PluginSandbox] = {}
        self.permissions: Dict[str, PluginPermissions] = {}
        self._lock = threading.RLock()

    def create_sandbox(
        self,
        plugin_id: str,
        permissions: Optional[PluginPermissions] = None,
    ) -> PluginSandbox:
        """Create and register a sandbox for *plugin_id*."""
        with self._lock:
            if permissions is None:
                permissions = PluginPermissions()
            self.permissions[plugin_id] = permissions
            sandbox = PluginSandbox(permissions)
            self.sandboxes[plugin_id] = sandbox
            return sandbox

    def get_sandbox(self, plugin_id: str) -> Optional[PluginSandbox]:
        """Return the sandbox for *plugin_id*, or None."""
        return self.sandboxes.get(plugin_id)

    def destroy_sandbox(self, plugin_id: str) -> None:
        """Destroy a plugin's sandbox and clean up temp files."""
        with self._lock:
            sandbox = self.sandboxes.pop(plugin_id, None)
            if sandbox and sandbox._temp_dir and Path(sandbox._temp_dir).exists():
                try:
                    shutil.rmtree(sandbox._temp_dir)
                except Exception as exc:
                    logger.warning("destroy_sandbox cleanup failed for %s: %s", plugin_id, exc)
            self.permissions.pop(plugin_id, None)

    def validate_plugin_manifest(self, manifest: dict) -> bool:
        """
        Security-scan a plugin manifest for suspicious patterns.

        Returns True if manifest passes all checks.
        """
        suspicious_patterns = [
            'eval(', 'exec(', 'compile(', '__import__',
            'subprocess', 'socket', 'multiprocessing',
            'os.system', 'os.popen', 'commands.',
        ]
        if 'entry_point' in manifest:
            entry = manifest['entry_point']
            if any(p in entry for p in suspicious_patterns):
                logger.warning(
                    "Suspicious entry_point in plugin %s", manifest.get('name')
                )
                return False

        dangerous_deps = {'pycrypto', 'cryptography', 'paramiko', 'scapy'}
        for dep in manifest.get('dependencies', []):
            if dep in dangerous_deps:
                logger.warning(
                    "Dangerous dependency '%s' in plugin %s", dep, manifest.get('name')
                )
                return False

        return True


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_security_manager: Optional[PluginSecurityManager] = None


def get_security_manager() -> PluginSecurityManager:
    """Return the global PluginSecurityManager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = PluginSecurityManager()
    return _security_manager


__all__ = [
    "PluginPermissions",
    "PluginSandbox",
    "PluginSecurityManager",
    "get_security_manager",
]
