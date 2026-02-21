"""Tests for plugin manifest schema (PluginParam, ModuleManifest, PluginManifest)."""
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from vjlive3.plugins.manifest import PluginParam, ModuleManifest, PluginManifest


# ---- PluginParam --------------------------------------------------------

def test_param_defaults():
    p = PluginParam.from_dict({"id": "gain", "name": "Gain"})
    assert p.id == "gain"
    assert p.type == "float"
    assert p.default == 0.0

def test_param_from_dict_full():
    p = PluginParam.from_dict({
        "id": "speed", "name": "Speed",
        "type": "float", "min": 0.5, "max": 5.0, "default": 1.0
    })
    assert p.min == 0.5
    assert p.max == 5.0
    assert p.default == 1.0

def test_param_clamp():
    p = PluginParam.from_dict({"id": "x", "name": "x", "min": 0.0, "max": 1.0, "default": 0.5})
    assert p.clamp(-1.0) == 0.0
    assert p.clamp(2.0) == 1.0
    assert p.clamp(0.7) == pytest.approx(0.7)


# ---- ModuleManifest -----------------------------------------------------

def test_module_from_dict_minimal():
    m = ModuleManifest.from_dict({"id": "blur", "name": "Blur"})
    assert m.id == "blur"
    assert m.name == "Blur"
    assert m.gpu_tier == "NONE"
    assert m.is_valid()

def test_module_invalid_without_id():
    m = ModuleManifest.from_dict({"name": "Blur"})
    assert not m.is_valid()

def test_module_invalid_gpu_tier_defaults_none():
    m = ModuleManifest.from_dict({"id": "x", "name": "X", "gpu_tier": "ULTRA"})
    assert m.gpu_tier == "NONE"  # Corrected to default

def test_module_parameters_parsed():
    m = ModuleManifest.from_dict({
        "id": "blur", "name": "Blur",
        "parameters": [
            {"id": "radius", "name": "Radius", "type": "float", "min": 0.0, "max": 20.0, "default": 5.0}
        ]
    })
    assert len(m.parameters) == 1
    assert m.parameters[0].id == "radius"

def test_module_node_type_falls_back_to_id():
    m = ModuleManifest.from_dict({"id": "blur", "name": "Blur"})
    assert m.node_type == "blur"


# ---- PluginManifest.load ------------------------------------------------

def _write_manifest(tmp_dir: Path, data: dict) -> Path:
    path = tmp_dir / "manifest.json"
    path.write_text(json.dumps(data))
    return path


def test_load_valid_manifest(tmp_path):
    data = {
        "collection": "testplugin",
        "source": "standalone",
        "modules": [
            {"id": "test_node", "name": "Test Node", "category": "effect",
             "gpu_tier": "NONE", "node_type": "TEST_NODE",
             "parameters": [{"id": "val", "name": "Val", "min": 0.0, "max": 10.0, "default": 5.0}]}
        ]
    }
    mp = _write_manifest(tmp_path, data)
    pm = PluginManifest.load(mp)
    assert pm is not None
    assert pm.collection == "testplugin"
    assert len(pm.modules) == 1
    assert pm.modules[0].id == "test_node"
    assert len(pm.modules[0].parameters) == 1


def test_load_invalid_json_returns_none(tmp_path):
    mp = tmp_path / "manifest.json"
    mp.write_text("NOT VALID JSON {{{")
    pm = PluginManifest.load(mp)
    assert pm is None


def test_load_manifest_skips_invalid_modules(tmp_path):
    data = {
        "collection": "mix",
        "source": "standalone",
        "modules": [
            {"id": "good", "name": "Good"},
            {"name": "BadNoId"},   # missing id
        ]
    }
    mp = _write_manifest(tmp_path, data)
    pm = PluginManifest.load(mp)
    assert pm is not None
    assert len(pm.modules) == 1
    assert pm.modules[0].id == "good"


def test_load_missing_file_returns_none():
    pm = PluginManifest.load(Path("/tmp/totally_nonexistent_manifest.json"))
    assert pm is None


def test_load_collection_from_directory_name(tmp_path):
    """If manifest has no 'collection' key, use parent dir name."""
    data = {"modules": [{"id": "foo", "name": "Foo"}]}
    mp = _write_manifest(tmp_path, data)
    pm = PluginManifest.load(mp)
    assert pm.collection == tmp_path.name
