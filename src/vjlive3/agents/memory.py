"""AgentMemory — 50-snapshot ring buffer per agent."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np

SNAPSHOT_CAPACITY = 50
DIMS = 16


@dataclass
class Snapshot:
    """A single moment in an agent's history."""
    position: np.ndarray       # shape (DIMS,) float32
    velocity: np.ndarray       # shape (DIMS,) float32
    energy: float
    timestamp: float           # Agent age at capture (seconds)
    context_hash: int = 0      # Hash of plugin context at this frame

    def __post_init__(self) -> None:
        self.position = np.asarray(self.position, dtype=np.float32)
        self.velocity = np.asarray(self.velocity, dtype=np.float32)
        self.energy = float(self.energy)
        self.timestamp = float(self.timestamp)

    def distance_to(self, other: "Snapshot") -> float:
        """Manifold-space Euclidean distance between two snapshots."""
        d = (self.position - other.position + 0.5) % 1.0 - 0.5
        return float(np.linalg.norm(d))


class AgentMemory:
    """
    50-snapshot ring buffer for a single agent.

    Supports push, indexed recall, trajectory replay, and pair diff.
    """

    def __init__(self, capacity: int = SNAPSHOT_CAPACITY) -> None:
        self._capacity = max(1, int(capacity))
        self._buffer: List[Snapshot] = []
        self._head: int = 0        # Index of oldest entry (ring pointer)

    # ── Write ─────────────────────────────────────────────────────────────────

    def push(self, snapshot: Snapshot) -> None:
        """Add a snapshot, evicting the oldest if at capacity."""
        if len(self._buffer) < self._capacity:
            self._buffer.append(snapshot)
        else:
            self._buffer[self._head] = snapshot
            self._head = (self._head + 1) % self._capacity

    def push_from_agent(self, agent, context_hash: int = 0) -> None:
        """Convenience: capture a Snapshot from an Agent object."""
        snap = Snapshot(
            position=agent.position.copy(),
            velocity=agent.velocity.copy(),
            energy=agent.energy,
            timestamp=agent.age,
            context_hash=context_hash,
        )
        self.push(snap)

    # ── Read ──────────────────────────────────────────────────────────────────

    def recall(self, n: int = 1) -> Optional[Snapshot]:
        """Return the *n*-th most recent snapshot (1 = latest)."""
        if not self._buffer:
            return None
        ordered = self._ordered()
        idx = max(0, len(ordered) - n)
        return ordered[idx]

    def replay(self) -> List[Snapshot]:
        """Return all snapshots in chronological order (oldest first)."""
        return self._ordered()

    def diff(self, n: int = 1) -> Optional[np.ndarray]:
        """
        Return the position displacement between snapshot *n* and *n+1*.

        Useful for trajectory velocity estimation from stored history.
        Returns None if fewer than *n+1* snapshots exist.
        """
        ordered = self._ordered()
        if len(ordered) < n + 1:
            return None
        newer = ordered[-(1)]
        older = ordered[-(n + 1)]
        return (newer.position - older.position).astype(np.float32)

    def trajectory_positions(self) -> np.ndarray:
        """Return an (N, DIMS) array of all stored positions in order."""
        ordered = self._ordered()
        if not ordered:
            return np.empty((0, DIMS), dtype=np.float32)
        return np.stack([s.position for s in ordered])

    # ── Meta ──────────────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._buffer)

    def is_full(self) -> bool:
        return len(self._buffer) == self._capacity

    def clear(self) -> None:
        self._buffer.clear()
        self._head = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    # ── Internal ──────────────────────────────────────────────────────────────

    def _ordered(self) -> List[Snapshot]:
        """Return buffer in chronological order."""
        if len(self._buffer) < self._capacity:
            return list(self._buffer)
        return self._buffer[self._head:] + self._buffer[: self._head]
