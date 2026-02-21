"""Tests for NodeRegistry."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from vjlive3.graph.registry import NodeRegistry
from vjlive3.graph.node import Node, Parameter
from vjlive3.graph.signal import Port, SignalType


class _DummyNode(Node):
    node_type = "DUMMY"
    _input_ports  = []
    _output_ports = [Port("out", SignalType.ANY)]
    _parameters   = []

    def process(self, inputs, dt):
        return {"out": 0.0}


def test_register_and_create():
    r = NodeRegistry()
    r.register("DUMMY", _DummyNode)
    n = r.create("DUMMY")
    assert isinstance(n, _DummyNode)
    assert n.node_type == "DUMMY"


def test_register_decorator():
    r = NodeRegistry()

    @r.register("DEC_TEST")
    class _DecNode(Node):
        node_type = "DEC_TEST"
        _input_ports = []
        _output_ports = []
        _parameters = []
        def process(self, inputs, dt):
            return {}

    n = r.create("DEC_TEST")
    assert isinstance(n, _DecNode)


def test_create_with_explicit_id_and_name():
    r = NodeRegistry()
    r.register("DUMMY", _DummyNode)
    n = r.create("DUMMY", node_id="my-id", name="MyDummy")
    assert n.id == "my-id"
    assert n.name == "MyDummy"


def test_unknown_type_raises_key_error():
    r = NodeRegistry()
    with pytest.raises(KeyError, match="no_such_type"):
        r.create("no_such_type")


def test_list_types_sorted():
    r = NodeRegistry()
    r.register("ZZZ", _DummyNode)
    r.register("AAA", _DummyNode)
    types = r.list_types()
    assert types == sorted(types)
    assert "ZZZ" in types and "AAA" in types


def test_contains_operator():
    r = NodeRegistry()
    r.register("DUMMY", _DummyNode)
    assert "DUMMY" in r
    assert "NOPE" not in r


def test_len():
    r = NodeRegistry()
    assert len(r) == 0
    r.register("DUMMY", _DummyNode)
    assert len(r) == 1


def test_non_node_class_raises_type_error():
    r = NodeRegistry()
    with pytest.raises(TypeError):
        r.register("BAD", object)
