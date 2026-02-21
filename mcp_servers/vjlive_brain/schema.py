"""Schema definitions for the VJLive Brain knowledge base."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LogicPurity(str, Enum):
    """How bug-free is the extracted essence of a concept?"""
    CLEAN = "clean"         # Ported logic is reliable
    BUGGY = "buggy"         # Known bugs — do NOT port bugs
    GENIUS = "genius"       # Dreamer-flagged, confirmed viable
    UNKNOWN = "unknown"     # Not yet analyzed
    DREAMER_DEAD_END = "dreamer_dead_end"  # Analyzed, not viable


class RoleAssignment(str, Enum):
    """
    Manager = Orchestrator (spec writing, validation, BOARD.md).
    Worker  = Processor (single-file implementation, effect execution).
    """
    MANAGER = "manager"
    WORKER = "worker"


class DreamerVerdict(str, Enum):
    """Outcome of Dreamer analysis."""
    PENDING = "pending"
    GENIUS = "genius"       # Port it — validated viable
    SANDBOX = "sandbox"     # Promising but unstable — needs research
    DEAD_END = "dead_end"   # Not viable — documented why


class ConceptEntry(BaseModel):
    """
    A single entry in the Repository of Truth.

    Each entry maps a VJLive concept (effect, system, hardware integration)
    from its legacy origin to its VJLive3 implementation target.

    The `role_assignment` field enforces the Architect/Artisan split:
    - manager: orchestration logic, spec patterns, system design
    - worker: effect processing, plugin execution, single-file scope

    Workers should query `search_concepts(role='worker')` to stay in scope.
    """

    # Identity
    concept_id: str = Field(description="Unique slug, e.g. 'vimana-depth-mosh'")
    name: str = Field(description="Human-readable name")
    description: str = Field(description="2-3 sentences describing the concept")

    # Provenance
    origin_ref: str = Field(
        description="'vjlive-v1' | 'vjlive-v2' | 'both' | 'none'"
    )
    source_files: list[str] = Field(
        default_factory=list,
        description="Legacy file paths where this concept was found",
    )

    # Dreamer analysis
    dreamer_flag: bool = Field(
        default=False,
        description="True if this contains [DREAMER_LOGIC] requiring analysis",
    )
    dreamer_analysis: str = Field(
        default="",
        description="Analysis of the Dreamer logic — is it genius or hallucination?",
    )
    dreamer_verdict: DreamerVerdict = Field(
        default=DreamerVerdict.PENDING,
        description="Outcome of Dreamer analysis",
    )

    # Quality assessment
    logic_purity: LogicPurity = Field(
        default=LogicPurity.UNKNOWN,
        description="How clean/reliable is the extracted essence?",
    )

    # Agent roles
    role_assignment: RoleAssignment = Field(
        description="'manager' (orchestrator) | 'worker' (processor)"
    )

    # Phase gate relevance
    kitten_status: bool = Field(
        default=False,
        description="True if this concept contributes to the windowed app phase gate",
    )

    # Taxonomy
    tags: list[str] = Field(default_factory=list)
    category: str = Field(
        description="'engine' | 'plugin' | 'ui' | 'hardware' | 'dreamer' | 'test'"
    )
    performance_impact: str = Field(
        default="unknown",
        description="'low' | 'medium' | 'high' | 'unknown'",
    )

    # Porting status
    ported_to: str = Field(
        default="",
        description="VJLive3 file path once ported. Empty if not yet ported.",
    )
    ported_date: Optional[str] = Field(
        default=None,
        description="ISO date when porting was completed",
    )

    @property
    def is_ported(self) -> bool:
        """True if this concept has been ported to VJLive3."""
        return bool(self.ported_to)

    @property
    def display_status(self) -> str:
        """Human-readable status for display."""
        if self.is_ported:
            return f"✅ Ported → {self.ported_to}"
        if self.dreamer_flag and self.dreamer_verdict == DreamerVerdict.PENDING:
            return "⚠️ [DREAMER_LOGIC] — analysis pending"
        return "⬜ Not yet ported"
