"""Tests for P1-P2 PluginLoader and P1-P4 PluginScanner"""
import json
import pytest
from pathlib import Path
from vjlive3.plugins.registry import PluginRegistry
from vjlive3.plugins.loader import PluginLoader
from vjlive3.plugins.scanner import PluginScanner, DiscoveredPlugin


_VALID_MANIFEST = {
    "id": "com.test.blur", "name": "Blur", "version": "1.0.0",
    "description": "A simple blur effect", "author": "Test", "category": "effect",
    "tags": [], "parameters": []
}

_VALID_MODULE = """\
class BlurEffect:
    METADATA = {"name": "Blur", "description": "blur " * 10}
    def process(self, frame, audio): return frame

plugin_class = BlurEffect
"""


@pytest.fixture
def reg():
    return PluginRegistry()


@pytest.fixture
def loader(reg):
    return PluginLoader(reg)


@pytest.fixture
def scanner(reg, loader):
    return PluginScanner(reg, loader)


# ── PluginLoader tests ────────────────────────────────────────────────────────

def test_load_valid_manifest(tmp_path, loader, reg):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(_VALID_MANIFEST))
    (tmp_path / "manifest.py").write_text(_VALID_MODULE)
    assert loader.load_from_manifest(manifest) is True
    assert reg.get("Blur") is not None


def test_load_missing_file(tmp_path, loader):
    missing = tmp_path / "ghost" / "manifest.json"
    assert loader.load_from_manifest(missing) is False


def test_load_invalid_json(tmp_path, loader):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{bad json")
    assert loader.load_from_manifest(manifest) is False


def test_load_missing_required_field(tmp_path, loader):
    bad = dict(_VALID_MANIFEST)
    del bad["author"]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(bad))
    (tmp_path / "manifest.py").write_text(_VALID_MODULE)
    assert loader.load_from_manifest(manifest) is False


def test_load_missing_plugin_class(tmp_path, loader):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(_VALID_MANIFEST))
    (tmp_path / "manifest.py").write_text("# no plugin_class here\n")
    assert loader.load_from_manifest(manifest) is False


def test_load_import_error(tmp_path, loader):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(_VALID_MANIFEST))
    (tmp_path / "manifest.py").write_text("raise ImportError('missing dep')\n")
    assert loader.load_from_manifest(manifest) is False


def test_load_directory(tmp_path, loader, reg):
    (tmp_path / "manifest.json").write_text(json.dumps(_VALID_MANIFEST))
    (tmp_path / "manifest.py").write_text(_VALID_MODULE)
    results = loader.load_directory(tmp_path)
    assert any(v for v in results.values())


def test_load_directory_recursive(tmp_path, loader, reg):
    sub = tmp_path / "blur"
    sub.mkdir()
    (sub / "manifest.json").write_text(json.dumps(_VALID_MANIFEST))
    (sub / "manifest.py").write_text(_VALID_MODULE)
    results = loader.load_directory_recursive(tmp_path)
    assert any(v for v in results.values())


# ── PluginScanner tests ───────────────────────────────────────────────────────

def test_scan_empty_dir(tmp_path, scanner):
    result = scanner.scan(tmp_path)
    assert result == []


def test_scan_single_plugin(tmp_path, scanner):
    (tmp_path / "manifest.json").write_text(json.dumps(_VALID_MANIFEST))
    result = scanner.scan(tmp_path)
    assert len(result) == 1
    assert result[0].name == "Blur"


def test_scan_recursive(tmp_path, scanner):
    sub = tmp_path / "effects" / "blur"
    sub.mkdir(parents=True)
    (sub / "manifest.json").write_text(json.dumps(_VALID_MANIFEST))
    result = scanner.scan(tmp_path)
    assert len(result) == 1


def test_scan_skips_pycache(tmp_path, scanner):
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "manifest.json").write_text(json.dumps(_VALID_MANIFEST))
    result = scanner.scan(tmp_path)
    assert result == []


def test_scan_and_load(tmp_path, scanner, reg):
    (tmp_path / "manifest.json").write_text(json.dumps(_VALID_MANIFEST))
    (tmp_path / "manifest.py").write_text(_VALID_MODULE)
    result = scanner.scan_and_load(tmp_path)
    assert len(result) == 1
    assert result[0].loaded is True


def test_scan_and_load_invalid_manifest(tmp_path, scanner):
    (tmp_path / "manifest.json").write_text("{invalid}")
    result = scanner.scan_and_load(tmp_path)
    # scanner itself returns [] because metadata parse failed
    assert result == []


def test_vjlive2_compat_bundled(tmp_path, scanner):
    bundled = tmp_path / "manifest.json.bundled"
    bundled.write_text(json.dumps(_VALID_MANIFEST))
    result = scanner.scan_vjlive2_compat(tmp_path)
    assert len(result) == 1


def test_scan_nonexistent_root(tmp_path, scanner):
    result = scanner.scan(tmp_path / "does_not_exist")
    assert result == []


def test_missing_name_field(tmp_path, scanner):
    bad = dict(_VALID_MANIFEST)
    del bad["name"]
    (tmp_path / "manifest.json").write_text(json.dumps(bad))
    result = scanner.scan(tmp_path)
    assert result == []
