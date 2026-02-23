"""
P3-EXT005: LivingFractalConsciousness — Julia set fractal with 5-agent personality system.

Sophisticated fractal visualization whose parameters are continuously influenced by
5 distinct agent personalities: Trinity (chaos), Cipher (analog), Neon (audio),
Azura (cosmic), Antigravity (harmony). Includes snapshot morphing, audio reactivity,
and an AI suggestion engine for live performance.

Ported from VJLive-2: plugins/core/living_fractal_consciousness/__init__.py (626 lines)
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import math
import time as _time
import logging
try:
    import numpy as np
    HAS_NP = True
except ImportError:
    HAS_NP = False
try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
# # from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

# ── Agent system ─────────────────────────────────────────────────────────────

class AgentPersonality(Enum):
    TRINITY    = "trinity"
    CIPHER     = "cipher"
    NEON       = "neon"
    AZURA      = "azura"
    ANTIGRAVITY = "antigravity"


VALID_MOODS = ("ecstatic", "calm", "aggressive", "melancholic", "mysterious", "neutral")

MOOD_MODIFIERS: Dict[str, Dict[str, float]] = {
    "ecstatic":    {"evolution_speed": 0.3, "glow": 0.2, "decay": -0.15},
    "calm":        {"distortion": -0.4, "symmetry": 0.25, "decay": 0.2},
    "aggressive":  {"pulse": 0.5, "distortion": 0.3, "glow": -0.2},
    "mysterious":  {"color_shift": 0.4, "zoom": 0.3, "complexity": -0.25},
    "melancholic": {"noise": 0.5, "decay": 0.3, "glow": -0.4},
    "neutral":     {},
}

_DEFAULT_CONFIGS: Dict[AgentPersonality, Dict] = {
    AgentPersonality.TRINITY:     {"intensity": 0.8, "mood": "ecstatic",
        "weights": {"complexity": 0.9, "evolution_speed": 0.95, "distortion": 0.7,
                    "glow": 0.6, "noise": 0.3, "chromatic_aberration": 0.4,
                    "zoom": 0.2, "color_shift": 0.5, "pulse": 0.3, "symmetry": 0.4, "decay": 0.5}},
    AgentPersonality.CIPHER:      {"intensity": 0.6, "mood": "calm",
        "weights": {"complexity": 0.4, "evolution_speed": 0.3, "distortion": 0.8,
                    "glow": 0.2, "noise": 0.95, "chromatic_aberration": 0.85,
                    "zoom": 0.3, "color_shift": 0.4, "pulse": 0.2, "symmetry": 0.5, "decay": 0.7}},
    AgentPersonality.NEON:        {"intensity": 0.7, "mood": "aggressive",
        "weights": {"complexity": 0.5, "evolution_speed": 0.8, "distortion": 0.4,
                    "glow": 0.7, "noise": 0.2, "chromatic_aberration": 0.3,
                    "zoom": 0.4, "color_shift": 0.9, "pulse": 0.95, "symmetry": 0.3, "decay": 0.4}},
    AgentPersonality.AZURA:       {"intensity": 0.75, "mood": "mysterious",
        "weights": {"complexity": 0.6, "evolution_speed": 0.4, "distortion": 0.3,
                    "glow": 0.85, "noise": 0.1, "chromatic_aberration": 0.2,
                    "zoom": 0.9, "color_shift": 0.8, "pulse": 0.4, "symmetry": 0.6, "decay": 0.3}},
    AgentPersonality.ANTIGRAVITY: {"intensity": 0.85, "mood": "neutral",
        "weights": {"complexity": 0.7, "evolution_speed": 0.5, "distortion": 0.4,
                    "glow": 0.9, "noise": 0.15, "chromatic_aberration": 0.25,
                    "zoom": 0.5, "color_shift": 0.6, "pulse": 0.35, "symmetry": 0.95, "decay": 0.85}},
}

PARAM_ORDER = ["complexity", "evolution_speed", "distortion", "glow", "noise",
               "chromatic_aberration", "zoom", "color_shift", "pulse", "symmetry", "decay"]


@dataclass
class AgentInfluence:
    personality: AgentPersonality
    intensity: float = 0.8
    mood: str = "neutral"
    parameter_weights: Dict[str, float] = field(default_factory=dict)
    _peak_intensity: float = 0.0
    _peak_timer: float = 0.0
    _peak_duration: float = 0.0

    def effective_intensity(self) -> float:
        return max(self.intensity, self._peak_intensity)


@dataclass
class FractalSnapshot:
    timestamp: float
    description: str
    parameters: Dict[str, float]
    agent_states: Dict[str, Dict]


# ── Metadata ─────────────────────────────────────────────────────────────────

METADATA = {
    "name": "Living Fractal Consciousness",
    "description": "Julia set fractal with 5-agent personality system, audio reactivity, and state morphing.",
    "version": "3.0.0",
    "plugin_type": "effect",
    "category": "generator",
    "tags": ["fractal", "agent", "consciousness", "audio_reactive", "julia", "ai"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "complexity",          "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "evolution_speed",     "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "distortion",          "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "glow",                "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "noise",               "type": "float", "default": 1.5, "min": 0.0, "max": 10.0},
        {"name": "chromatic_aberration","type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "zoom",                "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
        {"name": "color_shift",         "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "pulse",               "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "symmetry",            "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "decay",               "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        # Agent intensities
        {"name": "trinity_intensity",   "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        {"name": "cipher_intensity",    "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        {"name": "neon_intensity",      "type": "float", "default": 7.0, "min": 0.0, "max": 10.0},
        {"name": "azura_intensity",     "type": "float", "default": 7.5, "min": 0.0, "max": 10.0},
        {"name": "antigravity_intensity","type": "float", "default": 8.5, "min": 0.0, "max": 10.0},
        {"name": "mix",                 "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
    ],
}

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1), vec2(1,-1), vec2(-1,1), vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID],0.0,1.0); uv=verts[gl_VertexID]*0.5+0.5; }
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv; out vec4 fragColor;
uniform sampler2D u_texture;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_mix;
uniform float u_params[11];          // PARAM_ORDER indexed
uniform float u_agent_influence[5];  // intensity per agent
uniform float u_agent_moods[5];      // mood modifier per agent (0=neutral, 1=ecstatic, etc.)

float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
vec3 palette(float t, float shift) {
    vec3 a = vec3(0.5), b = vec3(0.5);
    vec3 c = vec3(1.0), d = vec3(0.263, 0.416, 0.557);
    return a + b * cos(6.283185*(c*t + d + shift));
}

void main() {
    // Unpack params
    float complexity   = u_params[0] / 10.0 * 4.0 + 0.5;  // 0.5-4.5 iterations scale
    float evo_speed    = u_params[1] / 10.0 * 2.0;
    float distortion   = u_params[2] / 10.0 * 0.5;
    float glow_str     = u_params[3] / 10.0 * 2.0;
    float noise_amt    = u_params[4] / 10.0 * 0.15;
    float chroma       = u_params[5] / 10.0 * 0.02;
    float zoom         = 0.5 + u_params[6] / 10.0 * 3.0;
    float color_shift  = u_params[7] / 10.0;
    float pulse        = u_params[8] / 10.0;
    float symmetry_ord = max(2.0, floor(u_params[9] / 10.0 * 6.0) + 2.0);  // 2-8
    float decay_v      = u_params[10] / 10.0 * 0.95;

    // Agent influence weighting
    float trinity    = u_agent_influence[0];
    float cipher_v   = u_agent_influence[1];
    float neon       = u_agent_influence[2];
    float azura      = u_agent_influence[3];
    float anti       = u_agent_influence[4];

    // Dynamic C parameter for Julia set, influenced by agents
    float t = u_time * evo_speed * (1.0 + trinity * 0.5);
    float cx = -0.7 + 0.2 * sin(t * 0.16 + anti * 0.3) + distortion * trinity * 0.3;
    float cy =  0.27 + 0.15 * cos(t * 0.23 + azura * 0.2) + distortion * cipher_v * 0.2;

    // UV to complex plane
    vec2 fc = (uv * 2.0 - 1.0) * vec2(u_resolution.x / u_resolution.y, 1.0);
    fc /= zoom * (1.0 + azura * 0.5);

    // Symmetry folding
    float sym_angle = 6.28318 / symmetry_ord;
    float angle = atan(fc.y, fc.x);
    angle = mod(angle, sym_angle);
    if (angle > sym_angle * 0.5) angle = sym_angle - angle;
    fc = length(fc) * vec2(cos(angle), sin(angle));

    // Wave distortion (Cipher)
    vec2 warp = vec2(sin(fc.y * 3.0 + t * cipher_v * 0.5), cos(fc.x * 3.0 + t * cipher_v * 0.4));
    fc += warp * distortion * 0.1 * cipher_v;

    // Julia iteration
    vec2 z = fc;
    vec2 c2 = vec2(cx, cy);
    float n = 0.0;
    int max_iter = 64;
    for (int i = 0; i < 64; i++) {
        if (dot(z,z) > 4.0) { n = float(i); break; }
        z = vec2(z.x*z.x - z.y*z.y + c2.x, 2.0*z.x*z.y + c2.y);
        n = float(i);
    }
    float smooth_n = n - log2(log2(dot(z,z))) / log2(complexity + 1.0);
    float t_col = smooth_n / 64.0;

    // Color
    float shift = color_shift + neon * 0.2 * sin(u_time * 2.0) + azura * 0.15;
    vec3 col = palette(t_col, shift);

    // Glow (Antigravity + Azura)
    float glow_bloom = pow(1.0 - clamp(t_col, 0.0, 1.0), 3.0) * glow_str * (anti + azura) * 0.5;
    col += glow_bloom;

    // Audio pulse (Neon) — momentary brightness
    col *= 1.0 + pulse * neon * sin(u_time * 20.0) * 0.3;

    // Chromatic aberration (Cipher)
    if (chroma > 0.001) {
        vec2 off = (uv - 0.5) * chroma * cipher_v;
        float r2 = texture(u_texture, uv + off).r;
        float b2 = texture(u_texture, uv - off).b;
        col.r = mix(col.r, r2, 0.3 * cipher_v);
        col.b = mix(col.b, b2, 0.3 * cipher_v);
    }

    // Film grain noise (Cipher)
    if (noise_amt > 0.0) col += (hash(uv * u_resolution + u_time * 100.0) - 0.5) * noise_amt * cipher_v;

    col = clamp(col, 0.0, 1.0);

    vec4 src = texture(u_texture, uv);
    fragColor = mix(src, vec4(col, 1.0), u_mix);
}
"""

