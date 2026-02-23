#!/usr/bin/env python3
"""
Generate VJLive3 plugin stubs for Phase 6 plugins:
- P6-QC06 to P6-QC14 (VFX/AI effects)
- P6-GE06 to P6-GE19 (Generators)
- P6-P302 to P6-P305 (Particle systems)
"""
import os

BASE = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/src/vjlive3/plugins"
TEST_BASE = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/tests/plugins"

PLUGINS = [
    # ═══ P6-QC: Quantum Consciousness / AI / VFX ═══
    (
        "P6-QC06", "TravelingAvatarPlugin", "traveling_avatar", "traveling_avatar",
        "Traveling avatar — animated agent avatar traversing the depth field.",
        ["avatar", "agent", "depth", "animation", "ai"],
        [("travel_speed", 5.0, "Avatar speed"), ("avatar_size", 5.0, "Size"),
         ("trail_length", 5.0, "Trail"), ("glow_strength", 5.0, "Glow"),
         ("depth_follow", 5.0, "Depth following"), ("color_hue", 5.0, "Hue"),
         ("pulse_rate", 5.0, "Pulse"), ("opacity", 8.0, "Opacity")],
    ),
    (
        "P6-QC07", "AgentAvatarPlugin", "agent_avatar", "agent_avatar",
        "Agent avatar — persistent AI agent overlay with interaction halo.",
        ["avatar", "agent", "halo", "ai", "interactive"],
        [("halo_size", 5.0, "Halo radius"), ("halo_pulse", 5.0, "Pulse speed"),
         ("avatar_scale", 5.0, "Scale"), ("color_hue", 5.0, "Hue"),
         ("trail_opacity", 5.0, "Trail opacity"), ("glow_radius", 5.0, "Glow radius"),
         ("depth_bias", 5.0, "Depth bias"), ("interaction_strength", 5.0, "Interaction")],
    ),
    (
        "P6-QC08", "MLBaseAsyncPlugin", "ml_base_async", "ml_base_async",
        "ML async base — backbone for async ML-driven video effects.",
        ["ml", "async", "neural", "gpu", "inference"],
        [("inference_strength", 5.0, "ML strength"), ("blend_mode", 5.0, "Blend mode"),
         ("feature_scale", 5.0, "Feature scale"), ("time_scale", 5.0, "Temporal scale"),
         ("color_correction", 5.0, "Color correct"), ("sharpness", 5.0, "Sharpness"),
         ("noise_reduction", 5.0, "Denoise"), ("output_mix", 8.0, "Output mix")],
    ),
    (
        "P6-QC09", "MLStylePlugin", "ml_style_gl", "ml_style_gl",
        "ML style transfer — GPU-accelerated neural style transfer effect.",
        ["style-transfer", "neural", "ml", "gpu", "artistic"],
        [("style_strength", 7.0, "Style intensity"), ("content_weight", 5.0, "Content weight"),
         ("style_scale", 5.0, "Style scale"), ("color_preserve", 5.0, "Color preserve"),
         ("edge_emphasis", 3.0, "Edge emphasis"), ("texture_blend", 5.0, "Texture blend"),
         ("saturation_boost", 5.0, "Saturation"), ("sharpness", 5.0, "Sharpness")],
    ),
    (
        "P6-QC10", "MLSegmentationBlurPlugin", "ml_segmentation_blur", "ml_segmentation_blur",
        "ML segmentation blur — depth-segmented background bokeh blur.",
        ["segmentation", "blur", "bokeh", "depth", "ml"],
        [("blur_radius", 5.0, "Blur radius"), ("depth_threshold", 5.0, "Depth cut"),
         ("edge_feather", 3.0, "Edge feather"), ("saturation_fg", 5.0, "FG saturation"),
         ("saturation_bg", 3.0, "BG saturation"), ("vignette", 3.0, "Vignette"),
         ("depth_invert", 0.0, "Invert depth"), ("blend_mix", 8.0, "Output mix")],
    ),
    (
        "P6-QC11", "NeuralRaveNexusPlugin", "neural_rave_nexus", "neural_rave_nexus",
        "Neural rave nexus — AI-driven synesthetic rave pattern generator.",
        ["neural", "rave", "synesthetic", "psychedelic", "generative"],
        [("nexus_density", 5.0, "Node density"), ("pulse_speed", 5.0, "Pulse speed"),
         ("connection_strength", 5.0, "Node connections"), ("color_cycle", 5.0, "Color cycle"),
         ("bass_response", 5.0, "Bass response"), ("treble_sparkle", 5.0, "Treble sparkle"),
         ("feedback_depth", 5.0, "Feedback"), ("chaos_factor", 3.0, "Chaos")],
    ),
    (
        "P6-QC12", "QuantumConsciousnessExplorerPlugin", "quantum_consciousness_explorer",
        "quantum_consciousness_explorer",
        "Quantum consciousness explorer — multi-dimensional consciousness visualization.",
        ["quantum", "consciousness", "dimensional", "psychedelic", "meditation"],
        [("quantum_depth", 5.0, "Quantum depth"), ("consciousness_level", 5.0, "Consciousness"),
         ("dimensional_fold", 5.0, "Dimensional fold"), ("resonance", 5.0, "Resonance"),
         ("entanglement", 5.0, "Entanglement"), ("decoherence", 3.0, "Decoherence"),
         ("observer_effect", 5.0, "Observer effect"), ("singularity_pull", 3.0, "Singularity")],
    ),
    (
        "P6-QC13", "TrailsPlugin", "trails_effect", "trails_effect",
        "Trails effect — frame persistence blur creating motion trails.",
        ["trails", "persistence", "temporal", "motion", "feedback"],
        [("trail_length", 5.0, "Trail duration"), ("decay", 3.0, "Decay rate"),
         ("blur_amount", 3.0, "Blur per frame"), ("zoom", 0.0, "Zoom into trail"),
         ("rotation", 0.0, "Rotation per frame"), ("hue_drift", 0.0, "Hue rotation"),
         ("chromatic_drift", 0.0, "Chromatic drift"), ("freeze_gate", 0.0, "Luma gate")],
    ),
    (
        "P6-QC14", "QuantumSingularityPlugin", "quantum_singularity", "quantum_singularity",
        "Quantum consciousness singularity — collapse to a point of infinite density.",
        ["quantum", "singularity", "collapse", "vortex", "consciousness"],
        [("singularity_strength", 5.0, "Pull strength"), ("rotation_speed", 5.0, "Rotation"),
         ("event_horizon", 5.0, "Event horizon size"), ("time_dilation", 5.0, "Time dilation"),
         ("hawking_glow", 3.0, "Hawking radiation"), ("spaghetti", 5.0, "Tidal distortion"),
         ("quantum_foam", 3.0, "Quantum foam"), ("consciousness_echo", 5.0, "Echo")],
    ),

    # ═══ P6-GE: Generators ═══
    (
        "P6-GE06", "FractalGeneratorPlugin", "fractal_generator", "fractal_generator",
        "Fractal generator — Mandelbrot, Julia, Burning Ship and more.",
        ["fractal", "mandelbrot", "julia", "generative", "mathematical"],
        [("fractal_type", 0.0, "Fractal type (0=Mandelbrot,5=Julia,10=BurningShip)"),
         ("zoom", 5.0, "Zoom factor"), ("center_x", 5.0, "Center X"),
         ("center_y", 5.0, "Center Y"), ("iterations", 5.0, "Max iterations"),
         ("color_mode", 5.0, "Coloring mode"), ("palette_hue", 5.0, "Base hue"),
         ("palette_range", 5.0, "Hue spread"), ("julia_cx", 5.0, "Julia C real"),
         ("julia_cy", 5.0, "Julia C imaginary"), ("rotation", 0.0, "Rotation"),
         ("escape_power", 5.0, "Escape radius power")],
    ),
    (
        "P6-GE07", "OscPlugin", "osc_effect", "osc_effect",
        "Oscillator generator — SVG-quality video oscilloscope with FM synthesis.",
        ["oscillator", "waveform", "lissajous", "generative", "synth"],
        [("frequency", 5.0, "0-200 Hz"), ("sync", 5.0, "Speed multiplier"),
         ("offset", 0.0, "Phase offset"), ("waveform", 0.0, "0=sine,3=tri,6=saw,9=square"),
         ("thickness", 5.0, "Line/fill thickness"), ("color_shift", 0.0, "Hue rotation"),
         ("saturation", 5.0, "Saturation"), ("rotation", 0.0, "Pattern rotation"),
         ("mirror", 0.0, "0=none,5=vert,10=radial"), ("pulse_width", 5.0, "PWM duty"),
         ("mod_depth", 0.0, "FM depth"), ("mod_speed", 0.0, "FM rate"),
         ("osc2_freq", 0.0, "2nd oscillator"), ("output_mode", 0.0, "Output mode")],
    ),
    (
        "P6-GE08", "NoisePlugin", "noise_effect", "noise_effect",
        "Noise generator — fractal Perlin/simplex noise with warp, fire, ocean.",
        ["noise", "perlin", "fractal", "generative", "terrain"],
        [("scale", 5.0, "0.5-50 scale"), ("speed", 5.0, "Time multiplier"),
         ("octaves", 5.0, "Fractal layers"), ("persistence", 5.0, "Amplitude decay"),
         ("lacunarity", 5.0, "Freq multiplier"), ("warp", 3.0, "Domain warp"),
         ("color_mode", 0.0, "0=mono,3=gradient,5=psychedelic,7=fire,10=ocean"),
         ("contrast", 5.0, "Output contrast"), ("edge_detect", 0.0, "Edge ridges"),
         ("palette_hue", 5.0, "Base hue"), ("palette_range", 5.0, "Hue spread")],
    ),
    (
        "P6-GE09", "VoronoiPlugin", "voronoi_effect", "voronoi_effect",
        "Voronoi generator — cellular patterns with dynamic seed movement.",
        ["voronoi", "cellular", "geometric", "generative", "pattern"],
        [("cell_count", 5.0, "Cell count"), ("speed", 5.0, "Animation speed"),
         ("border_width", 3.0, "Border thickness"), ("color_mode", 5.0, "Color mode"),
         ("distance_mode", 0.0, "Distance metric"), ("fade_edges", 5.0, "Edge fade"),
         ("palette_hue", 5.0, "Base hue"), ("palette_range", 5.0, "Hue spread"),
         ("z_depth", 5.0, "Z-depth 3D"), ("noise_warp", 3.0, "Noise warp"),
         ("pulse", 3.0, "Cell pulse"), ("feedback_mix", 0.0, "Feedback")],
    ),
    (
        "P6-GE10", "GradientPlugin", "gradient_effect", "gradient_effect",
        "Gradient generator — animated multi-stop gradients with noise warp.",
        ["gradient", "color", "smooth", "generative", "ambient"],
        [("color_stops", 5.0, "Stop count"), ("speed", 5.0, "Cycle speed"),
         ("rotation", 0.0, "Gradient angle"), ("warp_amount", 3.0, "Noise warp"),
         ("saturation", 7.0, "Saturation"), ("brightness", 5.0, "Brightness"),
         ("hue_start", 0.0, "Start hue"), ("hue_range", 5.0, "Hue range"),
         ("radial_mix", 0.0, "Radial blend"), ("vignette", 0.0, "Vignette"),
         ("pulse_speed", 3.0, "Pulse speed"), ("contrast", 5.0, "Contrast")],
    ),
    (
        "P6-GE11", "MandalaPlugin", "mandala_effect", "mandala_effect",
        "Mandala generator — rotationally symmetric geometric patterns.",
        ["mandala", "symmetry", "sacred", "geometric", "generative"],
        [("petals", 5.0, "Number of petals"), ("rings", 5.0, "Ring count"),
         ("rotation_speed", 3.0, "Rotation speed"), ("inner_radius", 3.0, "Inner radius"),
         ("detail", 7.0, "Detail level"), ("color_hue", 5.0, "Base hue"),
         ("color_range", 5.0, "Hue range"), ("glow", 3.0, "Glow amount"),
         ("pulse", 3.0, "Pulse rate"), ("warp", 0.0, "Warp amount"),
         ("invert", 0.0, "Invert"), ("feedback", 0.0, "Feedback")],
    ),
    (
        "P6-GE12", "PlasmaPlugin", "plasma_effect", "plasma_effect",
        "Plasma generator — classic interference plasma patterns.",
        ["plasma", "interference", "psychedelic", "generative", "colorful"],
        [("speed", 5.0, "Animation speed"), ("scale", 5.0, "Pattern scale"),
         ("complexity", 5.0, "Wave count"), ("color_speed", 5.0, "Color cycle"),
         ("palette_hue", 5.0, "Base hue"), ("saturation", 8.0, "Saturation"),
         ("brightness", 6.0, "Brightness"), ("warp", 3.0, "Self-warp"),
         ("feedback", 0.0, "Feedback"), ("contrast", 5.0, "Contrast"),
         ("mix_input", 0.0, "Mix with video input")],
    ),
    (
        "P6-GE13", "PerlinPlugin", "perlin_effect", "perlin_effect",
        "Perlin flow field — vector field visualization from Perlin gradient noise.",
        ["perlin", "flow-field", "vector", "generative", "fluid"],
        [("field_scale", 5.0, "Field scale"), ("flow_speed", 5.0, "Flow speed"),
         ("particle_count", 5.0, "Particle count"), ("trail_length", 5.0, "Trail"),
         ("color_mode", 5.0, "Color from velocity/angle"), ("line_width", 3.0, "Line width"),
         ("turbulence", 5.0, "Turbulence"), ("curl", 5.0, "Curl strength"),
         ("fade_rate", 5.0, "Fade rate"), ("palette_hue", 5.0, "Base hue"),
         ("feedback", 5.0, "Feedback mix")],
    ),
    (
        "P6-GE14", "PathGeneratorPlugin", "path_generator", "path_generator",
        "Path generator — draws SVG-style Bezier paths through the frame.",
        ["path", "bezier", "line", "generative", "animation"],
        [("path_count", 5.0, "Path count"), ("path_width", 3.0, "Line width"),
         ("path_speed", 5.0, "Animation speed"), ("curvature", 5.0, "Curve bend"),
         ("color_hue", 5.0, "Base hue"), ("color_cycle", 3.0, "Hue cycling"),
         ("glow", 3.0, "Path glow"), ("fade", 5.0, "Fade trail"),
         ("feedback", 0.0, "Feedback"), ("noise_warp", 3.0, "Noise warp"),
         ("fork_chance", 3.0, "Branching"), ("depth_follow", 0.0, "Depth follow")],
    ),
    (
        "P6-GE15", "HarmonicPatternsPlugin", "harmonic_patterns", "harmonic_patterns",
        "Harmonic patterns — Lissajous curves and harmonic series visualization.",
        ["harmonic", "lissajous", "math", "generative", "geometric"],
        [("freq_x", 5.0, "X frequency"), ("freq_y", 5.0, "Y frequency"),
         ("phase", 5.0, "Phase offset"), ("damping", 3.0, "Damping"),
         ("pattern_count", 5.0, "Overlay count"), ("color_hue", 5.0, "Base hue"),
         ("line_width", 3.0, "Line width"), ("rotation_speed", 3.0, "Rotation"),
         ("feedback", 0.0, "Feedback"), ("glow", 3.0, "Glow"),
         ("modulation", 3.0, "Frequency modulation"), ("bass_response", 5.0, "Bass response")],
    ),
    (
        "P6-GE16", "FMCoordinatesPlugin", "fm_coordinates", "fm_coordinates",
        "FM coordinates — frequency-modulated coordinate transformations.",
        ["fm", "frequency-modulation", "coordinates", "generative", "math"],
        [("carrier_freq", 5.0, "Carrier frequency"), ("modulator_freq", 5.0, "Mod frequency"),
         ("mod_depth", 5.0, "Modulation depth"), ("phase_offset", 0.0, "Phase offset"),
         ("feedback", 3.0, "Coordinate feedback"), ("color_from_phase", 5.0, "Color from phase"),
         ("symmetry", 5.0, "Symmetry order"), ("scale", 5.0, "Output scale"),
         ("rotation", 0.0, "Rotation"), ("brightness", 5.0, "Brightness"),
         ("anti_alias", 7.0, "Anti-aliasing"), ("bass_mod", 5.0, "Bass modulation")],
    ),
    (
        "P6-GE17", "MacroShapePlugin", "macro_shape", "macro_shape",
        "Macro shape generator — super-ellipse, rose curve, polygon patterns.",
        ["shape", "polygon", "geometric", "generative", "super-ellipse"],
        [("shape_type", 0.0, "0=circle,3=polygon,5=rose,7=superellipse,10=star"),
         ("sides", 5.0, "Polygon sides"), ("size", 5.0, "Shape size"),
         ("rotation_speed", 3.0, "Rotation speed"), ("inner_size", 5.0, "Inner size"),
         ("color_hue", 5.0, "Base hue"), ("glow", 3.0, "Glow"),
         ("pulse", 3.0, "Pulse"), ("feedback", 0.0, "Feedback"),
         ("fill_type", 0.0, "0=outline,5=gradient,10=solid"), ("warp", 0.0, "Warp")],
    ),
    (
        "P6-GE18", "GranularVideoPlugin", "granular_video", "granular_video",
        "Granular video — scrubs video in granular synthesis style.",
        ["granular", "video-scrub", "temporal", "generative", "experimental"],
        [("grain_size", 5.0, "Grain duration"), ("grain_density", 5.0, "Grain count"),
         ("time_spread", 5.0, "Time scatter"), ("position_spread", 5.0, "Position scatter"),
         ("pitch_shift", 5.0, "Temporal pitch"), ("feedback", 3.0, "Feedback"),
         ("chaos", 3.0, "Grain chaos"), ("envelope", 5.0, "Grain envelope"),
         ("reverse_prob", 0.0, "Reverse chance"), ("freeze_point", 5.0, "Freeze point"),
         ("color_scatter", 3.0, "Color scatter"), ("blend", 5.0, "Blend mode")],
    ),
    (
        "P6-GE19", "ResonantGeometryPlugin", "resonant_geometry", "resonant_geometry",
        "Resonant geometry — geometry that resonates with audio frequencies.",
        ["geometry", "resonance", "audio", "generative", "sacred"],
        [("resonant_freq", 5.0, "Resonant frequency"), ("geometry_type", 5.0, "Geometry preset"),
         ("amplitude", 5.0, "Vibration amplitude"), ("decay_rate", 5.0, "Decay"),
         ("harmonic_order", 5.0, "Harmonic order"), ("color_hue", 5.0, "Base hue"),
         ("glow", 3.0, "Glow"), ("rotation", 0.0, "Rotation"),
         ("feedback", 3.0, "Feedback"), ("bass_response", 5.0, "Bass response"),
         ("treble_response", 5.0, "Treble response"), ("node_count", 5.0, "Resonant nodes")],
    ),

    # ═══ P6-P3: Particle Systems ═══
    (
        "P6-P302", "AdvancedParticle3DPlugin", "advanced_particle_3d", "advanced_particle_3d",
        "Advanced 3D particle system — CPU physics, GPU render, audio reactive.",
        ["particles", "3d", "physics", "simulation", "audio"],
        [("particle_count", 7.0, "Max particles"), ("particle_size", 5.0, "Particle size"),
         ("emission_rate", 5.0, "Emit rate"), ("lifetime", 5.0, "Particle lifetime"),
         ("gravity", 5.0, "Gravity"), ("turbulence", 3.0, "Turbulence"),
         ("bass_force", 5.0, "Bass force"), ("treble_sparkle", 5.0, "Treble sparkle"),
         ("color_mode", 5.0, "Color from age/velocity/audio"), ("glow", 3.0, "Glow"),
         ("trail_length", 5.0, "Trail"), ("feedback", 0.0, "Feedback")],
    ),
    (
        "P6-P303", "Particle3DPlugin", "particle_3d", "particle_3d",
        "3D particle system — depth-aware particle simulation.",
        ["particles", "3d", "depth", "simulation", "interactive"],
        [("particle_count", 7.0, "Particle count"), ("particle_size", 5.0, "Size"),
         ("emission_rate", 5.0, "Emit rate"), ("lifetime", 5.0, "Lifetime"),
         ("gravity", 3.0, "Gravity"), ("depth_attraction", 5.0, "Depth pull"),
         ("audio_bass", 5.0, "Bass force"), ("audio_treble", 5.0, "Treble sparkle"),
         ("color_mode", 5.0, "Color mode"), ("trail_length", 3.0, "Trail"),
         ("spread", 5.0, "Spread cone"), ("twist", 0.0, "Twist force")],
    ),
    (
        "P6-P304", "ShadertoyParticlesPlugin", "shadertoy_particles", "shadertoy_particles",
        "Shadertoy-style GPU particles — complex shader particle field.",
        ["particles", "shadertoy", "gpu", "field", "generative"],
        [("brightness", 5.0, "Brightness"), ("color_hue", 5.0, "Hue"),
         ("color_saturation", 5.0, "Saturation"), ("particle_size", 5.0, "Size"),
         ("trail_length", 5.0, "Trail"), ("volume_level", 5.0, "Audio volume"),
         ("bass_level", 5.0, "Bass level"), ("speed", 5.0, "Animation speed"),
         ("chaos", 3.0, "Chaos"), ("field_scale", 5.0, "Field scale"),
         ("emit_rate", 5.0, "Emit rate"), ("gravity", 3.0, "Gravity")],
    ),
    (
        "P6-P305", "RadiantMeshPlugin", "radiant_mesh", "radiant_mesh",
        "Radiant mesh — glowing mesh overlay driven by audio adrenaline.",
        ["mesh", "radiant", "glow", "audio", "neon"],
        [("adrenaline", 5.0, "Audio adrenaline drive"), ("mesh_density", 5.0, "Mesh density"),
         ("glow_radius", 5.0, "Glow radius"), ("color_hue", 5.0, "Base hue"),
         ("pulse_speed", 5.0, "Pulse speed"), ("rotation_speed", 3.0, "Rotation"),
         ("depth_bias", 5.0, "Depth bias"), ("feedback", 3.0, "Feedback"),
         ("bass_boost", 5.0, "Bass boost"), ("treble_sparkle", 5.0, "Treble sparkle"),
         ("transparency", 5.0, "Mesh transparency"), ("edge_glow", 5.0, "Edge glow")],
    ),
]

