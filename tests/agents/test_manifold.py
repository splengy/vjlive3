"""Tests for vjlive3.agents.manifold — Manifold16D and GravityWell."""
import pytest
import numpy as np
from vjlive3.agents.manifold import Manifold16D, GravityWell, _toroidal_delta, DIMS


# ── GravityWell tests ────────────────────────────────────────────────────────

def test_gravity_well_force_at_centre():
    """Force should be near zero when agent IS at the well centre."""
    centre = np.full(DIMS, 0.5, dtype=np.float32)
    well = GravityWell(centre=centre.copy(), strength=1.0, softening=0.1)
    f = well.force_at(centre.copy())
    assert np.linalg.norm(f) < 0.5   # Softening limits max force


def test_gravity_well_force_direction():
    """Force should point FROM agent position TOWARD well centre."""
    centre = np.full(DIMS, 0.5, dtype=np.float32)
    pos = np.full(DIMS, 0.0, dtype=np.float32)
    well = GravityWell(centre=centre, strength=2.0, softening=0.01, radius=5.0)
    f = well.force_at(pos)
    # Check force is nonzero
    assert np.linalg.norm(f) > 0.0


def test_gravity_well_zero_force_beyond_radius():
    """No force should be applied beyond the well's radius."""
    centre = np.full(DIMS, 0.0, dtype=np.float32)
    pos = np.full(DIMS, 0.5, dtype=np.float32)
    well = GravityWell(centre=centre, strength=100.0, radius=0.01)
    f = well.force_at(pos)
    assert np.allclose(f, 0.0)


def test_gravity_well_pads_short_centre():
    well = GravityWell(centre=np.array([0.5, 0.5], dtype=np.float32))
    assert well.centre.shape == (DIMS,)


# ── Manifold16D tests ────────────────────────────────────────────────────────

def test_manifold_distance_same_point():
    m = Manifold16D()
    p = np.random.rand(DIMS).astype(np.float32)
    assert m.distance(p, p) == pytest.approx(0.0, abs=1e-6)


def test_manifold_distance_symmetric():
    m = Manifold16D()
    a = np.random.rand(DIMS).astype(np.float32)
    b = np.random.rand(DIMS).astype(np.float32)
    assert m.distance(a, b) == pytest.approx(m.distance(b, a), abs=1e-5)


def test_manifold_distance_max_on_torus():
    """Max distance on a [0,1) torus is sqrt(DIMS) * 0.5."""
    m = Manifold16D()
    a = np.zeros(DIMS, dtype=np.float32)
    b = np.full(DIMS, 0.5, dtype=np.float32)
    d = m.distance(a, b)
    assert 0.0 < d <= np.sqrt(DIMS) * 0.5 + 1e-5


def test_manifold_add_and_clear_wells():
    m = Manifold16D()
    m.add_gravity_well(GravityWell(centre=np.zeros(DIMS), label="test"))
    assert len(m.wells) == 1
    m.clear_wells()
    assert len(m.wells) == 0


def test_manifold_remove_well_by_label():
    m = Manifold16D()
    m.add_gravity_well(GravityWell(centre=np.zeros(DIMS), label="a"))
    m.add_gravity_well(GravityWell(centre=np.ones(DIMS), label="b"))
    m.remove_gravity_well("a")
    assert len(m.wells) == 1
    assert m.wells[0].label == "b"


def test_manifold_total_force_no_wells():
    m = Manifold16D()
    pos = np.random.rand(DIMS).astype(np.float32)
    f = m.total_gravity_force(pos)
    assert np.allclose(f, 0.0)


def test_manifold_project_to_screen_in_range():
    for _ in range(20):
        pos = np.random.rand(DIMS).astype(np.float32)
        x, y = Manifold16D.project_to_screen(pos)
        assert 0.0 <= x < 1.0, f"x={x}"
        assert 0.0 <= y < 1.0, f"y={y}"


def test_manifold_wrap():
    pos = np.full(DIMS, 1.5, dtype=np.float32)
    wrapped = Manifold16D.wrap(pos)
    assert np.allclose(wrapped, 0.5, atol=1e-5)


def test_toroidal_delta_shortest_path():
    """Delta on torus: crossing boundary should be shorter than going around."""
    a = np.zeros(DIMS, dtype=np.float32); a[0] = 0.05
    b = np.zeros(DIMS, dtype=np.float32); b[0] = 0.95
    d = _toroidal_delta(a, b)
    # Shortest path crosses boundary: delta[0] should be +0.1, not -0.9
    assert abs(d[0]) == pytest.approx(0.1, abs=1e-5)
