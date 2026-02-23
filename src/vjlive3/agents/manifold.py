"""Manifold16D — 16-dimensional toroidal phase space for agent traversal."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import numpy as np

DIMS = 16


@dataclass
class GravityWell:
    """
    A point attractor in 16D manifold space.

    Agents are pulled toward the well's centre with a force that falls
    off as 1 / (distance^2 + softening^2).
    """
    centre: np.ndarray                  # Shape (DIMS,)
    strength: float = 1.0              # Attraction magnitude
    softening: float = 0.05            # Prevents singularity at r=0
    radius: float = 1.0                # Cut-off (no force beyond this)
    label: str = ""

    def __post_init__(self) -> None:
        self.centre = np.asarray(self.centre, dtype=np.float32).flatten()
        if self.centre.shape[0] < DIMS:
            self.centre = np.pad(self.centre, (0, DIMS - self.centre.shape[0]))
        self.centre = self.centre[:DIMS]

    def force_at(self, position: np.ndarray) -> np.ndarray:
        """Return force vector pointing from *position* toward this well's centre."""
        delta = _toroidal_delta(self.centre, position)   # Shortest path on torus
        dist2 = float(np.dot(delta, delta))
        if dist2 > self.radius ** 2:
            return np.zeros(DIMS, dtype=np.float32)
        effective = dist2 + self.softening ** 2
        magnitude = self.strength / effective
        norm = np.linalg.norm(delta) + 1e-9
        return (delta / norm * magnitude).astype(np.float32)


def _toroidal_delta(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Shortest-path delta on a [0,1)^N torus: each component in (-0.5, 0.5]."""
    d = a - b
    return (d + 0.5) % 1.0 - 0.5


class Manifold16D:
    """
    16-dimensional toroidal phase space.

    Agents live in [0, 1)^16 with periodic boundary conditions.
    Gravity wells can be registered to attract agents.
    """

    def __init__(self) -> None:
        self._wells: List[GravityWell] = []

    # ── Well management ──────────────────────────────────────────────────────

    def add_gravity_well(self, well: GravityWell) -> None:
        """Register a gravity well."""
        self._wells.append(well)

    def remove_gravity_well(self, label: str) -> None:
        """Remove all wells with the given label."""
        self._wells = [w for w in self._wells if w.label != label]

    def clear_wells(self) -> None:
        self._wells.clear()

    @property
    def wells(self) -> List[GravityWell]:
        return list(self._wells)

    # ── Geometry ──────────────────────────────────────────────────────────────

    @staticmethod
    def distance(a: np.ndarray, b: np.ndarray) -> float:
        """Euclidean distance on the torus (shortest path)."""
        return float(np.linalg.norm(_toroidal_delta(a, b)))

    @staticmethod
    def project_to_screen(position: np.ndarray) -> tuple[float, float]:
        """
        Project a 16D manifold position to [0,1)^2 screen coordinates.

        First two dimensions form the primary axes; dims 2-7 add a small
        modulation to create richer, non-repeating trajectories.
        """
        pos = np.asarray(position, dtype=np.float32)
        x = float(pos[0])
        y = float(pos[1])
        for d in range(2, min(8, DIMS)):
            scale = 0.04 / d
            if d % 2 == 0:
                x = float(np.mod(x + pos[d] * scale, 1.0))
            else:
                y = float(np.mod(y + pos[d] * scale, 1.0))
        return x, y

    # ── Physics helper ────────────────────────────────────────────────────────

    def total_gravity_force(self, position: np.ndarray) -> np.ndarray:
        """Sum force contributions from all registered gravity wells."""
        if not self._wells:
            return np.zeros(DIMS, dtype=np.float32)
        forces = [w.force_at(position) for w in self._wells]
        return np.sum(forces, axis=0).astype(np.float32)

    @staticmethod
    def wrap(position: np.ndarray) -> np.ndarray:
        """Apply toroidal wrapping to keep position in [0, 1)^16."""
        return np.mod(position, 1.0).astype(np.float32)