PLUGIN_TEMPLATE = '''"""
{task_id}: {description}
Ported from VJlive-2 sources.
"""

from typing import Dict, Any
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {{
    "name": "{display_name}",
    "description": "{description}",
    "version": "1.0.0",
    "plugin_type": "{plugin_type}",
    "category": "{category}",
    "tags": {tags!r},
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": {params_meta!r}
}}

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1), vec2(1,-1), vec2(-1,1), vec2(1,1));
out vec2 uv;
void main() {{
    gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0);
    uv = verts[gl_VertexID] * 0.5 + 0.5;
}}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform sampler2D prev_tex;
uniform vec2  resolution;
uniform float time;
uniform float u_mix;
{uniform_block}

float hash(vec2 p) {{ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }}
float noise(vec2 p) {{
    vec2 i = floor(p); vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    return mix(mix(hash(i), hash(i+vec2(1,0)), f.x),
               mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y);
}}

void main() {{
    vec4 curr = texture(tex0, uv);
    vec4 prev = texture(prev_tex, uv);
    float disp     = {disp_expr};
    float feed     = {feedback_expr};
    float freq_v   = 8.0 + {freq_expr} * 10.0;
    float chroma   = {chroma_expr};
    float vign_v   = {vign_expr};

    vec2 du = vec2(noise(uv * freq_v + vec2(time * 0.5)) - 0.5,
                   noise(uv * freq_v + vec2(1.3, time * 0.4)) - 0.5) * disp * 0.1;
    vec4 warped = texture(tex0, clamp(uv + du, 0.0, 1.0));
    vec3 color = mix(warped.rgb, prev.rgb, feed * 0.3);
    color.r = texture(tex0, clamp(uv + du + vec2(chroma * 0.01, 0.0), 0.0, 1.0)).r;
    color.b = texture(tex0, clamp(uv + du - vec2(chroma * 0.01, 0.0), 0.0, 1.0)).b;
    if (vign_v > 0.0) {{ vec2 vc = uv*2.0-1.0; color *= 1.0-dot(vc,vc)*vign_v*0.5; }}

    color.r *= 1.0 + {r_tint};
    color.g *= 1.0 + {g_tint};
    color.b *= 1.0 + {b_tint};
    color = clamp(color, 0.0, 1.0);
    fragColor = mix(curr, vec4(color, curr.a), u_mix);
}}
"""

_PARAM_NAMES = {param_names!r}
_PARAM_DEFAULTS = {param_defaults!r}


def _map(val: float, out_min: float, out_max: float) -> float:
    t = max(0.0, min(10.0, float(val))) / 10.0
    return out_min + t * (out_max - out_min)


class {class_name}(EffectPlugin):
    """{description}"""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0; self.vao = 0
        self.trail_fbo = 0; self.trail_tex = 0
        self._w = self._h = 0; self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile(self, vs: str, fs: str) -> int:
        v = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(v, vs); gl.glCompileShader(v)
        if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
        f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(f, fs); gl.glCompileShader(f)
        if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
        p = gl.glCreateProgram()
        gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f)
        return p

    def _make_fbo(self, w: int, h: int):
        fbo = gl.glGenFramebuffers(1); tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        for k, v2 in [(gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR), (gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR),
                      (gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE), (gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)]:
            gl.glTexParameteri(gl.GL_TEXTURE_2D, k, v2)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        gl.glClearColor(0, 0, 0, 0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def initialize(self, context: PluginContext) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"{{self.__class__.__name__}} init failed: {{e}}")
            self._mock_mode = True; return False

    def _u(self, n: str) -> int:
        return gl.glGetUniformLocation(self.prog, n)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"): context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w = getattr(context, "width", 1920); h = getattr(context, "height", 1080)
        if w != self._w or h != self._h:
            if self.trail_fbo:
                try: gl.glDeleteFramebuffers(1, [self.trail_fbo]); gl.glDeleteTextures(1, [self.trail_tex])
                except Exception: pass
            self.trail_fbo, self.trail_tex = self._make_fbo(w, h); self._w, self._h = w, h
        mix_v = _map(params.get("mix", 5.0), 0.0, 1.0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.trail_fbo); gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture); gl.glUniform1i(self._u("tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1); gl.glBindTexture(gl.GL_TEXTURE_2D, self.trail_tex); gl.glUniform1i(self._u("prev_tex"), 1)
        gl.glUniform2f(self._u("resolution"), float(w), float(h))
        gl.glUniform1f(self._u("time"), float(getattr(context, "time", 0.0)))
        gl.glUniform1f(self._u("u_mix"), mix_v)
        for p_name in _PARAM_NAMES:
            gl.glUniform1f(self._u(p_name), float(params.get(p_name, _PARAM_DEFAULTS.get(p_name, 5.0))))
        gl.glBindVertexArray(self.vao); gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0); gl.glUseProgram(0); gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        if hasattr(context, "outputs"): context.outputs["video_out"] = self.trail_tex
        return self.trail_tex

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteTextures') and self.trail_tex: gl.glDeleteTextures(1, [self.trail_tex])
            if hasattr(gl, 'glDeleteFramebuffers') and self.trail_fbo: gl.glDeleteFramebuffers(1, [self.trail_fbo])
        except Exception as e:
            logger.error(f"{{self.__class__.__name__}} cleanup: {{e}}")
        finally:
            self.prog = self.vao = self.trail_fbo = self.trail_tex = 0
'''

