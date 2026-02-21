"""Tests for Node, Parameter, and graph.signal types."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from vjlive3.graph.signal import SignalType, Port
from vjlive3.graph.node import Parameter, Node


# ---- Test helpers -------------------------------------------------------

class _PassthroughNode(Node):
    """Concrete test node that passes input to output."""
    node_type = "PASSTHROUGH"
    _input_ports  = [Port("in",  SignalType.ANY, "Input")]
    _output_ports = [Port("out", SignalType.ANY, "Output")]
    _parameters   = [Parameter("gain", 1.0, 0.0, 4.0, "Gain")]

    def process(self, inputs, dt):
        val = inputs.get("in", 0.0)
        return {"out": val * self._params["gain"].value}


# ---- SignalType ---------------------------------------------------------

def test_signal_type_compatible_same():
    assert SignalType.VIDEO.compatible_with(SignalType.VIDEO)

def test_signal_type_incompatible():
    assert not SignalType.VIDEO.compatible_with(SignalType.AUDIO)

def test_signal_type_any_matches_all():
    for t in SignalType:
        assert SignalType.ANY.compatible_with(t)
        assert t.compatible_with(SignalType.ANY)


# ---- Parameter ----------------------------------------------------------

def test_parameter_set_clamps_min():
    p = Parameter("x", 5.0, 0.0, 10.0)
    p.set(-99.0)
    assert p.value == 0.0

def test_parameter_set_clamps_max():
    p = Parameter("x", 5.0, 0.0, 10.0)
    p.set(999.0)
    assert p.value == 10.0

def test_parameter_to_signal_midpoint():
    p = Parameter("x", 5.0, 0.0, 10.0)
    assert p.to_signal() == pytest.approx(5.0)

def test_parameter_from_signal_round_trip():
    p = Parameter("x", 5.0, 0.0, 10.0)
    p.from_signal(7.5)
    assert p.value == pytest.approx(7.5)

def test_parameter_to_signal_zero_span():
    p = Parameter("x", 1.0, 1.0, 1.0)
    assert p.to_signal() == 0.0


# ---- Node ---------------------------------------------------------------

def test_node_id_auto_generated():
    n = _PassthroughNode()
    assert len(n.id) == 36  # UUID4 format

def test_node_explicit_id():
    n = _PassthroughNode(node_id="test-123")
    assert n.id == "test-123"

def test_node_parameter_independence():
    n1 = _PassthroughNode()
    n2 = _PassthroughNode()
    n1.set_parameter("gain", 2.0)
    assert n2.get_parameter("gain").value == 1.0  # default unchanged

def test_node_set_unknown_param_returns_false():
    n = _PassthroughNode()
    assert n.set_parameter("no_such_param", 5.0) is False

def test_node_process():
    n = _PassthroughNode()
    result = n.process({"in": 3.0}, dt=0.016)
    assert result["out"] == pytest.approx(3.0)

def test_node_process_with_gain():
    n = _PassthroughNode()
    n.set_parameter("gain", 2.0)
    result = n.process({"in": 3.0}, dt=0.016)
    assert result["out"] == pytest.approx(6.0)

def test_node_state_round_trip():
    n = _PassthroughNode(node_id="abc", name="MyNode")
    n.set_parameter("gain", 3.0)
    state = n.get_state()
    n2 = _PassthroughNode(node_id="abc", name="MyNode")
    n2.set_state(state)
    assert n2.get_parameter("gain").value == pytest.approx(3.0)
