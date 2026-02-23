"""Tests for vjlive3.agents.bridge — AgentBridge."""
import pytest
import numpy as np
from unittest.mock import MagicMock
from vjlive3.agents.bridge import AgentBridge
from vjlive3.agents.agent import AgentState, DIMS
from vjlive3.agents.manifold import GravityWell


def _make_context(audio=None):
    ctx = MagicMock()
    ctx.inputs = {"audio_data": audio or {}}
    ctx.agent_state = {}
    return ctx


# ── Spawn / capacity ──────────────────────────────────────────────────────────

def test_bridge_spawns_agent():
    b = AgentBridge(max_agents=4)
    a = b.spawn_agent(energy=1.0)
    assert a is not None
    assert b.agent_count == 1


def test_bridge_respects_max_agents():
    b = AgentBridge(max_agents=2)
    b.spawn_agent(); b.spawn_agent()
    overflow = b.spawn_agent()
    assert overflow is None
    assert b.agent_count == 2


def test_bridge_step_advances_agents():
    b = AgentBridge(auto_spawn=False)
    b.spawn_agent(energy=1.0)
    ctx = _make_context()
    b.step(ctx, dt=1 / 60)
    # Agent age should advance
    assert b.agents[0].age > 0.0


def test_bridge_step_zero_dt():
    b = AgentBridge(auto_spawn=False)
    b.spawn_agent(energy=1.0)
    ctx = _make_context()
    b.step(ctx, dt=0.0)
    assert b.agents[0].age == pytest.approx(0.0, abs=1e-6)


# ── Auto-spawn ────────────────────────────────────────────────────────────────

def test_auto_spawn_on_bass():
    b = AgentBridge(max_agents=4, auto_spawn=True)
    ctx = _make_context(audio={"bass": 0.9, "beat": 0.0, "mid": 0.0, "treble": 0.0})
    b.step(ctx, dt=1 / 60)
    assert b.agent_count >= 1


def test_no_auto_spawn_when_disabled():
    b = AgentBridge(max_agents=4, auto_spawn=False)
    ctx = _make_context(audio={"bass": 1.0, "beat": 1.0})
    b.step(ctx, dt=1 / 60)
    assert b.agent_count == 0


# ── Context publishing ────────────────────────────────────────────────────────

def test_step_publishes_agent_state():
    b = AgentBridge(auto_spawn=False)
    b.spawn_agent(energy=1.0)
    ctx = _make_context()
    b.step(ctx, dt=1 / 60)
    state = ctx.agent_state
    assert "agents" in state
    assert "screen_positions" in state
    assert "param_influences" in state
    assert "agent_count" in state


def test_screen_positions_in_unit_square():
    b = AgentBridge(auto_spawn=False)
    for _ in range(3):
        b.spawn_agent(energy=1.0)
    ctx = _make_context()
    b.step(ctx, dt=1 / 60)
    for x, y in ctx.agent_state["screen_positions"]:
        assert 0.0 <= x < 1.0
        assert 0.0 <= y < 1.0


def test_param_influences_shape():
    b = AgentBridge(auto_spawn=False)
    n = 3
    for _ in range(n):
        b.spawn_agent(energy=1.0)
    ctx = _make_context()
    b.step(ctx, dt=1 / 60)
    pi = ctx.agent_state["param_influences"]
    # to_param_influence() defaults to 8 elements
    assert pi.shape[0] == n
    assert pi.shape[1] > 0


def test_empty_agents_param_influences_shape():
    b = AgentBridge(auto_spawn=False)
    ctx = _make_context()
    b.step(ctx, dt=1 / 60)
    pi = ctx.agent_state["param_influences"]
    assert pi.shape == (0, DIMS)


# ── Memory ────────────────────────────────────────────────────────────────────

def test_bridge_memory_created_for_agent():
    b = AgentBridge(auto_spawn=False, snapshot_interval=0.0)
    a = b.spawn_agent(energy=1.0)
    ctx = _make_context()
    b.step(ctx, dt=1 / 60)
    mem = b.get_memory(a.id)
    assert mem is not None
    assert len(mem) >= 1


def test_bridge_memory_none_for_unknown_id():
    b = AgentBridge(auto_spawn=False)
    assert b.get_memory("no-such-id") is None


# ── Gravity wells ─────────────────────────────────────────────────────────────

def test_bridge_add_remove_well():
    b = AgentBridge()
    b.add_gravity_well(GravityWell(centre=np.zeros(DIMS), label="w1"))
    assert len(b.manifold.wells) == 1
    b.remove_gravity_well("w1")
    assert len(b.manifold.wells) == 0


def test_bridge_clear_wells():
    b = AgentBridge()
    for i in range(3):
        b.add_gravity_well(GravityWell(centre=np.zeros(DIMS), label=str(i)))
    b.clear_wells()
    assert len(b.manifold.wells) == 0


# ── Coverage gap tests (bridge.py lines 120-144, 172-173, 178-181) ────────────

def test_auto_spawn_does_not_exceed_max_when_full():
    b = AgentBridge(max_agents=1, auto_spawn=True)
    b.spawn_agent(energy=1.0)
    ctx = _make_context(audio={"bass": 1.0, "beat": 0.0, "mid": 0.0, "treble": 0.0})
    b.step(ctx, dt=1 / 60)
    assert b.agent_count == 1


def test_cull_removes_dead_agents_after_interval():
    from vjlive3.agents.bridge import _CULL_INTERVAL
    b = AgentBridge(auto_spawn=False)
    b.spawn_agent(energy=0.001)
    ctx = _make_context()
    b.step(ctx, dt=_CULL_INTERVAL + 0.5)
    alive = [ag for ag in b.agents if ag.is_alive()]
    assert len(alive) == b.agent_count


def test_memory_snapshot_captures_multiple_agents():
    b = AgentBridge(auto_spawn=False, snapshot_interval=0.0)
    a1 = b.spawn_agent(energy=1.0)
    a2 = b.spawn_agent(energy=1.0)
    ctx = _make_context()
    b.step(ctx, dt=1 / 60)
    for agent in [a1, a2]:
        mem = b.get_memory(agent.id)
        assert mem is not None and len(mem) >= 1


def test_extract_audio_handles_exception():
    b = AgentBridge(auto_spawn=False)
    ctx = MagicMock()
    ctx.inputs.get.side_effect = RuntimeError("broken")
    audio = b._extract_audio(ctx)
    assert audio == {}


def test_publish_context_without_agent_state_attr():
    b = AgentBridge(auto_spawn=False)
    b.spawn_agent(energy=1.0)
    class MinimalCtx:
        inputs = {"audio_data": {}}
    ctx = MinimalCtx()
    b.step(ctx, dt=1 / 60)
    assert hasattr(ctx, "agent_state")
    assert "agents" in ctx.agent_state