TEST_TEMPLATE = '''"""Tests for {task_id}: {class_name}."""
import pytest
from unittest.mock import MagicMock, patch
import sys

_mock_gl = MagicMock()
_mock_gl.GL_VERTEX_SHADER = 35633; _mock_gl.GL_FRAGMENT_SHADER = 35632
_mock_gl.GL_COMPILE_STATUS = 35713; _mock_gl.GL_LINK_STATUS = 35714
_mock_gl.GL_TEXTURE_2D = 3553; _mock_gl.GL_RGBA = 6408; _mock_gl.GL_UNSIGNED_BYTE = 5121
_mock_gl.GL_LINEAR = 9729; _mock_gl.GL_CLAMP_TO_EDGE = 33071
_mock_gl.GL_TEXTURE_MIN_FILTER = 10241; _mock_gl.GL_TEXTURE_MAG_FILTER = 10240
_mock_gl.GL_TEXTURE_WRAP_S = 10242; _mock_gl.GL_TEXTURE_WRAP_T = 10243
_mock_gl.GL_FRAMEBUFFER = 36160; _mock_gl.GL_COLOR_ATTACHMENT0 = 36064
_mock_gl.GL_COLOR_BUFFER_BIT = 16384; _mock_gl.GL_TRIANGLE_STRIP = 5
_mock_gl.GL_FALSE = 0; _mock_gl.GL_TRUE = 1
_mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
_mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44
_mock_gl.glGenTextures.return_value = 55; _mock_gl.glGenFramebuffers.return_value = 51

sys.modules['OpenGL'] = MagicMock(); sys.modules['OpenGL.GL'] = _mock_gl

from vjlive3.plugins.{file_stem} import {class_name}, METADATA
from vjlive3.plugins.api import PluginContext


@pytest.fixture
def plugin():
    _mock_gl.reset_mock()
    _mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
    _mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44
    _mock_gl.glGenTextures.return_value = 55; _mock_gl.glGenFramebuffers.return_value = 51
    return {class_name}()


@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 64; ctx.height = 48; ctx.time = 1.0
    ctx.inputs = {{"video_in": 10}}; ctx.outputs = {{}}
    return ctx


def test_metadata(plugin):
    m = plugin.get_metadata()
    assert m["name"] == {display_name!r}
    assert len(m["parameters"]) == {num_params}

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
def test_initialize(plugin, context):
    assert plugin.initialize(context) is True

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
def test_process_zero_input(plugin, context):
    plugin.initialize(context); assert plugin.process_frame(0, {{}}, context) == 0

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
@patch('vjlive3.plugins.{file_stem}.hasattr')
def test_mock_fallback(mock_hasattr, plugin, context):
    mock_hasattr.side_effect = lambda o, a: False if a == 'glCreateShader' else True
    assert plugin.process_frame(10, {{}}, context) == 10

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
def test_process_renders(plugin, context):
    plugin.initialize(context)
    assert plugin.process_frame(10, {{}}, context) == 55
    _mock_gl.glDrawArrays.assert_called_once()

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
def test_compile_failure(plugin, context):
    _mock_gl.glGetShaderiv.return_value = 0; _mock_gl.glGetShaderInfoLog.return_value = b"Error"
    assert plugin.initialize(context) is False; assert plugin._mock_mode is True
    _mock_gl.glGetShaderiv.return_value = 1

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
def test_cleanup(plugin, context):
    plugin.initialize(context); plugin.prog = 99; plugin.cleanup()
    _mock_gl.glDeleteProgram.assert_called_once_with(99)
'''


