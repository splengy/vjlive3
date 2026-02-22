from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from vjlive3.plugins.loader import PluginLoader, PluginManifest
from vjlive3.plugins.registry import PluginRegistry

class TestPluginLoaderExtraCoverage:
    def setup_method(self):
        self.reg = PluginRegistry()
        self.loader = PluginLoader(self.reg)

    def test_manifest_os_error(self, tmp_path):
        import os
        p = tmp_path / "denied.json"
        p.touch()
        os.chmod(p, 0o000)
        try:
            with pytest.raises(ValueError, match="Cannot read"):
                PluginManifest(p)
        finally:
            os.chmod(p, 0o644)

    def test_check_dependencies_missing_vjlive_and_module(self, tmp_path):
        p = tmp_path / "req.json"
        p.write_text('{"name": "X", "dependencies": {"vjlive": ">=4.0.0", "missing_sys_module": "1.0"}}')
        m = PluginManifest(p)
        with patch('vjlive3.plugins.loader.semver', MagicMock()) as mock_semver:
            mock_semver.match.return_value = False
            missing = m.check_dependencies()
        assert any("vjlive" in x for x in missing)
        assert any("missing_sys_module" in x for x in missing)

    def test_discover_plugins_permission_error(self):
        with patch('pathlib.Path.exists', return_value=False):
            with patch('pathlib.Path.mkdir', side_effect=PermissionError):
                self.loader.plugin_dirs = [Path('/root/noperm')]
                assert self.loader.discover_plugins() == []

    def test_discover_plugins_bad_manifest_json(self, tmp_path):
        d = tmp_path / "bad"
        d.mkdir()
        (d / "plugin.json").write_text("invalid json")
        self.loader.plugin_dirs = [tmp_path]
        manifests = self.loader.discover_plugins()
        assert manifests == []

    def test_load_plugin_missing_deps(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        p = d / "plugin.json"
        p.write_text('{"name": "X", "dependencies": {"no_such_module": "1.0"}}')
        m = PluginManifest(p)
        assert self.loader.load_plugin(m) is False

    @patch('importlib.util.spec_from_file_location', return_value=None)
    def test_load_plugin_spec_none(self, mock_spec, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        p = d / "plugin.json"
        p.write_text('{"name": "X", "main": "main.py"}')
        (d/"main.py").touch()
        m = PluginManifest(p)
        assert self.loader.load_plugin(m) is False

    def test_load_plugin_no_plugin_class(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        p = d / "plugin.json"
        p.write_text('{"name": "X", "main": "main.py"}')
        (d/"main.py").write_text("x = 1")
        m = PluginManifest(p)
        assert self.loader.load_plugin(m) is False

    def test_load_plugin_exception(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        p = d / "plugin.json"
        p.write_text('{"name": "X", "main": "main.py"}')
        (d/"main.py").write_text("raise RuntimeError('crash')")
        m = PluginManifest(p)
        assert self.loader.load_plugin(m) is False

    def test_unload_plugin_cleanup_exception(self):
        m = MagicMock()
        m.cleanup.side_effect = Exception("cleanup crash")
        self.loader.plugins["crashy"] = m
        assert self.loader.unload_plugin("crashy") is True
