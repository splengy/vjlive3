"""
AgentBridge — P6-AG1 core.

Connects the autonomous agent population to the VJLive3 plugin pipeline.
Each frame it:
  1. Runs AgentPhysics.step() for all agents
  2. Optionally captures AgentMemory snapshots
  3. Writes agent state into context so effect plugins can read it
  4. Handles agent spawn/cull based on audio energy
"""
from __future__ import annotations
from typing import Dict, List, Optional
import logging
import numpy as np

from .agent import Agent, AgentState, DIMS
from .manifold import Manifold16D, GravityWell
from .physics import AgentPhysics
from .memory import AgentMemory

logger = logging.getLogger(__name__)

_DEFAULT_MAX_AGENTS = 8
_SPAWN_ENERGY_THRESHOLD = 0.6   # bass level that triggers a spawn
_CULL_INTERVAL = 2.0            # seconds between cull passes


class AgentBridge:
    """
    Central coordinator between agents and the plugin pipeline.

    Usage
    -----
    bridge = AgentBridge()
    bridge.add_gravity_well(GravityWell(centre=np.array([0.5]*16), strength=0.5))

    # In your render loop:
    bridge.step(context, dt=1/60)

    # Plugins read from context.agent_state:
    #   context.agent_state["agents"]        → list of Agent
    #   context.agent_state["screen_positions"] → list of (x, y)
    #   context.agent_state["param_influences"] → np.ndarray shape (N, DIMS)
    """

    def __init__(
        self,
        max_agents: int = _DEFAULT_MAX_AGENTS,
        *,
        manifold: Optional[Manifold16D] = None,
        memory_capacity: int = 50,
        damping: float = 0.85,
        bass_impulse_scale: float = 0.3,
        gravity_scale: float = 1.0,
        auto_spawn: bool = True,
        snapshot_interval: float = 0.1,  # Seconds between memory captures
    ) -> None:
        self.max_agents = max(1, int(max_agents))
        self.manifold = manifold or Manifold16D()
        self.physics = AgentPhysics(
            self.manifold,
            damping=damping,
            bass_impulse_scale=bass_impulse_scale,
            gravity_scale=gravity_scale,
        )
        self.memory_capacity = int(memory_capacity)
        self.auto_spawn = bool(auto_spawn)
        self.snapshot_interval = float(snapshot_interval)

        self._agents: List[Agent] = []
        self._memories: Dict[str, AgentMemory] = {}  # agent.id → AgentMemory

        self._time: float = 0.0
        self._last_cull: float = 0.0
        self._last_snapshot: float = 0.0

    # ── Public API ─────────────────────────────────────────────────────────

    def add_gravity_well(self, well: GravityWell) -> None:
        self.manifold.add_gravity_well(well)

    def remove_gravity_well(self, label: str) -> None:
        self.manifold.remove_gravity_well(label)

    def clear_wells(self) -> None:
        self.manifold.clear_wells()

    def spawn_agent(
        self,
        energy: float = 1.0,
        position: Optional[np.ndarray] = None,
    ) -> Optional[Agent]:
        """Manually spawn one agent. Returns None if at capacity."""
        if len(self._agents) >= self.max_agents:
            return None
        agent = self.physics.spawn(energy=energy, position=position)
        self._agents.append(agent)
        self._memories[agent.id] = AgentMemory(capacity=self.memory_capacity)
        logger.debug("Spawned agent %s (total=%d)", agent.id, len(self._agents))
        return agent

    def step(self, context, dt: float = 1 / 60) -> None:
        """
        Advance the agent system by *dt* seconds.

        Reads audio from ``context.inputs.get("audio_data")`` if available,
        then writes results back to ``context.agent_state``.
        """
        if dt <= 0:
            return

        self._time += dt

        # Read audio
        audio = self._extract_audio(context)

        # Auto-spawn on strong bass if below capacity
        if self.auto_spawn:
            bass = float((audio or {}).get("bass", 0.0))
            if bass > _SPAWN_ENERGY_THRESHOLD and len(self._agents) < self.max_agents:
                self.spawn_agent(energy=min(1.0, bass))

        # Physics step
        self.physics.step(self._agents, dt, audio=audio)

        # Memory snapshots
        if self._time - self._last_snapshot >= self.snapshot_interval:
            ctx_hash = id(context)
            for agent in self._agents:
                if agent.id in self._memories:
                    self._memories[agent.id].push_from_agent(agent, ctx_hash)
            self._last_snapshot = self._time

        # Cull dead agents periodically
        if self._time - self._last_cull >= _CULL_INTERVAL:
            before = len(self._agents)
            self._agents = AgentPhysics.cull_dead(self._agents)
            # Clean up memories for dead agents
            live_ids = {a.id for a in self._agents}
            self._memories = {k: v for k, v in self._memories.items() if k in live_ids}
            culled = before - len(self._agents)
            if culled:
                logger.debug("Culled %d dead agents (remaining=%d)", culled, len(self._agents))
            self._last_cull = self._time

        # Publish state to context
        self._publish(context)

    def get_memory(self, agent_id: str) -> Optional[AgentMemory]:
        """Return the memory buffer for a given agent ID."""
        return self._memories.get(agent_id)

    @property
    def agents(self) -> List[Agent]:
        return list(self._agents)

    @property
    def agent_count(self) -> int:
        return len(self._agents)

    # ── Internals ─────────────────────────────────────────────────────────

    def _extract_audio(self, context) -> dict:
        try:
            data = context.inputs.get("audio_data") or {}
            return {
                "bass": float(data.get("bass", 0.0)),
                "mid": float(data.get("mid", 0.0)),
                "treble": float(data.get("treble", 0.0)),
                "beat": float(data.get("beat", 0.0)),
            }
        except Exception:
            return {}

    def _publish(self, context) -> None:
        """Write agent state into context.agent_state."""
        if not hasattr(context, "agent_state"):
            try:
                context.agent_state = {}
            except Exception:
                return

        screen_positions = [a.screen_xy() for a in self._agents]
        param_influences = (
            np.stack([a.to_param_influence() for a in self._agents])
            if self._agents
            else np.empty((0, DIMS), dtype=np.float32)
        )

        context.agent_state = {
            "agents": list(self._agents),
            "screen_positions": screen_positions,
            "param_influences": param_influences,
            "agent_count": len(self._agents),
            "time": self._time,
        }