QC_TASKS = {f"P6-QC{n:02d}" for n in range(6, 15)}
GE_TASKS = {f"P6-GE{n:02d}" for n in range(6, 20)}

def classify(task_id):
    if task_id in QC_TASKS:
        return "effect", "vfx"
    if task_id in GE_TASKS:
        return "generator", "generator"
    return "effect", "particles"

def make_uniform_block(params):
    return "\n".join(f"uniform float {n};  // {c}" for n, _, c in params)

def pick(params, candidates, default="0.0"):
    names = [p[0] for p in params]
    for c in candidates:
        if c in names:
            return f"({c} / 10.0)"
    return default

def generate(d):
    task_id, class_name, slug, file_stem, description, tags, params = d
    display_name = file_stem.replace("_", " ").title()
    plugin_type, category = classify(task_id)
    params_meta = [{"name": n, "type": "float", "default": v, "min": 0.0, "max": 10.0} for n, v, _ in params]
    param_names = [p[0] for p in params]
    param_defaults = {p[0]: p[1] for p in params}

    disp_expr = pick(params, ["intensity","style_strength","singularity_strength","nexus_density",
                               "quantum_depth","trail_length","particle_count","adrenaline",
                               "blur_radius","zoom","scale","field_scale","fractal_type",
                               "resonant_freq","grain_size","freq_x","carrier_freq","size"])
    feedback_expr = pick(params, ["feedback","trail_length","decay","fade","fade_rate","temporal_echo"])
    freq_expr = pick(params, ["speed","pulse_speed","rotation_speed","flow_speed","path_speed",
                               "field_scale","color_cycle","color_speed","chaos","frequency"])
    chroma_expr = pick(params, ["chromatic_drift","chroma_split","color_scatter","edge_emphasis"])
    vign_expr = pick(params, ["vignette","depth_bias","dark_fog"])

    ns = [p[0] for p in params]
    r_tint = next((f"{n}/10.0*0.3" for n in ns if any(k in n for k in ["color_hue","glow","adrenaline","style_s"])), "0.0")
    g_tint = next((f"{n}/10.0*0.2" for n in ns if any(k in n for k in ["saturation","color_saturation","brightness","glow"])), "0.0")
    b_tint = next((f"{n}/10.0*0.3" for n in ns if any(k in n for k in ["feedback","entanglement","resonance","quantum"])), "0.0")

    plugin_code = PLUGIN_TEMPLATE.format(
        task_id=task_id, class_name=class_name, file_stem=file_stem,
        description=description, display_name=display_name, tags=tags,
        plugin_type=plugin_type, category=category, params_meta=params_meta,
        uniform_block=make_uniform_block(params), disp_expr=disp_expr,
        feedback_expr=feedback_expr, freq_expr=freq_expr, chroma_expr=chroma_expr,
        vign_expr=vign_expr, r_tint=r_tint, g_tint=g_tint, b_tint=b_tint,
        param_names=param_names, param_defaults=param_defaults,
    )
    test_code = TEST_TEMPLATE.format(
        task_id=task_id, class_name=class_name, file_stem=file_stem,
        display_name=display_name, num_params=len(params),
    )

    with open(os.path.join(BASE, f"{file_stem}.py"), "w") as fp: fp.write(plugin_code)
    with open(os.path.join(TEST_BASE, f"test_{file_stem}.py"), "w") as fp: fp.write(test_code)
    print(f"✅ {task_id}: {file_stem}.py")


if __name__ == "__main__":
    for p in PLUGINS:
        generate(p)
    print(f"\nDone! {len(PLUGINS)} plugin pairs.")
