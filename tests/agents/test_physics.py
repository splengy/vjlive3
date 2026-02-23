"""Tests for vjlive3.agents.physics — AgentPhysics."""
import pytest
import numpy as np
from unittest.mock import MagicMock
from vjlive3.agents.agent import Agent, AgentState, DIMS
from vjlive3.agents.manifold import Manifold16D, GravityWell
from vjlive3.agents.physics import AgentPhysics


@pytest.fixture
def manifold():
    return Manifold16D()


@pytest.fixture
def physics(manifold):
    return AgentPhysics(manifold, damping=0.9, bass_impulse_scale=0.2)


@pytest.fixture
def agent():
    return Agent(
        position=np.full(DIMS, 0.5, dtype=np.float32),
        velocity=np.zeros(DIMS, dtype=np.float32),
        energy=1.0,
    )


def test_step_advances_age(physics, agent):
    physics.step([agent], dt=0.1)
    assert agent.age == pytest.approx(0.1, abs=1e-5)


def test_step_zero_dt_no_change(physics, agent):
    orig_pos = agent.position.copy()
    physics.step([agent], dt=0.0)
    assert np.allclose(agent.position, orig_pos)


def test_step_skips_dead_agents(physics):
    dead = Agent(energy=0.0)
    dead.state = AgentState.DEAD
    orig_pos = dead.position.copy()
    physics.step([dead], dt=0.1)
    assert np.allclose(dead.position, orig_pos)


def test_bass_impulse_changes_velocity(physics, agent):
    v_before = agent.velocity.copy()
    physics.step([agent], dt=1 / 60, audio={"bass": 1.0, "beat": 0.0, "mid": 0.0, "treble": 0.0})
    assert not np.allclose(agent.velocity, v_before), "Bass impulse should change velocity"


def test_damping_reduces_velocity(physics):
    a = Agent(velocity=np.ones(DIMS, dtype=np.float32) * 0.5)
    physics.step([a], dt=1.0, audio={})
    speed = np.linalg.norm(a.velocity)
    assert speed < np.sqrt(DIMS) * 0.5, "Damping should reduce speed"


def test_gravity_well_attracts_agent(manifold, physics):
    centre = np.zeros(DIMS, dtype=np.float32)
    pos = np.full(DIMS, 0.9, dtype=np.float32)
    manifold.add_gravity_well(GravityWell(centre=centre, strength=5.0, radius=5.0))
    a = Agent(position=pos.copy(), velocity=np.zeros(DIMS, dtype=np.float32))
    physics.step([a], dt=0.5, audio={})
    # Velocity should have a component toward the well
    assert np.linalg.norm(a.velocity) > 0.0


def test_spawn_creates_agent():
    a = AgentPhysics.spawn(energy=0.7)
    assert a.energy == pytest.approx(0.7, abs=1e-5)
    assert a.position.shape == (DIMS,)


def test_spawn_with_custom_position():
    pos = np.full(DIMS, 0.25, dtype=np.float32)
    a = AgentPhysics.spawn(position=pos)
    assert np.allclose(a.position, pos)


def test_cull_dead_removes_dead():
    alive = Agent(energy=1.0)
    dead = Agent(energy=0.0)
    dead.state = AgentState.DEAD
    result = AgentPhysics.cull_dead([alive, dead])
    assert len(result) == 1
    assert result[0] is alive


def test_position_wraps_on_torus(physics, agent):
    agent.position = np.full(DIMS, 0.99, dtype=np.float32)
    agent.velocity = np.full(DIMS, 0.5, dtype=np.float32)
    physics.step([agent], dt=1.0, audio={})
    assert np.all(agent.position >= 0.0)
    assert np.all(agent.position < 1.0)
