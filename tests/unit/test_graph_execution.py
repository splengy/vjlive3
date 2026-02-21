"""Tests for NodeGraph execution, connections, and topo sort."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import json
import tempfile
import pytest

from vjlive3.graph.node import Node, Parameter
from vjlive3.graph.signal import Port, SignalType
from vjlive3.graph.graph import NodeGraph, GraphCycleError, PortTypeMismatchError
from vjlive3.graph.registry import NodeRegistry
from vjlive3.graph.persistence import save_graph, load_graph


# ---- Helpers / test nodes -----------------------------------------------

class _ConstNode(Node):
    """Outputs a constant value."""
    node_type = "CONST"
    _input_ports  = []
    _output_ports = [Port("out", SignalType.MODULATION)]
    _parameters   = [Parameter("value", 1.0, 0.0, 10.0)]

    def process(self, inputs, dt):
        return {"out": self._params["value"].value}


class _AddNode(Node):
    """Adds two modulation inputs."""
    node_type = "ADD"
    _input_ports  = [Port("a", SignalType.MODULATION), Port("b", SignalType.MODULATION)]
    _output_ports = [Port("sum", SignalType.MODULATION)]
    _parameters   = []

    def process(self, inputs, dt):
        a = inputs.get("a", 0.0)
        b = inputs.get("b", 0.0)
        return {"sum": a + b}


class _VideoNode(Node):
    node_type = "VIDEO"
    _input_ports  = []
    _output_ports = [Port("frame", SignalType.VIDEO)]
    _parameters   = []

    def process(self, inputs, dt):
        return {"frame": "FRAME_DATA"}


# ---- Connection ---------------------------------------------------------

def test_connect_and_tick():
    g = NodeGraph()
    c1 = _ConstNode(node_id="c1")
    c1.set_parameter("value", 3.0)
    c2 = _ConstNode(node_id="c2")
    c2.set_parameter("value", 4.0)
    adder = _AddNode(node_id="add")
    g.add_node(c1).add_node(c2).add_node(adder)
    g.connect("c1", "out", "add", "a")
    g.connect("c2", "out", "add", "b")
    results = g.tick(dt=0.016)
    assert results["add"]["sum"] == pytest.approx(7.0)


def test_connect_unknown_node_raises():
    g = NodeGraph()
    g.add_node(_ConstNode(node_id="c1"))
    with pytest.raises(KeyError):
        g.connect("c1", "out", "nonexistent", "a")


def test_connect_unknown_port_raises():
    g = NodeGraph()
    g.add_node(_ConstNode(node_id="c1"))
    g.add_node(_AddNode(node_id="add"))
    with pytest.raises(AttributeError):
        g.connect("c1", "NO_SUCH_PORT", "add", "a")


def test_port_type_mismatch_raises():
    g = NodeGraph()
    g.add_node(_VideoNode(node_id="vid"))
    g.add_node(_AddNode(node_id="add"))
    with pytest.raises(PortTypeMismatchError):
        g.connect("vid", "frame", "add", "a")  # VIDEO → MODULATION


def test_cycle_detection():
    g = NodeGraph()
    n1 = _AddNode(node_id="n1")
    n2 = _AddNode(node_id="n2")
    g.add_node(n1).add_node(n2)
    g.connect("n1", "sum", "n2", "a")
    with pytest.raises(GraphCycleError):
        g.connect("n2", "sum", "n1", "b")  # would form cycle


def test_disconnect():
    g = NodeGraph()
    c1 = _ConstNode(node_id="c1")
    add = _AddNode(node_id="add")
    g.add_node(c1).add_node(add)
    edge_id = g.connect("c1", "out", "add", "a")
    assert g.edge_count() == 1
    g.disconnect(edge_id)
    assert g.edge_count() == 0


# ---- Parameter control --------------------------------------------------

def test_set_param_dot_path():
    g = NodeGraph()
    c = _ConstNode(node_id="const")
    g.add_node(c)
    ok = g.set_param("const.value", 7.0)
    assert ok is True
    assert c.get_parameter("value").value == pytest.approx(7.0)


def test_set_param_unknown_node():
    g = NodeGraph()
    assert g.set_param("no_node.value", 5.0) is False


def test_set_param_triggers_listener():
    received = []
    g = NodeGraph()
    g.add_node(_ConstNode(node_id="c"))
    g.add_listener(lambda path, val: received.append((path, val)))
    g.set_param("c.value", 3.0)
    assert received == [("c.value", 3.0)]


# ---- Disabled node skipped ----------------------------------------------

def test_disabled_node_outputs_nothing():
    g = NodeGraph()
    c = _ConstNode(node_id="c")
    c.set_parameter("value", 5.0)
    add = _AddNode(node_id="add")
    g.add_node(c).add_node(add)
    g.connect("c", "out", "add", "a")
    c.disable()
    results = g.tick()
    assert results["add"]["sum"] == pytest.approx(0.0)


# ---- Graph state --------------------------------------------------------

def test_add_duplicate_node_raises():
    g = NodeGraph()
    n = _ConstNode(node_id="dup")
    g.add_node(n)
    with pytest.raises(ValueError):
        g.add_node(n)


def test_remove_node_cleans_edges():
    g = NodeGraph()
    c = _ConstNode(node_id="c")
    add = _AddNode(node_id="add")
    g.add_node(c).add_node(add)
    g.connect("c", "out", "add", "a")
    assert g.edge_count() == 1
    g.remove_node("c")
    assert g.edge_count() == 0


# ---- Persistence --------------------------------------------------------

def _make_registry():
    r = NodeRegistry()
    r.register("CONST", _ConstNode)
    r.register("ADD", _AddNode)
    return r


def test_save_and_load_round_trip():
    g = NodeGraph()
    c = _ConstNode(node_id="c")
    c.set_parameter("value", 9.0)
    add = _AddNode(node_id="add")
    g.add_node(c).add_node(add)
    g.connect("c", "out", "add", "a")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        path = tmp.name

    save_graph(g, path)
    g2 = load_graph(path, _make_registry())

    assert g2.node_count() == 2
    assert g2.edge_count() == 1
    assert g2.get_node("c").get_parameter("value").value == pytest.approx(9.0)


def test_load_unknown_type_skips_gracefully():
    raw = {
        "vjlive3_graph_version": 1,
        "nodes": [{"id": "x", "node_type": "UNKNOWN_TYPE", "name": "x"}],
        "edges": [],
    }
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(raw, f)
        path = f.name

    g = load_graph(path, _make_registry())
    assert g.node_count() == 0  # unknown type silently skipped
