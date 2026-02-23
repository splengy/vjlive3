"""Tests for vjlive3.agents.memory — AgentMemory and Snapshot."""
import pytest
import numpy as np
from vjlive3.agents.agent import Agent, DIMS
from vjlive3.agents.memory import AgentMemory, Snapshot, SNAPSHOT_CAPACITY


def _make_snap(ts=0.0, energy=1.0) -> Snapshot:
    return Snapshot(
        position=np.random.rand(DIMS).astype(np.float32),
        velocity=np.zeros(DIMS, dtype=np.float32),
        energy=energy,
        timestamp=ts,
    )


# ── Snapshot tests ───────────────────────────────────────────────────────────

def test_snapshot_distance_same_position():
    s = _make_snap()
    assert s.distance_to(s) == pytest.approx(0.0, abs=1e-5)


def test_snapshot_distance_symmetric():
    a = _make_snap(); b = _make_snap()
    assert a.distance_to(b) == pytest.approx(b.distance_to(a), abs=1e-5)


# ── AgentMemory tests ─────────────────────────────────────────────────────────

def test_memory_empty_on_init():
    m = AgentMemory()
    assert len(m) == 0
    assert m.recall() is None


def test_memory_push_and_len():
    m = AgentMemory(capacity=5)
    for i in range(3):
        m.push(_make_snap(ts=float(i)))
    assert len(m) == 3


def test_memory_is_full_at_capacity():
    m = AgentMemory(capacity=3)
    for _ in range(3):
        m.push(_make_snap())
    assert m.is_full()


def test_memory_ring_buffer_evicts_oldest():
    m = AgentMemory(capacity=3)
    for i in range(5):
        m.push(_make_snap(ts=float(i)))
    # Should only hold 3 snapshots
    assert len(m) == 3
    # Most recent should be ts=4
    latest = m.recall(1)
    assert latest.timestamp == pytest.approx(4.0, abs=1e-5)


def test_memory_recall_nth():
    m = AgentMemory(capacity=10)
    for i in range(5):
        m.push(_make_snap(ts=float(i)))
    assert m.recall(1).timestamp == pytest.approx(4.0, abs=1e-5)
    assert m.recall(2).timestamp == pytest.approx(3.0, abs=1e-5)
    assert m.recall(5).timestamp == pytest.approx(0.0, abs=1e-5)


def test_memory_replay_chronological():
    m = AgentMemory(capacity=10)
    for i in range(5):
        m.push(_make_snap(ts=float(i)))
    replay = m.replay()
    timestamps = [s.timestamp for s in replay]
    assert timestamps == sorted(timestamps)


def test_memory_diff_returns_displacement():
    m = AgentMemory(capacity=10)
    s1 = Snapshot(position=np.zeros(DIMS, dtype=np.float32),
                  velocity=np.zeros(DIMS, dtype=np.float32), energy=1.0, timestamp=0.0)
    s2 = Snapshot(position=np.ones(DIMS, dtype=np.float32) * 0.1,
                  velocity=np.zeros(DIMS, dtype=np.float32), energy=1.0, timestamp=1.0)
    m.push(s1); m.push(s2)
    diff = m.diff(1)
    assert diff is not None
    assert diff.shape == (DIMS,)


def test_memory_diff_returns_none_when_insufficient():
    m = AgentMemory(capacity=10)
    m.push(_make_snap())
    assert m.diff(5) is None


def test_memory_push_from_agent():
    m = AgentMemory(capacity=10)
    a = Agent()
    m.push_from_agent(a, context_hash=42)
    assert len(m) == 1
    s = m.recall(1)
    assert s.context_hash == 42
    assert np.allclose(s.position, a.position)


def test_memory_trajectory_positions_shape():
    m = AgentMemory(capacity=10)
    for _ in range(4):
        m.push(_make_snap())
    traj = m.trajectory_positions()
    assert traj.shape == (4, DIMS)


def test_memory_clear():
    m = AgentMemory(capacity=5)
    for _ in range(3):
        m.push(_make_snap())
    m.clear()
    assert len(m) == 0
    assert m.recall() is None


def test_memory_default_capacity_is_50():
    m = AgentMemory()
    assert m.capacity == SNAPSHOT_CAPACITY
