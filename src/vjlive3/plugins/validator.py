"""
Plugin Validator for VJLive3.

Ported directly from VJlive-2/core/plugins/plugin_validator.py.
Static AST analysis for plugin code to enforce security and compliance.
"""

import ast
import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class SecurityViolation(Exception):
    """Raised when plugin code violates security policies."""


class PluginValidator:
    """
    Validates plugin code using static analysis (AST).

    Checks for:
    - Dangerous imports (os, subprocess, socket, etc.)
    - Dangerous built-ins (eval, exec, compile, open)
    - Unknown manifest permission requests

    Source: VJlive-2/core/plugins/plugin_validator.py:PluginValidator
    """

    FORBIDDEN_IMPORTS = {
        'os', 'sys', 'subprocess', 'shutil', 'pickle', 'marshal',
        'http', 'socket', 'urllib', 'requests',
    }

    FORBIDDEN_FUNCTIONS = {
        'eval', 'exec', 'compile', 'open', 'globals', 'locals',
        'getattr', 'setattr', 'delattr', 'input',
    }

    KNOWN_PERMISSIONS = {'network', 'filesystem', 'audio_input', 'video_input', 'admin'}
    
    # Licensing metadata fields for business model integration
    KNOWN_LICENSE_TYPES = {'free', 'paid', 'subscription', 'burst'}
    KNOWN_GPU_TIERS = {'NONE', 'LOW', 'MEDIUM', 'HIGH', 'ULTRA'}
    KNOWN_CATEGORIES = {'core', 'custom', 'experimental', 'depth', 'audio', 'modulator', 'generator'}

    def __init__(self) -> None:
        self.violations: List[str] = []

    def validate_file(self, file_path: str) -> bool:
        """Validate a Python source file. Returns True if safe."""
        try:
            with open(file_path, 'r', encoding='utf-8') as fh:
                source = fh.read()
            return self.validate_source(source, file_path)
        except Exception as exc:
            logger.error("Validation failed for %s: %s", file_path, exc)
            return False

    def validate_source(self, source: str, filename: str = "<string>") -> bool:
        """Validate Python source code string. Returns True if safe."""
        self.violations = []
        try:
            tree = ast.parse(source, filename=filename)
            self._check_tree(tree)
        except SyntaxError as exc:
            logger.error("Syntax error in plugin %s: %s", filename, exc)
            return False

        if self.violations:
            for v in self.violations:
                logger.warning("Security violation in %s: %s", filename, v)
            return False

        return True

    def _check_tree(self, tree: ast.AST) -> None:
        """Walk the AST and collect violations."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                self._check_import(node)
            elif isinstance(node, ast.Call):
                self._check_call(node)

    def _check_import(self, node: ast.AST) -> None:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] in self.FORBIDDEN_IMPORTS:
                    self.violations.append(f"Forbidden import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in self.FORBIDDEN_IMPORTS:
                self.violations.append(f"Forbidden import from: {node.module}")

    def _check_call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            if node.func.id in self.FORBIDDEN_FUNCTIONS:
                self.violations.append(f"Forbidden function call: {node.func.id}")

    def validate_manifest(self, manifest: dict) -> bool:
        """
        Validate plugin manifest schema, permissions, and business metadata.
        Returns True if valid.
        """
        required_fields = {'id', 'version', 'name', 'main'}
        missing = required_fields - set(manifest.keys())
        if missing:
            logger.error("Manifest missing required fields: %s", missing)
            return False

        plugin_id = str(manifest['id'])
        if not plugin_id.replace('-', '_').isidentifier():
            logger.warning("Plugin ID '%s' may cause import issues", plugin_id)

        # Validate permissions
        permissions = manifest.get('permissions', [])
        if not isinstance(permissions, list):
            logger.error("Manifest 'permissions' must be a list")
            return False

        unknown = set(permissions) - self.KNOWN_PERMISSIONS
        if unknown:
            logger.warning("Unknown permissions requested: %s", unknown)

        # Validate licensing metadata (business model integration)
        licensing = manifest.get('licensing', {})
        if licensing:
            # License type validation
            license_type = licensing.get('license_type')
            if license_type and license_type not in self.KNOWN_LICENSE_TYPES:
                logger.warning("Unknown license type: %s", license_type)
            
            # Price validation (must be non-negative number)
            price = licensing.get('price_usd')
            if price is not None:
                try:
                    price_val = float(price)
                    if price_val < 0:
                        logger.error("License price must be non-negative")
                        return False
                except (ValueError, TypeError):
                    logger.error("License price must be a number")
                    return False

            # Subscription price validation
            sub_price = licensing.get('subscription_monthly_usd')
            if sub_price is not None:
                try:
                    sub_val = float(sub_price)
                    if sub_val < 0:
                        logger.error("Subscription price must be non-negative")
                        return False
                except (ValueError, TypeError):
                    logger.error("Subscription price must be a number")
                    return False

            # Trial period validation
            trial_days = licensing.get('trial_period_days')
            if trial_days is not None:
                try:
                    trial_val = int(trial_days)
                    if trial_val < 0:
                        logger.error("Trial period must be non-negative")
                        return False
                except (ValueError, TypeError):
                    logger.error("Trial period must be an integer")
                    return False

            # Burst credits validation
            burst_credits = licensing.get('burst_credits_required')
            if burst_credits is not None:
                try:
                    burst_val = int(burst_credits)
                    if burst_val < 0:
                        logger.error("Burst credits must be non-negative")
                        return False
                except (ValueError, TypeError):
                    logger.error("Burst credits must be an integer")
                    return False

            # Node licensing validation
            node_lic = licensing.get('node_licensing', {})
            if node_lic:
                # Validate enabled flag
                if 'enabled' in node_lic and not isinstance(node_lic['enabled'], bool):
                    logger.error("node_licensing.enabled must be a boolean")
                    return False
                # Validate per_instance flag
                if 'per_instance' in node_lic and not isinstance(node_lic['per_instance'], bool):
                    logger.error("node_licensing.per_instance must be a boolean")
                    return False
                # Validate floating_licenses count
                float_lic = node_lic.get('floating_licenses', 0)
                try:
                    int(float_lic)
                except (ValueError, TypeError):
                    logger.error("node_licensing.floating_licenses must be an integer")
                    return False

            # Entitlements validation
            entitlements = licensing.get('entitlements', {})
            if entitlements:
                # Validate commercial_use
                if 'commercial_use' in entitlements and not isinstance(entitlements['commercial_use'], bool):
                    logger.error("entitlements.commercial_use must be a boolean")
                    return False
                # Validate source_access
                if 'source_access' in entitlements and not isinstance(entitlements['source_access'], bool):
                    logger.error("entitlements.source_access must be a boolean")
                    return False
                # Validate updates_included
                if 'updates_included' in entitlements and not isinstance(entitlements['updates_included'], bool):
                    logger.error("entitlements.updates_included must be a boolean")
                    return False
                # Validate support_level
                support_level = entitlements.get('support_level')
                if support_level and support_level not in {'community', 'standard', 'premium'}:
                    logger.warning("Unknown support_level: %s", support_level)

        # Validate GPU tier requirements
        gpu_tier = manifest.get('gpu_tier', 'NONE')
        if gpu_tier not in self.KNOWN_GPU_TIERS:
            logger.warning("Unknown GPU tier: %s, defaulting to NONE", gpu_tier)

        # Validate OpenGL version format
        min_gl = manifest.get('minimum_opengl_version', '3.1')
        if not re.match(r'^\d+\.\d+$', str(min_gl)):
            logger.warning("Invalid OpenGL version format: %s", min_gl)

        # Validate required extensions list
        req_ext = manifest.get('required_extensions', [])
        if not isinstance(req_ext, list):
            logger.error("required_extensions must be a list")
            return False

        # Validate category
        category = manifest.get('category', 'custom')
        if category not in self.KNOWN_CATEGORIES:
            logger.warning("Unknown category: %s", category)

        return True


__all__ = ["SecurityViolation", "PluginValidator"]