PRESETS = {
    "balanced":         {"complexity": 5.0, "evolution_speed": 3.0, "distortion": 2.0, "glow": 4.0,
                         "noise": 1.5, "chromatic_aberration": 2.0, "zoom": 1.0, "color_shift": 3.0,
                         "pulse": 0.0, "symmetry": 5.0, "decay": 2.0},
    "trinity_dominant": {"complexity": 8.0, "evolution_speed": 8.0, "distortion": 5.0, "glow": 6.0,
                         "noise": 3.0, "trinity_intensity": 10.0},
    "neon_pulse":       {"pulse": 9.0, "color_shift": 8.0, "evolution_speed": 7.0,
                         "neon_intensity": 10.0, "glow": 7.0},
    "azura_cosmic":     {"zoom": 8.0, "glow": 9.0, "color_shift": 8.0, "complexity": 7.0,
                         "azura_intensity": 10.0},
    "cipher_analog":    {"noise": 8.0, "chromatic_aberration": 7.0, "decay": 7.0,
                         "distortion": 6.0, "cipher_intensity": 10.0},
}


def _safe_float(v: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, float(v)))


class LivingFractalConsciousnessPlugin(object):
    """Julia set fractal with 5-agent personality system and audio reactivity."""

    def __init__(self):
        super().__init__()
        self._mock_mode    = not (HAS_GL and HAS_NP)
        self.prog          = 0
        self.vao           = 0
        self._initialized  = False
        self._time         = 0.0

        # Base parameter state
        self.params: Dict[str, float] = {p["name"]: p["default"] for p in METADATA["parameters"]}

        # Agent objects
        self.agents: Dict[AgentPersonality, AgentInfluence] = {}
        for personality, cfg in _DEFAULT_CONFIGS.items():
            a = AgentInfluence(personality=personality, intensity=cfg["intensity"],
                               mood=cfg["mood"], parameter_weights=dict(cfg["weights"]))
            self.agents[personality] = a

        # Audio smoothing buffer
        self.audio_buffer: Dict[str, float] = {"bass": 0.0, "mid": 0.0, "high": 0.0, "beat": 0.0, "volume": 0.0}

        # Snapshot / morph
        self.morph_target:       Optional[FractalSnapshot] = None
        self.morph_start_params: Dict[str, float]          = {}
        self.morph_target_params: Dict[str, float]         = {}
        self.morph_progress:     float = 0.0
        self.morph_duration:     float = 5.0

        # Agent evolution tracker
        self._last_evolve_time:  float = 0.0
        self._evolve_interval:   float = 7.0  # seconds between mood changes

        # AI suggestion history
        self.param_history: List[Dict[str, float]] = []
        self._last_suggestion_time: float = 0.0

    # ── GL helpers ────────────────────────────────────────────────────────────

    def _compile(self, vs: str, fs: str) -> int:
        v = gl.glCreateShader(gl.GL_VERTEX_SHADER);  gl.glShaderSource(v, vs); gl.glCompileShader(v)
        if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
        f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER); gl.glShaderSource(f, fs); gl.glCompileShader(f)
        if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
        p = gl.glCreateProgram(); gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f); return p

    def _uloc(self, name: str) -> int:
        return gl.glGetUniformLocation(self.prog, name)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def get_metadata(self) -> Dict:
        return METADATA

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"LivingFractalConsciousnessPlugin init: {e}")
            self._mock_mode = True; return False

    # ── Parameter management ──────────────────────────────────────────────────

    def set_parameter(self, name: str, value: float) -> None:
        if name in self.params:
            self.params[name] = _safe_float(value)
        else:
            logger.warning(f"Unknown param: {name}")

    # ── Agent interface ───────────────────────────────────────────────────────

    def set_agent_mood(self, personality: AgentPersonality, mood: str) -> None:
        if mood not in VALID_MOODS:
            raise ValueError(f"Invalid mood '{mood}'. Must be one of {VALID_MOODS}")
        self.agents[personality].mood = mood

    def trigger_agent_peak(self, personality: AgentPersonality, duration: float = 2.0) -> None:
        a = self.agents[personality]
        a._peak_intensity = min(2.0, a.intensity * 2.0)
        a._peak_timer     = 0.0
        a._peak_duration  = duration

    def get_agent_status(self) -> Dict:
        return {
            p.value: {"intensity": a.intensity, "mood": a.mood,
                      "peak_active": a._peak_intensity > 0}
            for p, a in self.agents.items()
        }

    def get_agent_influence_vector(self) -> List[float]:
        return [self.agents[p].effective_intensity() for p in AgentPersonality]

    def get_agent_mood_vector(self) -> List[float]:
        moods = list(VALID_MOODS)
        return [float(moods.index(self.agents[p].mood)) for p in AgentPersonality]

    # ── Audio reactivity ──────────────────────────────────────────────────────

    def update_audio(self, audio_data: Dict) -> None:
        for key in self.audio_buffer:
            val = float(audio_data.get(key, 0.0))
            self.audio_buffer[key] = 0.7 * self.audio_buffer[key] + 0.3 * val
        # Map to pulse param (Neon agent)
        self.params["pulse"] = _safe_float(
            (self.audio_buffer["bass"] + self.audio_buffer["beat"]) * 5.0)

    # ── Agent evolution ───────────────────────────────────────────────────────

    def evolve_agents(self, delta_time: float) -> None:
        self._last_evolve_time += delta_time
        if self._last_evolve_time < self._evolve_interval:
            return
        self._last_evolve_time = 0.0
        import random
        # Random mood shift and intensity drift for one agent
        personality = random.choice(list(AgentPersonality))
        agent = self.agents[personality]
        new_mood = random.choice(VALID_MOODS)
        agent.mood = new_mood
        drift = random.uniform(-0.05, 0.05)
        agent.intensity = max(0.1, min(1.0, agent.intensity + drift))
        # Adjust interval randomly 5-15s
        self._evolve_interval = random.uniform(5.0, 15.0)

    def _update_peak_timers(self, dt: float) -> None:
        for a in self.agents.values():
            if a._peak_intensity > 0:
                a._peak_timer += dt
                if a._peak_timer >= a._peak_duration:
                    a._peak_intensity = 0.0
                    a._peak_timer = 0.0

    # ── Snapshot & morph ──────────────────────────────────────────────────────

    def create_snapshot(self, description: str = "") -> FractalSnapshot:
        return FractalSnapshot(
            timestamp=_time.time(),
            description=description,
            parameters=dict(self.params),
            agent_states={
                p.value: {"intensity": a.intensity, "mood": a.mood}
                for p, a in self.agents.items()
            }
        )

    def start_morph_to(self, target: FractalSnapshot, duration: float = 5.0) -> None:
        self.morph_start_params = dict(self.params)
        self.morph_target_params = dict(target.parameters)
        self.morph_target   = target
        self.morph_duration = max(0.1, duration)
        self.morph_progress = 0.0

    def update_morph(self, dt: float) -> bool:
        if self.morph_target is None:
            return True
        self.morph_progress += dt / self.morph_duration
        if self.morph_progress >= 1.0:
            self.morph_progress = 1.0
            for p in self.params:
                if p in self.morph_target_params:
                    self.params[p] = _safe_float(self.morph_target_params[p])
            self.morph_target = None
            return True
        t = self.morph_progress
        for p in self.params:
            if p in self.morph_start_params and p in self.morph_target_params:
                self.params[p] = _safe_float(
                    (1.0 - t) * self.morph_start_params[p] + t * self.morph_target_params[p])
        return False

    # ── AI suggestions ────────────────────────────────────────────────────────

    def suggest_parameter_change(self) -> Dict:
        now = _time.time()
        self.param_history.append(dict(self.params))
        if len(self.param_history) > 120:
            self.param_history = self.param_history[-120:]
        if now - self._last_suggestion_time < 30.0 or len(self.param_history) < 10:
            return {}
        self._last_suggestion_time = now
        # Heuristic suggestions
        if self.params["complexity"] < 3.0:
            return {"parameter": "complexity",
                    "current_value": self.params["complexity"],
                    "suggested_value": min(10.0, self.params["complexity"] + 1.5),
                    "confidence": 0.8, "reason": "Low complexity reduces visual interest"}
        if self.params["glow"] > 8.0:
            return {"parameter": "glow",
                    "current_value": self.params["glow"],
                    "suggested_value": max(0.0, self.params["glow"] - 2.0),
                    "confidence": 0.6, "reason": "High glow may cause visual fatigue"}
        if self.params["pulse"] < 1.0 and self.audio_buffer.get("bass", 0.0) > 0.5:
            return {"parameter": "pulse",
                    "current_value": self.params["pulse"],
                    "suggested_value": 5.0,
                    "confidence": 0.75, "reason": "Strong audio signal but pulse is low"}
        return {}

    # ── Agent-modified param computation ─────────────────────────────────────

    def _compute_agent_modified_params(self, external_params: Dict) -> List[float]:
        """Compute agent-influenced values for the 11 core params."""
        # Start from external frame params, fall back to self.params
        base = [_safe_float(external_params.get(p, self.params.get(p, 5.0))) for p in PARAM_ORDER]
        agents = list(AgentPersonality)
        for i, personality in enumerate(agents):
            agent = self.agents[personality]
            influence = agent.effective_intensity()
            weights = [agent.parameter_weights.get(p, 0.0) for p in PARAM_ORDER]
            mood_mods = MOOD_MODIFIERS.get(agent.mood, {})
            for j, p in enumerate(PARAM_ORDER):
                mood_w = mood_mods.get(p, 0.0)
                base[j] += influence * (weights[j] + mood_w) * 0.08
        return [_safe_float(v) for v in base]

    # ── Rendering ─────────────────────────────────────────────────────────────

    def process_frame(self, input_texture: int, params: Dict, context):
        if not input_texture or input_texture <= 0: return 0
        dt = 1.0 / 60.0; self._time += dt
        # Update agents
        self.update_morph(dt)
        self._update_peak_timers(dt)
        # Sync from frame params
        for p in self.params:
            if p in params:
                self.params[p] = _safe_float(params[p])
        # Agent intensities from frame params
        intensity_map = {
            AgentPersonality.TRINITY:     "trinity_intensity",
            AgentPersonality.CIPHER:      "cipher_intensity",
            AgentPersonality.NEON:        "neon_intensity",
            AgentPersonality.AZURA:       "azura_intensity",
            AgentPersonality.ANTIGRAVITY: "antigravity_intensity",
        }
        for personality, param_name in intensity_map.items():
            if param_name in params:
                self.agents[personality].intensity = _safe_float(params[param_name]) / 10.0

        # Audio from context
        audio = getattr(context, 'inputs', {}).get('audio_data', {})
        if isinstance(audio, dict) and audio:
            self.update_audio(audio)

        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
            return input_texture

        if not self._initialized: self.initialize(context)
        w = getattr(context, 'width', 1920); h = getattr(context, 'height', 1080)

        agent_params  = self._compute_agent_modified_params(params)
        influence_vec = self.get_agent_influence_vector()
        mood_vec      = self.get_agent_mood_vector()
        u_mix         = _safe_float(params.get('mix', 8.0)) / 10.0

        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._uloc('u_texture'), 0)
        gl.glUniform2f(self._uloc('u_resolution'), float(w), float(h))
        gl.glUniform1f(self._uloc('u_time'), self._time)
        gl.glUniform1f(self._uloc('u_mix'), u_mix)
        gl.glUniform1fv(self._uloc('u_params'), 11, agent_params)
        gl.glUniform1fv(self._uloc('u_agent_influence'), 5, influence_vec)
        gl.glUniform1fv(self._uloc('u_agent_moods'), 5, mood_vec)
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0); gl.glUseProgram(0)
        if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
        return input_texture

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
        except Exception as e: logger.error(f"LivingFractalConsciousnessPlugin cleanup: {e}")
        finally: self.prog = self.vao = 0
