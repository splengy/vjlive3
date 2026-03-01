import logging
from typing import Dict, Any, Tuple
from vjlive3.plugins.base import Effect

logger = logging.getLogger(__name__)

# METADATA required by safety rails
METADATA = {
    "name": "Bad Trip Datamosh",
    "version": "1.0.0",
    "description": "Simulates a psychedelic crisis. Aggressive, hostile, unsettling visuals.",
    "author": "VJLive3 Core",
    "license": "Proprietary",
}

FRAGMENT_SHADER = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D tex1;
uniform float time;
uniform vec2 resolution;

uniform float u_anxiety;
uniform float u_demon_face;
uniform float u_insect_crawl;
uniform float u_void_gaze;
uniform float u_reality_tear;
uniform float u_sickness;
uniform float u_time_loop;
uniform float u_breathing_walls;
uniform float u_paranoia;
uniform float u_shadow_people;
uniform float u_psychosis;
uniform float u_doom;

uniform float u_mix;

float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

void main() {
    vec2 uv = v_uv;
    vec2 texel = 1.0 / resolution;

    bool hasDual = (texture(tex1, vec2(0.5)).r +
                    texture(tex1, vec2(0.5)).g +
                    texture(tex1, vec2(0.5)).b) > 0.001;

    float depth = texture(depth_tex, uv).r;

    if (u_breathing_walls > 0.0) {
        vec2 center = vec2(0.5);
        vec2 d = uv - center;
        float r = length(d);
        float a = atan(d.y, d.x);
        float breath = sin(time * u_anxiety + r * 10.0) * u_breathing_walls * 0.05;
        uv += d * breath;
    }

    if (depth > 0.2 && u_demon_face > 0.0) {
        float faceWarp = sin(uv.y * 50.0 + time * 10.0) * u_demon_face * 0.02;
        uv.x += faceWarp * smoothstep(0.2, 0.5, depth);

        vec2 eyeUV = (uv - 0.5) * vec2(1.0, 2.0);
        if (length(eyeUV) < 0.1) {
            uv -= (uv - 0.5) * u_demon_face * 0.5;
        }
    }

    if (u_insect_crawl > 0.0) {
        float bugs = hash(uv * 100.0 + vec2(time * 10.0, sin(time)));
        if (bugs > 0.95 - u_insect_crawl * 0.05) {
            uv += (vec2(hash(uv), hash(uv+1.0)) - 0.5) * 0.02;
        }
    }

    vec4 color = hasDual ? texture(tex1, uv) : texture(tex0, uv);
    vec4 prev = texture(texPrev, uv);

    color = mix(color, prev, u_time_loop * 0.5);

    if (u_reality_tear > 0.0) {
        float tear = step(0.98 - u_reality_tear * 0.1, hash(vec2(uv.y * 10.0, time)));
        if (tear > 0.5) {
            vec4 other = hasDual ? texture(tex0, uv) : vec4(1.0) - color;
            color = mix(color, other, 0.8);
        }
    }

    if (u_sickness > 0.0) {
        vec3 sickGreen = vec3(0.2, 0.5, 0.1);
        vec3 sickPurple = vec3(0.4, 0.0, 0.4);
        float sickMix = sin(time * 0.5) * 0.5 + 0.5;
        vec3 sickColor = mix(sickGreen, sickPurple, sickMix);
        color.rgb = mix(color.rgb, color.rgb * sickColor * 2.0, u_sickness * 0.5);
    }

    if (u_shadow_people > 0.0 && depth < 0.3) {
        color.rgb *= (1.0 - u_shadow_people * 0.8);
    }

    if (u_psychosis > 0.0) {
        color.rgb = abs(color.rgb - vec3(u_psychosis * 0.5));
    }

    if (u_void_gaze > 0.0) {
        float d = length(v_uv - 0.5);
        color.rgb *= smoothstep(0.8, 0.2, d * (1.0 + u_void_gaze));
    }

    color.rgb = (color.rgb - 0.5) * (1.0 + u_doom) + 0.5;

    if (u_paranoia > 0.0 && hash(vec2(time)) > 0.9) {
        color.rgb = vec3(0.0);
    }

    vec4 original = hasDual ? texture(tex1, v_uv) : texture(tex0, v_uv);
    fragColor = mix(original, color, u_mix);
}
"""

class BadTripDatamoshEffect(Effect):
    """Bad Trip Datamosh — The Nightmare Flip."""
    
    # Presets mapping (0-10 base scale)
    PRESETS = {
        'arachnophobia': {'insect_crawl': 10.0, 'shadow_people': 8.0, 'anxiety': 8.0, 'demon_face': 2.0},
        'ego_death': {'void_gaze': 10.0, 'reality_tear': 8.0, 'time_loop': 10.0, 'psychosis': 10.0, 'breathing_walls': 8.0},
        'schizoid': {'anxiety': 10.0, 'paranoia': 10.0, 'breathing_walls': 10.0, 'reality_tear': 10.0, 'shadow_people': 10.0},
        'demon_worship': {'demon_face': 9.0, 'doom': 8.0, 'sickness': 7.0, 'void_gaze': 6.0},
        'mild_trip': {'anxiety': 3.0, 'demon_face': 3.0, 'breathing_walls': 4.0, 'reality_tear': 2.0, 'paranoia': 1.0}
    }

    def __init__(self, name: str = 'bad_trip_datamosh'):
        super().__init__(name)
        # Base 0-10 parameters from UI
        self.params = {
            'anxiety': 6.0,
            'demon_face': 4.0,
            'insect_crawl': 3.0,
            'void_gaze': 5.0,
            'reality_tear': 4.0,
            'sickness': 5.0,
            'time_loop': 5.0,
            'breathing_walls': 4.0,
            'paranoia': 3.0,
            'shadow_people': 4.0,
            'psychosis': 2.0,
            'doom': 4.0
        }
        
    def get_fragment_shader(self) -> str:
        return FRAGMENT_SHADER

    def _map_param(self, name: str, out_min: float, out_max: float) -> float:
        """Map 0-10 parameter to output range."""
        val = self.params.get(name, 0.0)
        # clamp
        val = max(0.0, min(10.0, val))
        return (val / 10.0) * (out_max - out_min) + out_min

    def load_preset(self, preset_name: str):
        if preset_name in self.PRESETS:
            # reset all to 0 first, or merge? Let's just merge as per typical VJ workflow,
            # or actually, just set the ones in the preset, assuming a base state
            for k in self.params:
                self.params[k] = 0.0
            for k, v in self.PRESETS[preset_name].items():
                self.params[k] = v

    def apply_uniforms(self, time: float, resolution: Tuple[int, int],
                       audio_reactor=None, semantic_layer=None):
        """Apply all uniforms + audio modulation."""
        
        # Ranges:
        # anxiety: 0-10 directly in shader
        # others generally 0-1
        anxiety = self._map_param('anxiety', 0.0, 10.0)
        demon_face = self._map_param('demon_face', 0.0, 1.0)
        insect_crawl = self._map_param('insect_crawl', 0.0, 1.0)
        void_gaze = self._map_param('void_gaze', 0.0, 1.0)
        reality_tear = self._map_param('reality_tear', 0.0, 1.0)
        sickness = self._map_param('sickness', 0.0, 1.0)
        time_loop = self._map_param('time_loop', 0.0, 1.0)
        breathing_walls = self._map_param('breathing_walls', 0.0, 1.0)
        paranoia = self._map_param('paranoia', 0.0, 1.0)
        shadow_people = self._map_param('shadow_people', 0.0, 1.0)
        psychosis = self._map_param('psychosis', 0.0, 1.0)
        doom = self._map_param('doom', 0.0, 1.0)

        # Apply Audio Reactivity if available
        if audio_reactor:
            try:
                # Anxiety boosted by high-frequency energy
                anxiety *= (1.0 + audio_reactor.get_energy(0.5) * 0.5)
                # Demon face boosted by bass
                demon_face *= (1.0 + audio_reactor.get_band('bass', 0.0) * 0.5)
                # Paranoia boosted by overall energy
                paranoia *= (1.0 + audio_reactor.get_energy(0.5) * 0.5)
                # Breathing walls boosted by mid frequencies
                breathing_walls *= (1.0 + audio_reactor.get_band('mid', 0.0) * 0.5)
            except Exception:
                pass  # Silently ignore audio errors as per spec
                
        # Send to OpenGL (Assuming base class handles actual glUniform calls via self.set_uniform)
        # The base Effect class handles time, resolution, and mix.
        self.set_uniform("u_anxiety", anxiety)
        self.set_uniform("u_demon_face", demon_face)
        self.set_uniform("u_insect_crawl", insect_crawl)
        self.set_uniform("u_void_gaze", void_gaze)
        self.set_uniform("u_reality_tear", reality_tear)
        self.set_uniform("u_sickness", sickness)
        self.set_uniform("u_time_loop", time_loop)
        self.set_uniform("u_breathing_walls", breathing_walls)
        self.set_uniform("u_paranoia", paranoia)
        self.set_uniform("u_shadow_people", shadow_people)
        self.set_uniform("u_psychosis", psychosis)
        self.set_uniform("u_doom", doom)

        # Note: texPrev (unit 1) and other textures must be bound by the rendering chain before calling this.

    def get_state(self) -> Dict[str, Any]:
        """Return effect state for serialization."""
        return {
            "name": self.name,
            "params": self.params.copy()
        }
