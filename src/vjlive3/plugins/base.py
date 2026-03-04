"""
Plugin base class for VJLive3 effects.
Distinct from vjlive3.render.effect.Effect (GPU-bound).
This base class supports CPU-side parameter management and uniform dispatch
with no GPU or display requirements — safe for unit tests without a render context.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class Effect:
    """
    Minimal base class for VJLive3 plugin effects.

    Subclasses implement:
      - get_fragment_shader()  → WGSL/GLSL source string
      - apply_uniforms(...)    → call self.set_uniform(name, value) for each param
      - load_preset(name)      → optional preset system

    set_uniform() is a no-op here; the renderer overrides it at runtime,
    and tests can mock it with MagicMock.
    """

    METADATA: dict = {}

    def __init__(self, name: str = "effect") -> None:
        self.name = name
        self.params: Dict[str, float] = {}
        self.enabled: bool = True

    # ---- GPU uniform dispatch (no-op in tests) ---------------------------

    def set_uniform(self, name: str, value: Any) -> None:
        """Override / mock this to capture uniform calls."""

    # ---- Subclass contract -----------------------------------------------

    def get_fragment_shader(self) -> str:
        """Return the WGSL/GLSL fragment shader source."""
        raise NotImplementedError(f"{type(self).__name__} must implement get_fragment_shader()")

    def apply_uniforms(
        self,
        time: float,
        resolution: Tuple[int, int],
        audio_reactor: Optional[Any] = None,
        semantic_layer: Optional[Any] = None,
    ) -> None:
        """Push all per-frame uniforms via set_uniform()."""

    # ---- Serialisation ---------------------------------------------------

    def get_state(self) -> Dict[str, Any]:
        return {"name": self.name, "params": dict(self.params)}
