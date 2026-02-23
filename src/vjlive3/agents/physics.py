"""AgentPhysics — Euler integrator for agents on the 16D manifold."""
from __future__ import annotations
from typing import List, Optional
import numpy as np

from .agent import Agent, DIMS
from .manifold import Manifold16D


class AgentPhysics:
    """
    Applies forces to agents and advances their state each frame.

    Force sources applied each tick, in order:
    1. Gravity wells from the Manifold
    2. Audio-reactive impulse (bass/beat → shockwave)
    3. Velocity damping
    4. Agent.tick() (position integration + energy decay)
    """

    def __init__(
        self,
        manifold: Manifold16D,
        *,
        damping: float = 0.85,          # Velocity multiplier per second (0=instant stop, 1=no damping)
        bass_impulse_scale: float = 0.3,  # How hard bass kicks push agents
        gravity_scale: float = 1.0,
    ) -> None:
        self.manifold = manifold
        self.damping = float(np.clip(damping, 0.0, 1.0))
        self.bass_impulse_scale = float(bass_impulse_scale)
        self.gravity_scale = float(gravity_scale)

    # ── Main update ───────────────────────────────────────────────────────────

    def step(
        self,
        agents: List[Agent],
        dt: float,
        *,
        audio: Optional[dict] = None,
    ) -> None:
        """
        Advance all *agents* by *dt* seconds.

        *audio* may contain keys: ``bass``, ``mid``, ``treble``, ``beat``
        (all floats in [0.0, 1.0]).
        """
        if dt <= 0:
            return

        bass = float((audio or {}).get("bass", 0.0))
        beat = float((audio or {}).get("beat", 0.0))

        for agent in agents:
            if not agent.is_alive():
                continue

            # 1. Gravity wells
            gravity = self.manifold.total_gravity_force(agent.position)
            agent.apply_impulse(gravity * self.gravity_scale * dt)

            # 2. Bass shockwave — radial impulse from current position
            if bass > 0.05 or beat > 0.5:
                impulse_strength = bass * self.bass_impulse_scale + beat * 0.05
                impulse_dir = self._random_unit_16d()
                agent.apply_impulse(impulse_dir * impulse_strength * dt)

            # 3. Damping (frame-rate-independent)
            damping_factor = self.damping ** dt
            agent.velocity *= damping_factor

            # 4. Integrate position + energy decay
            agent.tick(dt)

    # ── Spawn / cull helpers ──────────────────────────────────────────────────

    @staticmethod
    def spawn(
        energy: float = 1.0,
        position: Optional[np.ndarray] = None,
        velocity: Optional[np.ndarray] = None,
    ) -> Agent:
        """Create and return a new agent at *position* (random if None)."""
        from .agent import Agent
        pos = position if position is not None else np.random.rand(DIMS).astype(np.float32)
        vel = velocity if velocity is not None else np.zeros(DIMS, dtype=np.float32)
        return Agent(position=pos, velocity=vel, energy=float(energy))

    @staticmethod
    def cull_dead(agents: List[Agent]) -> List[Agent]:
        """Return only alive agents."""
        return [a for a in agents if a.is_alive()]

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _random_unit_16d() -> np.ndarray:
        v = np.random.randn(DIMS).astype(np.float32)
        norm = np.linalg.norm(v) + 1e-9
        return (v / norm).astype(np.float32)
