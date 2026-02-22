"""
P1-R2: Effect Base Class
Base class for all VJLive3 effects.
"""
from typing import Tuple, Any, Optional
from .program import ShaderProgram

class Effect:
    """Base class for all VJLive3 effects. Holds shader + parameters."""

    # Required by PRIME_DIRECTIVE Rule 2 (Data Provenance)
    METADATA = {
        "author": "Antigravity (Manager)",
        "phase": "P1-R2",
        "description": "Base interface for pipeline rendering effects"
    }

    def __init__(self, name: str, fragment_source: str) -> None:
        self.name = name
        from .program import BASE_VERTEX_SHADER
        self.shader = ShaderProgram(BASE_VERTEX_SHADER, fragment_source, name)
        
        self.enabled: bool = True
        self.mix: float = 1.0
        self.manual_render: bool = False

    def apply_uniforms(
        self,
        time: float,
        resolution: Tuple[int, int],
        audio_reactor: Any,
        semantic_layer: Any,
    ) -> None:
        """Override in subclasses to bind per-frame params."""
        pass

    def pre_process(self, chain: "EffectChain", input_tex: int) -> Optional[int]:
        """Optional pre-pass (CPU ML, etc.). Return alt texture or None."""
        return None
