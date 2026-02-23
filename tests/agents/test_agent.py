"""Tests for vjlive3.agents.agent — Agent dataclass."""
import pytest
import numpy as np
from vjlive3.agents.agent import Agent, AgentState, DIMS


def test_default_agent_shape():
    a = Agent()
    assert a.position.shape == (DIMS,)
    assert a.velocity.shape == (DIMS,)
    assert a.state == AgentState.ACTIVE


def test_agent_position_range():
    a = Agent()
    # Random init should be in [0,1)
    assert np.all(a.position >= 0.0)
    assert np.all(a.position < 1.0)


def test_apply_impulse_clamps_to_max_speed():
    a = Agent(max_speed=0.5)
    big = np.ones(DIMS, dtype=np.float32) * 100.0
    a.apply_impulse(big)
    assert np.all(np.abs(a.velocity) <= 0.5 + 1e-6)


def test_tick_advances_position():
    a = Agent(position=np.zeros(DIMS, dtype=np.float32),
              velocity=np.ones(DIMS, dtype=np.float32) * 0.1)
    a.tick(1.0)
    assert np.allclose(a.position, (0.0 + 0.1) % 1.0, atol=1e-5)


def test_tick_decays_energy():
    a = Agent(energy=1.0, energy_decay=0.5)
    a.tick(1.0)
    assert a.energy == pytest.approx(0.5, abs=1e-5)


def test_state_transitions_to_dead():
    a = Agent(energy=0.001, energy_decay=1.0)
    a.tick(1.0)
    assert a.state == AgentState.DEAD
    assert not a.is_alive()


def test_state_transitions_to_decaying():
    a = Agent(energy=0.05, energy_decay=0.0, energy_threshold_active=0.1)
    a._update_state()
    assert a.state == AgentState.DECAYING


def test_screen_xy_in_unit_square():
    for _ in range(20):
        a = Agent()
        x, y = a.screen_xy()
        assert 0.0 <= x < 1.0, f"x={x} out of range"
        assert 0.0 <= y < 1.0, f"y={y} out of range"


def test_toroidal_wrap_on_tick():
    a = Agent(position=np.full(DIMS, 0.95, dtype=np.float32),
              velocity=np.full(DIMS, 0.2, dtype=np.float32))
    a.tick(1.0)
    assert np.all(a.position < 1.0)
    assert np.all(a.position >= 0.0)


def test_to_param_influence_shape():
    a = Agent()
    params = a.to_param_influence(8)
    assert params.shape == (8,)
    assert np.all(params >= 0.0)
    assert np.all(params <= 1.0)


def test_to_param_influence_more_than_dims():
    a = Agent()
    params = a.to_param_influence(20)  # Should wrap modulo DIMS
    assert params.shape == (20,)
