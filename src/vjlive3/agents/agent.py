"""Agent dataclass — core identity and state for a VJLive3 agent."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import numpy as np
import uuid


class AgentState(Enum):
    """Lifecycle states for an Agent."""
    DORMANT = auto()    # Awaiting energy threshold
    ACTIVE = auto()     # Fully operating
    DECAYING = auto()   # Energy low, fading out
    DEAD = auto()       # Ready for garbage collection


DIMS = 16  # Manifold dimensionality


@dataclass
class Agent:
    """
    A single autonomous agent inhabiting the 16-dimensional manifold.

    Position is a unit-normalised float32 vector in [0, 1)^16 (toroidal).
    Velocity is in manifold units per second.
    Energy is in [0.0, 1.0]; drops via decay, boosted by audio impulses.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    position: np.ndarray = field(
        default_factory=lambda: np.random.rand(DIMS).astype(np.float32)
    )
    velocity: np.ndarray = field(
        default_factory=lambda: np.zeros(DIMS, dtype=np.float32)
    )
    energy: float = 1.0
    age: float = 0.0   # Seconds since spawn
    state: AgentState = AgentState.ACTIVE

    # Tunable constants
    energy_decay: float = 0.01   # Per second
    energy_threshold_active: float = 0.1
    max_speed: float = 0.5       # Manifold units/s

    def __post_init__(self) -> None:
        # Ensure numpy arrays are correct dtype/shape on init
        self.position = np.asarray(self.position, dtype=np.float32).flatten()[:DIMS]
        if self.position.shape[0] < DIMS:
            pad = np.random.rand(DIMS - self.position.shape[0]).astype(np.float32)
            self.position = np.concatenate([self.position, pad])
        self.velocity = np.asarray(self.velocity, dtype=np.float32).flatten()[:DIMS]
        if self.velocity.shape[0] < DIMS:
            self.velocity = np.pad(self.velocity, (0, DIMS - self.velocity.shape[0]))

    def apply_impulse(self, force: np.ndarray) -> None:
        """Add an impulse force to velocity (audio kick, gravity)."""
        self.velocity = np.clip(
            self.velocity + force.astype(np.float32),
            -self.max_speed,
            self.max_speed,
        )

    def tick(self, dt: float) -> None:
        """
        Advance agent by *dt* seconds.

        Integrates position, applies energy decay, updates state.
        Does NOT apply forces — that is done by AgentPhysics.
        """
        self.position = np.mod(self.position + self.velocity * dt, 1.0).astype(np.float32)
        self.energy = max(0.0, self.energy - self.energy_decay * dt)
        self.age += dt
        self._update_state()

    def _update_state(self) -> None:
        if self.energy <= 0.0:
            self.state = AgentState.DEAD
        elif self.energy < self.energy_threshold_active:
            self.state = AgentState.DECAYING
        else:
            self.state = AgentState.ACTIVE

    def is_alive(self) -> bool:
        return self.state != AgentState.DEAD

    def screen_xy(self) -> tuple[float, float]:
        """
        Project the 16D position to a 2D screen coordinate in [0, 1)^2.

        Uses the first two dimensions directly; higher dimensions modulate them.
        """
        x = float(self.position[0])
        y = float(self.position[1])
        # Modulate with dims 2-7 for richer motion
        for d in range(2, min(8, DIMS)):
            scale = 0.05 / (d - 1)
            if d % 2 == 0:
                x = np.mod(x + self.position[d] * scale, 1.0)
            else:
                y = np.mod(y + self.position[d] * scale, 1.0)
        return float(x), float(y)

    def to_param_influence(self, num_params: int = 8) -> np.ndarray:
        """
        Map position to a parameter influence vector of length *num_params*.

        Values in [0.0, 1.0], suitable for blending with plugin params.
        """
        # Use first num_params dimensions, wrap if needed
        indices = np.arange(num_params) % DIMS
        return self.position[indices].copy()
