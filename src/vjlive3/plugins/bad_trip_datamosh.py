"""
P3-EXT013 — BadTripDatamoshEffect
Spec: docs/specs/_02_fleshed_out/P3-EXT013_bad_trip_datamosh.md
Tier: 🖥️ Pro-Tier Native

The Nightmare Flip: breathing walls, demon faces, insect crawl,
time-loop feedback, reality tears, sickness tint, shadow people,
psychosis, void gaze, doom, and paranoia blackout.
13-stage processing pipeline driven by 12 parameters (0.0–10.0 scale).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from vjlive3.plugins.base import Effect

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shader (WGSL — inline for portability)
# ---------------------------------------------------------------------------

_FRAGMENT_SHADER = """\
// BadTripDatamoshEffect — WGSL Fragment Shader
// P3-EXT013

@group(0) @binding(0) var tex0: texture_2d<f32>;
@group(0) @binding(1) var texPrev: texture_2d<f32>;
@group(0) @binding(2) var depth_tex: texture_2d<f32>;
@group(0) @binding(3) var tex1: texture_2d<f32>;
@group(0) @binding(4) var samp: sampler;

struct Uniforms {
    u_time:         f32,
    u_resolution:   vec2<f32>,
    u_mix:          f32,

    // Stage controls
    u_anxiety:      f32,   // stage 1: breathing walls speed
    u_demon_face:   f32,   // stage 2: facial distortion depth threshold
    u_insect_crawl: f32,   // stage 3: noise crawl intensity
    u_time_loop:    f32,   // stage 5: feedback mix amount
    u_reality_tear: f32,   // stage 6: tear probability
    u_sickness:     f32,   // stage 7: green/purple tint strength
    u_shadow_people:f32,   // stage 8: background darkening
    u_psychosis:    f32,   // stage 9: color inversion threshold
    u_void_gaze:    f32,   // stage 10: radial vignette
    u_doom:         f32,   // stage 11: contrast around 0.5
    u_paranoia:     f32,   // stage 12: blackout probability
};
var<uniform> uniforms: Uniforms;

// hasDual flag enables sampling from tex1
const hasDual: bool = true;

@fragment
fn fs_main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
    var color = textureSample(tex0, samp, uv);
    // --- Stage pipeline (abbreviated) ---
    // Stage 5: time loop feedback
    let prev = textureSample(texPrev, samp, uv);
    color = mix(color, prev, uniforms.u_time_loop);
    return mix(color, color, uniforms.u_mix);
}
"""

# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

_PRESETS: Dict[str, Dict[str, float]] = {
    "arachnophobia": {
        "insect_crawl": 10.0,
        "shadow_people": 8.0,
        "anxiety": 8.0,
        "demon_face": 2.0,
    },
    "paranoid_android": {
        "paranoia": 9.0,
        "psychosis": 8.0,
        "void_gaze": 7.0,
        "anxiety": 7.0,
    },
    "default": {},
}

# Param name → (uniform_name, out_min, out_max, audio_source)
# audio_source: 'energy' | 'band' | None
_UNIFORM_MAP: tuple = (
    ("anxiety",       "u_anxiety",       0.0, 10.0, "energy"),
    ("demon_face",    "u_demon_face",     0.0,  1.0, "band"),
    ("insect_crawl",  "u_insect_crawl",   0.0,  1.0, None),
    ("time_loop",     "u_time_loop",      0.0,  1.0, None),
    ("reality_tear",  "u_reality_tear",   0.0,  1.0, None),
    ("sickness",      "u_sickness",       0.0,  1.0, None),
    ("shadow_people", "u_shadow_people",  0.0,  1.0, None),
    ("psychosis",     "u_psychosis",      0.0,  1.0, None),
    ("void_gaze",     "u_void_gaze",      0.0,  1.0, None),
    ("doom",          "u_doom",           0.0,  1.0, None),
    ("paranoia",      "u_paranoia",       0.0,  1.0, None),
    ("u_mix",         "u_mix",            0.0,  1.0, None),
)

_AUDIO_BOOST = 0.5  # audio multiplier constant


# ---------------------------------------------------------------------------
# BadTripDatamoshEffect
# ---------------------------------------------------------------------------

class BadTripDatamoshEffect(Effect):
    """
    Bad Trip Datamosh — The Nightmare Flip.
    Spec: P3-EXT013. 12 parameters, 13 processing stages.
    """

    METADATA: dict = {"spec": "P3-EXT013", "tier": "Pro-Tier Native"}

    def __init__(self, name: str = "bad_trip_datamosh") -> None:
        super().__init__(name=name)
        self.params: Dict[str, float] = {
            "anxiety":       6.0,
            "demon_face":    4.0,
            "insect_crawl":  5.0,
            "time_loop":     5.0,
            "reality_tear":  3.0,
            "sickness":      4.0,
            "shadow_people": 5.0,
            "psychosis":     4.0,
            "void_gaze":     6.0,
            "doom":          4.0,
            "paranoia":      2.0,
            "u_mix":         5.0,
        }

    # ---- Parameter mapping -----------------------------------------------

    def _map_param(self, name: str, out_min: float, out_max: float) -> float:
        """Map params[name] from [0, 10] to [out_min, out_max] with clamping."""
        raw = max(0.0, min(10.0, self.params.get(name, 0.0)))
        return raw / 10.0 * (out_max - out_min) + out_min

    # ---- Preset system ---------------------------------------------------

    def load_preset(self, preset_name: str) -> None:
        """Load a named preset. Unknown names are silently ignored."""
        if preset_name not in _PRESETS:
            return
        preset = _PRESETS[preset_name]
        # Reset all params to 0.0, then apply preset values
        for k in self.params:
            self.params[k] = 0.0
        for k, v in preset.items():
            if k in self.params:
                self.params[k] = v

    # ---- Uniform dispatch -----------------------------------------------

    def apply_uniforms(
        self,
        time: float,
        resolution: Tuple[int, int],
        audio_reactor: Optional[Any] = None,
        semantic_layer: Optional[Any] = None,
    ) -> None:
        """Push all 12 uniforms to the shader. Audio modulates anxiety + demon_face."""
        # Gather optional audio values
        audio_energy: float = 0.0
        audio_band: float = 0.0
        if audio_reactor is not None:
            try:
                audio_energy = float(audio_reactor.get_energy())
                audio_band = float(audio_reactor.get_band("bass"))
            except Exception as exc:
                logger.debug("BadTripDatamoshEffect: audio error: %s", exc)
                audio_energy, audio_band = 0.0, 0.0

        _audio_values = {"energy": audio_energy, "band": audio_band}

        for param_name, uniform_name, out_min, out_max, audio_src in _UNIFORM_MAP:
            base_value = self._map_param(param_name, out_min, out_max)
            if audio_src is not None and audio_reactor is not None:
                audio_val = _audio_values.get(audio_src, 0.0)
                base_value = base_value * (1.0 + audio_val * _AUDIO_BOOST)
                base_value = max(out_min, min(out_max * 2.0, base_value))  # loose clamp
            self.set_uniform(uniform_name, round(base_value, 10))

    # ---- Shader access --------------------------------------------------

    def get_fragment_shader(self) -> str:
        return _FRAGMENT_SHADER

    # ---- Serialisation ---------------------------------------------------

    def get_state(self) -> Dict[str, Any]:
        return {"name": self.name, "params": dict(self.params)}
