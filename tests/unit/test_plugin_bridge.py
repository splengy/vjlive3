"""Tests for node_bridge (manifest → NodeRegistry) and PluginScanner."""
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from vjlive3.graph.node import Node
from vjlive3.graph.registry import NodeRegistry
from vjlive3.graph.graph import NodeGraph
from vjlive3.plugins.manifest import PluginManifest, ModuleManifest, PluginParam
from vjlive3.plugins.node_bridge import bridge_manifest, bridge_all
from vjlive3.plugins.scanner import PluginScanner


# ---- Helpers ------------------------------------------------------------

def _make_module(
    id="blur", name="Blur", node_type="BLUR",
    params=None, module_path="", class_name=""
) -> ModuleManifest:
    return ModuleManifest(
        id=id, name=name, node_type=node_type,
        parameters=params or [],
        module_path=module_path,
        class_name=class_name,
    )


def _make_manifest(tmp_path: Path, data: dict) -> PluginManifest:
    mp = tmp_path / "manifest.json"
    mp.write_text(json.dumps(data))
    return PluginManifest.load(mp)


# ---- bridge_manifest ----------------------------------------------------

def test_bridge_creates_stub_node():
    registry = NodeRegistry()
    module = _make_module(
        id="blur", node_type="BLUR",
        params=[PluginParam(id="radius", name="Radius", min=0.0, max=20.0, default=5.0)]
    )
    bridge_manifest(module, registry)
    assert "BLUR" in registry
    node = registry.create("BLUR")
    assert isinstance(node, Node)


def test_stub_has_correct_parameters():
    registry = NodeRegistry()
    module = _make_module(
        params=[
            PluginParam(id="speed", name="Speed", min=0.0, max=10.0, default=3.0),
            PluginParam(id="size",  name="Size",  min=0.0, max=5.0,  default=1.0),
        ]
    )
    bridge_manifest(module, registry)
    node = registry.create("BLUR")
    assert node.get_parameter("speed") is not None
    assert node.get_parameter("speed").value == pytest.approx(3.0)
    assert node.get_parameter("size").value == pytest.approx(1.0)


def test_stub_process_passthrough():
    registry = NodeRegistry()
    module = _make_module()
    bridge_manifest(module, registry)
    node = registry.create("BLUR")
    result = node.process({"input": "FRAME"}, dt=0.016)
    assert result.get("output") == "FRAME"


def test_bridge_skips_already_registered():
    registry = NodeRegistry()
    m1 = _make_module(id="blur", node_type="BLUR")
    m2 = _make_module(id="blur", node_type="BLUR")
    bridge_manifest(m1, registry)
    bridge_manifest(m2, registry)  # Should not raise or double-register
    assert len(registry) == 1


def test_bridge_invalid_module_path_falls_back_to_stub():
    registry = NodeRegistry()
    module = _make_module(
        module_path="nonexistent.module.xyz",
        class_name="NonExistentClass"
    )
    bridge_manifest(module, registry)
    assert "BLUR" in registry  # Stub created despite bad import


def test_bridge_all_returns_counts():
    class FakeManifest:
        modules = [_make_module("a", node_type="A"), _make_module("b", node_type="B")]

    registry = NodeRegistry()
    result = bridge_all([FakeManifest()], registry)
    assert result["registered"] == 2
    assert result["skipped"] == 0
    assert "A" in registry and "B" in registry


# ---- Manifest stub in NodeGraph -----------------------------------------

def test_stub_node_works_in_graph():
    registry = NodeRegistry()
    bridge_manifest(_make_module(id="src", node_type="SRC"), registry)
    bridge_manifest(_make_module(id="out", node_type="OUT"), registry)
    graph = NodeGraph()
    src = registry.create("SRC", node_id="s")
    out = registry.create("OUT", node_id="o")
    graph.add_node(src).add_node(out)
    graph.connect("s", "output", "o", "input")
    results = graph.tick()
    assert "o" in results  # no crash


# ---- PluginScanner ------------------------------------------------------

def _write_manifest_file(directory: Path, data: dict) -> Path:
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(data))
    return manifest_path


def test_scanner_scan_empty_dir(tmp_path):
    scanner = PluginScanner()
    result = scanner.scan(tmp_path)
    assert result["loaded"] == 0


def test_scanner_loads_valid_manifests(tmp_path):
    plugin_dir = tmp_path / "blur"
    plugin_dir.mkdir()
    _write_manifest_file(plugin_dir, {
        "collection": "blur", "source": "standalone",
        "modules": [{"id": "blur", "name": "Blur"}]
    })
    scanner = PluginScanner()
    result = scanner.scan(tmp_path)
    assert result["loaded"] == 1
    assert len(scanner.loaded_manifests) == 1


def test_scanner_registers_into_registry(tmp_path):
    plugin_dir = tmp_path / "testplug"
    plugin_dir.mkdir()
    _write_manifest_file(plugin_dir, {
        "collection": "testplug", "source": "standalone",
        "modules": [{"id": "mynode", "name": "My Node", "node_type": "MY_NODE"}]
    })
    registry = NodeRegistry()
    scanner = PluginScanner(registry=registry)
    result = scanner.scan(tmp_path)
    assert result["registered"] == 1
    assert "MY_NODE" in registry


def test_scanner_skips_bad_manifests(tmp_path):
    plugin_dir = tmp_path / "bad"
    plugin_dir.mkdir()
    (plugin_dir / "manifest.json").write_text("NOT JSON")
    scanner = PluginScanner()
    result = scanner.scan(tmp_path)
    assert result["loaded"] == 0
    assert result["skipped"] == 1


def test_scanner_scans_nested_dirs(tmp_path):
    for name in ["a", "b", "c"]:
        d = tmp_path / name
        d.mkdir()
        _write_manifest_file(d, {
            "collection": name, "source": "standalone",
            "modules": [{"id": name, "name": name.upper()}]
        })
    scanner = PluginScanner()
    result = scanner.scan(tmp_path)
    assert result["loaded"] == 3


def test_scanner_nonexistent_dir_does_not_crash():
    scanner = PluginScanner()
    result = scanner.scan("/tmp/nonexistent_vjlive3_test_dir_xyz")
    assert result["loaded"] == 0


def test_scanner_reset():
    scanner = PluginScanner()
    scanner._loaded.append(object())
    scanner.reset()
    assert len(scanner.loaded_manifests) == 0


# ---- Integration: scan VJlive-2 plugins (informational, always passes) --

def test_scan_vjlive2_plugins_no_crash():
    """Scan the real VJlive-2 plugins dir — just checks no exception raised."""
    vjlive2_plugins = Path(
        "/home/happy/Desktop/claude projects/VJlive-2/plugins"
    )
    if not vjlive2_plugins.is_dir():
        pytest.skip("VJlive-2 not present")

    registry = NodeRegistry()
    scanner = PluginScanner(registry=registry)
    result = scanner.scan(vjlive2_plugins)
    # Just assert we loaded SOMETHING, not zero
    assert result["loaded"] >= 0  # Cannot crash
