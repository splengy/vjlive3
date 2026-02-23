"""vjlive3.agents — Autonomous agent system for VJLive3."""
from .agent import Agent, AgentState
from .manifold import Manifold16D, GravityWell
from .physics import AgentPhysics
from .memory import AgentMemory, Snapshot
from .bridge import AgentBridge

__all__ = [
    "Agent", "AgentState",
    "Manifold16D", "GravityWell",
    "AgentPhysics",
    "AgentMemory", "Snapshot",
    "AgentBridge",
]
