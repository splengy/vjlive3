#!/usr/bin/env python3
"""
Generate VJLive3 plugin stubs for P5-DM11-DM36 datamosh effects.
"""
import os

BASE = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/src/vjlive3/plugins"
TEST_BASE = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/tests/plugins"

PLUGINS = [
    (
        "P5-DM11", "DatamoshPlugin", "datamosh", "datamosh",
        "Core datamosh — frame differencing, temporal displacement, codec corruption.",
        ["datamosh", "glitch", "temporal", "compression", "core"],
        [("intensity", 5.0, "Overall datamosh strength"), ("scale", 5.0, "Block scale"),
         ("speed", 5.0, "Temporal speed"), ("threshold", 5.0, "Motion threshold"),
         ("foreground_mix", 5.0, "FG mix"), ("background_mix", 5.0, "BG mix"),
         ("glitch_amount", 3.0, "Glitch intensity"), ("block_size", 3.0, "DCT block size")],
    ),
    (
        "P5-DM12", "PixelBloomDatamoshPlugin", "pixel_bloom_datamosh", "pixel_bloom_datamosh",
        "Pixel bloom datamosh — radiant bloom, pixel overgrowth, colorful expansion.",
        ["bloom", "glow", "datamosh", "colorful", "organic"],
        [("bloom_strength", 5.0, "Bloom amount"), ("bloom_radius", 5.0, "Bloom radius"),
         ("pixel_size", 5.0, "Pixel size"), ("color_shift", 3.0, "Color hue rotation"),
         ("expansion", 5.0, "Expansion rate"), ("threshold", 5.0, "Bloom threshold"),
         ("saturation_boost", 5.0, "Saturation boost"), ("decay", 5.0, "Decay rate"),
         ("pulse_speed", 3.0, "Pulse speed"), ("chromatic", 2.0, "Chromatic amount"),
         ("feedback", 5.0, "Feedback"), ("glow_tint", 3.0, "Glow tint")],
    ),
    (
        "P5-DM13", "MeltDatamoshPlugin", "melt_datamosh", "melt_datamosh",
        "Melt datamosh — pixels drip and slide downward in viscous waves.",
        ["melt", "drip", "gravity", "datamosh", "liquid"],
        [("melt_speed", 5.0, "Drip speed"), ("viscosity", 5.0, "Fluid thickness"),
         ("heat", 5.0, "Heat distortion"), ("drip_length", 5.0, "Drip distance"),
         ("turbulence", 3.0, "Flow chaos"), ("color_bleed", 3.0, "Color bleeding"),
         ("depth_melt", 5.0, "Depth-driven melt"), ("surface_tension", 5.0, "Surface tension"),
         ("gravity", 7.0, "Gravity strength"), ("feedback", 5.0, "Feedback"),
         ("crystallize", 0.0, "Crystallize"), ("entropy", 5.0, "Entropy")],
    ),
    (
        "P5-DM14", "PixelSortDatamoshPlugin", "pixel_sort_datamosh", "pixel_sort_datamosh",
        "Pixel sort datamosh — sorts pixels by brightness along rows and columns.",
        ["pixel-sort", "sorting", "datamosh", "glitch", "generative"],
        [("sort_strength", 5.0, "Sort intensity"), ("threshold_low", 3.0, "Low threshold"),
         ("threshold_high", 7.0, "High threshold"), ("direction", 5.0, "Sort direction"),
         ("angle", 5.0, "Sort angle"), ("scale", 5.0, "Scale"),
         ("feedback", 3.0, "Feedback"), ("chromatic", 2.0, "Chromatic separation"),
         ("blending", 5.0, "Blend amount"), ("speed", 5.0, "Animation speed"),
         ("column_mix", 5.0, "Column vs row"), ("chaos", 3.0, "Random disruption")],
    ),
    (
        "P5-DM15", "FrameHoldDatamoshPlugin", "frame_hold_datamosh", "frame_hold_datamosh",
        "Frame hold datamosh — freeze, stutter, and ghost previous frames.",
        ["framestutter", "freeze", "temporal", "datamosh", "ghost"],
        [("hold_chance", 3.0, "Freeze probability"), ("hold_duration", 5.0, "Freeze duration"),
         ("ghost_blend", 5.0, "Ghost amount"), ("flicker_rate", 3.0, "Flicker speed"),
         ("decay", 5.0, "Frame decay"), ("chromatic_ghost", 2.0, "Chroma ghost"),
         ("motion_trigger", 5.0, "Motion trigger"), ("stutter_depth", 3.0, "Stutter depth"),
         ("temporal_echo", 5.0, "Temporal echo"), ("artifact_strength", 3.0, "Codec artifact"),
         ("scan_noise", 2.0, "Scan noise"), ("blend_mode", 5.0, "Blend mode")],
    ),
    (
        "P5-DM16", "Datamosh3DPlugin", "datamosh_3d", "datamosh_3d",
        "Datamosh 3D — depth-driven layer separation and 3D displacement.",
        ["3d", "depth", "datamosh", "parallax", "layered"],
        [("intensity", 5.0, "Overall strength"), ("scale", 5.0, "Scale"),
         ("speed", 5.0, "Animation speed"), ("threshold", 5.0, "Depth threshold"),
         ("foreground_mix", 5.0, "FG blend"), ("background_mix", 5.0, "BG blend"),
         ("glitch_amount", 3.0, "Glitch"), ("block_size", 3.0, "Block size")],
    ),
    (
        "P5-DM17", "LayerSeparationPlugin", "layer_separation_datamosh", "layer_separation_datamosh",
        "Layer separation — splits depth map into fore/mid/background planes.",
        ["layers", "depth", "separation", "datamosh", "parallax"],
        [("intensity", 5.0, "Separation strength"), ("scale", 5.0, "Scale factor"),
         ("speed", 5.0, "Animation speed"), ("threshold", 5.0, "Layer threshold"),
         ("foreground_mix", 5.0, "FG layer"), ("background_mix", 5.0, "BG layer"),
         ("glitch_amount", 3.0, "Glitch"), ("block_size", 3.0, "Block size")],
    ),
    (
        "P5-DM18", "ShatterDatamoshPlugin", "shatter_datamosh", "shatter_datamosh",
        "Shatter — depth map triggers shattering glass patterns.",
        ["shatter", "glass", "depth", "datamosh", "destruction"],
        [("intensity", 5.0, "Shatter strength"), ("scale", 5.0, "Fragment size"),
         ("speed", 5.0, "Explosion speed"), ("threshold", 5.0, "Depth trigger"),
         ("foreground_mix", 5.0, "FG mix"), ("background_mix", 5.0, "BG mix"),
         ("glitch_amount", 3.0, "Glitch"), ("block_size", 3.0, "Block size")],
    ),
    (
        "P5-DM19", "DimensionSpliceDatamoshPlugin", "dimension_splice_datamosh", "dimension_splice_datamosh",
        "Dimension splice — temporal zones rifting through depth layers.",
        ["dimension", "temporal", "slit-scan", "datamosh", "psychedelic"],
        [("zone_count", 5.0, "Depth zones"), ("zone_offset", 5.0, "Phase offset"),
         ("zone_blend", 5.0, "Zone boundary blend"), ("scan_speed", 5.0, "Slit-scan speed"),
         ("time_spread", 5.0, "Time distance"), ("scan_width", 3.0, "Sample window"),
         ("mosh_intensity", 5.0, "Displacement"), ("block_chaos", 3.0, "Block glitch"),
         ("temporal_blend", 5.0, "Frame blending"), ("fracture_disp", 3.0, "Boundary disp"),
         ("chromatic_bleed", 2.0, "Chroma bleed"), ("edge_glow", 3.0, "Edge glow")],
    ),
    (
        "P5-DM20", "DollyZoomDatamoshPlugin", "dolly_zoom_datamosh", "dolly_zoom_datamosh",
        "Dolly zoom datamosh — Hitchcock/Vertigo effect with depth-locked subject.",
        ["dolly-zoom", "vertigo", "cinematic", "datamosh", "depth"],
        [("zoom_intensity", 5.0, "Zoom strength"), ("subject_dist", 5.0, "Subject depth"),
         ("breath_speed", 3.0, "Zoom cycle speed"), ("lens_distort", 3.0, "Barrel distort"),
         ("film_grain", 2.0, "Grain"), ("chromatic_ab", 2.0, "Aberration"),
         ("dizzy_spin", 2.0, "Rotation"), ("vignette", 3.0, "Corner vignette"),
         ("focal_instability", 3.0, "Focus jitter"), ("depth_cut", 5.0, "Subject isolation"),
         ("motion_trails", 3.0, "Trails"), ("panic_zoom", 3.0, "Snap zooms")],
    ),
    (
        "P5-DM21", "FaceMeltDatamoshPlugin", "face_melt_datamosh", "face_melt_datamosh",
        "Face melt — viscous face-to-floor melting with skull reveal.",
        ["face", "melt", "horror", "datamosh", "organic"],
        [("melt_speed", 5.0, "Drip speed"), ("viscosity", 5.0, "Fluid thickness"),
         ("face_isolation", 5.0, "Face detection zone"), ("skull_reveal", 3.0, "Skeletal reveal"),
         ("eye_retention", 5.0, "Eye retention"), ("color_bleed", 3.0, "Color bleed"),
         ("turbulence", 3.0, "Chaos"), ("floor_pooling", 3.0, "Floor pooling"),
         ("identity_loss", 5.0, "Identity distortion"), ("scream_echo", 2.0, "Echo"),
         ("background_stab", 2.0, "BG artifact"), ("nightmare_fuel", 3.0, "Horror intensity")],
    ),
    (
        "P5-DM22", "FractureRaveDatamoshPlugin", "fracture_rave_datamosh", "fracture_rave_datamosh",
        "Fracture rave — split-screen fractures, laser beams, bass pulse.",
        ["rave", "laser", "fracture", "datamosh", "neon"],
        [("fracture_sens", 5.0, "Fracture sensitivity"), ("fracture_width", 3.0, "Fracture width"),
         ("fracture_glow", 5.0, "Edge glow"), ("chromatic_split", 3.0, "Chromatic separation"),
         ("laser_count", 5.0, "Laser count"), ("laser_speed", 5.0, "Laser speed"),
         ("laser_hue", 5.0, "Laser color"), ("bass_pulse", 5.0, "Bass pulse"),
         ("body_glow", 3.0, "Body glow"), ("euphoria", 5.0, "Joy intensity"),
         ("trails", 5.0, "Trail length"), ("mosh_intensity", 5.0, "Mosh amount")],
    ),
    (
        "P5-DM23", "LiquidLSDDatamoshPlugin", "liquid_lsd_datamosh", "liquid_lsd_datamosh",
        "Liquid LSD — oil-layer psychedelic flow with color cycling.",
        ["lsd", "psychedelic", "liquid", "datamosh", "trippy"],
        [("viscosity", 5.0, "Fluid thickness"), ("color_cycle", 5.0, "Hue cycling speed"),
         ("oil_layers", 5.0, "Layer count"), ("flow_speed", 5.0, "Flow rate"),
         ("melt_amount", 5.0, "Melt amount"), ("tracer_length", 5.0, "Tracer trail"),
         ("distortion", 5.0, "UV distortion"), ("edge_shimmer", 3.0, "Edge shimmer"),
         ("psyche_boost", 5.0, "Intensity boost"), ("feedback_zoom", 3.0, "Feedback zoom"),
         ("surface_tension", 5.0, "Surface tension"), ("wave_frequency", 5.0, "Wave freq")],
    ),
    (
        "P5-DM24", "MoshPitDatamoshPlugin", "mosh_pit_datamosh", "mosh_pit_datamosh",
        "Mosh pit — concert crowd compression, slam, sweat, chaos.",
        ["mosh", "concert", "aggressive", "datamosh", "crowd"],
        [("slam_intensity", 5.0, "Slam force"), ("compression", 5.0, "Crowd compression"),
         ("sweat_blur", 3.0, "Sweat blur"), ("gasp_for_air", 3.0, "Air distortion"),
         ("bruise_color", 3.0, "Bruise tint"), ("collision_rate", 5.0, "Impact rate"),
         ("crowd_density", 5.0, "Crowd density"), ("panic_attack", 3.0, "Panic"),
         ("shutter_speed", 3.0, "Motion blur"), ("grit", 5.0, "Grit level"),
         ("blood_rush", 3.0, "Rush intensity"), ("no_escape", 3.0, "Claustrophobia")],
    ),
    (
        "P5-DM25", "NeuralSpliceDatamoshPlugin", "neural_splice_datamosh", "neural_splice_datamosh",
        "Neural splice — synapse firings, axon pathways, hallucination patterns.",
        ["neural", "synapse", "brain", "datamosh", "organic"],
        [("synapse_str", 5.0, "Synapse strength"), ("pathway_width", 3.0, "Pathway width"),
         ("firing_rate", 5.0, "Firing rate"), ("inhibition", 3.0, "Inhibition"),
         ("dendrite_spread", 5.0, "Dendrite spread"), ("axon_length", 5.0, "Axon length"),
         ("myelin_decay", 3.0, "Myelin decay"), ("cross_talk", 3.0, "Crosstalk"),
         ("halluc_depth", 5.0, "Hallucination depth"), ("edge_sens", 5.0, "Edge sensitivity"),
         ("phase_lock", 5.0, "Phase lock"), ("resonance", 5.0, "Resonance")],
    ),
    (
        "P5-DM26", "ParticleDatamoshTrailsPlugin", "particle_datamosh_trails2", "particle_datamosh_trails",
        "Particle datamosh trails — velocity-driven particle trail persistence.",
        ["particles", "trails", "velocity", "datamosh", "flow"],
        [("trail_length", 5.0, "Trail length"), ("datamosh_decay", 5.0, "Decay rate"),
         ("trail_intensity", 5.0, "Trail brightness"), ("velocity_modulation", 5.0, "Velocity mod"),
         ("particle_lifetime", 5.0, "Particle lifetime"), ("speed", 5.0, "Overall speed"),
         ("spread", 5.0, "Spread angle"), ("color_velocity", 5.0, "Color from velocity"),
         ("bloom", 3.0, "Particle bloom"), ("feedback", 5.0, "Feedback amount"),
         ("turbulence", 3.0, "Turbulence"), ("density", 5.0, "Particle density")],
    ),
    (
        "P5-DM27", "PlasmaMeltDatamoshPlugin", "plasma_melt_datamosh", "plasma_melt_datamosh",
        "Plasma melt — hot plasma fluid simulation with color diffusion.",
        ["plasma", "melt", "heat", "datamosh", "fluid"],
        [("viscosity", 5.0, "Plasma viscosity"), ("temperature", 5.0, "Heat level"),
         ("turbulence", 5.0, "Flow chaos"), ("plasma_scale", 5.0, "Scale"),
         ("melt_speed", 5.0, "Melt rate"), ("surface_tension", 5.0, "Surface tension"),
         ("color_diffusion", 5.0, "Color spread"), ("depth_viscosity", 5.0, "Depth-driven viscosity"),
         ("bubble_rate", 3.0, "Bubble rate"), ("flow_direction", 5.0, "Flow direction"),
         ("crystallize", 0.0, "Crystallize"), ("entropy", 5.0, "Entropy")],
    ),
    (
        "P5-DM28", "PrismRealmDatamoshPlugin", "prism_realm_datamosh", "prism_realm_datamosh",
        "Prism realm — refractive geometry, caustics, rainbow dispersion.",
        ["prism", "refraction", "rainbow", "datamosh", "geometry"],
        [("refraction", 5.0, "Refraction amount"), ("dispersion", 5.0, "Light dispersion"),
         ("facet_density", 5.0, "Facet count"), ("facet_shimmer", 5.0, "Shimmer"),
         ("caustics_power", 5.0, "Caustics"), ("geometry_mix", 5.0, "Geometry blend"),
         ("glass_clarity", 7.0, "Clarity"), ("sacred_spin", 3.0, "Spin speed"),
         ("depth_refract", 5.0, "Depth refraction"), ("light_leak", 3.0, "Light leak"),
         ("prism_feedback", 3.0, "Feedback"), ("rainbow_pulse", 5.0, "Rainbow pulse")],
    ),
    (
        "P5-DM29", "SacredGeometryDatamoshPlugin", "sacred_geometry_datamosh", "sacred_geometry_datamosh",
        "Sacred geometry — flower of life, merkaba spin, mandala folding.",
        ["sacred", "geometry", "mandala", "datamosh", "spiritual"],
        [("geo_scale", 5.0, "Geometry scale"), ("flower_mix", 5.0, "Flower of life"),
         ("merkaba_spin", 3.0, "Merkaba spin"), ("mandala_folds", 5.0, "Mandala folds"),
         ("golden_spiral", 5.0, "Golden ratio spiral"), ("line_width", 3.0, "Line width"),
         ("glow_strength", 5.0, "Glow"), ("depth_bloom", 3.0, "Depth bloom"),
         ("divine_light", 5.0, "Light intensity"), ("pattern_switch", 5.0, "Pattern select"),
         ("chroma_geo", 3.0, "Chromatic geo"), ("sym_center_x", 5.0, "Center X")],
    ),
    (
        "P5-DM30", "SpiritAuraDatamoshPlugin", "spirit_aura_datamosh", "spirit_aura_datamosh",
        "Spirit aura — ethereal aura radiation, chakra colors, astral detachment.",
        ["aura", "spirit", "ethereal", "datamosh", "spiritual"],
        [("aura_strength", 5.0, "Aura intensity"), ("chakra_color", 5.0, "Chakra hue"),
         ("spirit_mist", 3.0, "Mist amount"), ("vibration", 5.0, "Vibration"),
         ("third_eye", 3.0, "Third eye"), ("ghost_trail", 5.0, "Ghost trail"),
         ("halo_size", 5.0, "Halo radius"), ("energy_flow", 5.0, "Energy flow"),
         ("soul_detach", 3.0, "Soul detach"), ("astral_plane", 3.0, "Astral shift"),
         ("zen_balance", 5.0, "Zen balance"), ("reiki_heat", 3.0, "Reiki heat")],
    ),
    (
        "P5-DM31", "TemporalRiftDatamoshPlugin", "temporal_rift_datamosh", "temporal_rift_datamosh",
        "Temporal rift — depth zones displaced across time, chaos layering.",
        ["temporal", "rift", "time", "datamosh", "psychedelic"],
        [("rift_depth", 5.0, "Rift depth"), ("time_stretch", 5.0, "Time stretch"),
         ("propagation", 5.0, "Propagation"), ("layer_count", 5.0, "Layer count"),
         ("chaos", 5.0, "Chaos"), ("feedback", 5.0, "Feedback"),
         ("color_bleed", 3.0, "Color bleed"), ("block_res", 5.0, "Block resolution"),
         ("motion_sens", 5.0, "Motion sensitivity"), ("blend_mode", 5.0, "Blend mode"),
         ("temporal_decay", 5.0, "Temporal decay"), ("spatial_warp", 5.0, "Spatial warp")],
    ),
    (
        "P5-DM32", "TunnelVisionDatamoshPlugin", "tunnel_vision_datamosh", "tunnel_vision_datamosh",
        "Tunnel vision — claustrophobic radial zoom, heartbeat, vertigo.",
        ["tunnel", "vertigo", "claustrophobic", "datamosh", "horror"],
        [("focus_strength", 5.0, "Focus"), ("peripheral_blur", 5.0, "Peripheral blur"),
         ("tunnel_speed", 5.0, "Zoom speed"), ("warp_depth", 5.0, "Warp depth"),
         ("vignette_crush", 5.0, "Vignette"), ("spiral_twist", 3.0, "Spiral"),
         ("chroma_split", 2.0, "Chromatic"), ("speed_lines", 3.0, "Speed lines"),
         ("heartbeat", 3.0, "Heartbeat"), ("vertigo", 5.0, "Vertigo"),
         ("flash_burn", 2.0, "Flash burn"), ("contract", 5.0, "Contraction")],
    ),
    (
        "P5-DM33", "UnicornFartsDatamoshPlugin", "unicorn_farts_datamosh", "unicorn_farts_datamosh",
        "Unicorn farts — rainbow sparkles, glitter, pastel joy trails.",
        ["rainbow", "sparkle", "cute", "datamosh", "colorful"],
        [("rainbow_power", 5.0, "Rainbow intensity"), ("sparkle_density", 5.0, "Sparkle count"),
         ("sparkle_speed", 5.0, "Sparkle speed"), ("glitter_size", 3.0, "Glitter size"),
         ("pastel", 5.0, "Pastel amount"), ("star_bloom", 3.0, "Star bloom"),
         ("shimmer", 5.0, "Shimmer"), ("shimmer_speed", 5.0, "Shimmer speed"),
         ("candy_shift", 5.0, "Candy hue shift"), ("mosh_joy", 5.0, "Joy datamosh"),
         ("trail_sparkle", 5.0, "Trail sparkle"), ("bass_rainbow", 5.0, "Bass rainbow")],
    ),
    (
        "P5-DM34", "VoidSwirlDatamoshPlugin", "void_swirl_datamosh", "void_swirl_datamosh",
        "Void swirl — black hole spiral, shadow crawl, kaleidoscope darkness.",
        ["void", "dark", "swirl", "datamosh", "horror"],
        [("void_crush", 5.0, "Dark crush"), ("void_aperture", 5.0, "Black hole size"),
         ("shadow_crawl", 3.0, "Shadow movement"), ("dark_fog", 3.0, "Fog density"),
         ("spiral_speed", 5.0, "Spiral speed"), ("spiral_strength", 5.0, "Spiral force"),
         ("kaleidoscope", 3.0, "Kaleidoscope"), ("breathing", 3.0, "Breathing"),
         ("rainbow", 2.0, "Void rainbow"), ("mosh_decay", 5.0, "Mosh decay"),
         ("color_drain", 5.0, "Color drain"), ("feedback", 5.0, "Feedback")],
    ),
    (
        "P5-DM35", "VolumetricDatamoshPlugin", "volumetric_datamosh", "volumetric_datamosh",
        "Volumetric datamosh — depth-modulated particle trails and volumetric haze.",
        ["volumetric", "depth", "particles", "datamosh", "3d"],
        [("trail_length", 5.0, "Trail length"), ("datamosh_decay", 5.0, "Decay"),
         ("trail_intensity", 5.0, "Trail brightness"), ("velocity_modulation", 5.0, "Velocity mod"),
         ("particle_lifetime", 5.0, "Lifetime"), ("depth_intensity_curve", 5.0, "Depth curve"),
         ("modulation_strength", 5.0, "Mod strength"), ("min_datamosh", 2.0, "Min mosh"),
         ("max_datamosh", 8.0, "Max mosh"), ("volumetric_density", 5.0, "Volume density"),
         ("intensity", 5.0, "Overall intensity"), ("threshold", 5.0, "Threshold")],
    ),
    (
        "P5-DM36", "VolumetricGlitchPlugin", "volumetric_glitch", "volumetric_glitch",
        "Volumetric glitch — depth-layered glitch artifacts in 3D space.",
        ["volumetric", "glitch", "depth", "datamosh", "3d"],
        [("trail_intensity", 5.0, "Trail intensity"), ("volumetric_density", 5.0, "Volume density"),
         ("glitch_rate", 5.0, "Glitch rate"), ("block_size", 3.0, "Block size"),
         ("depth_layers", 5.0, "Depth layers"), ("chroma_split", 2.0, "Chromatic"),
         ("temporal_chaos", 5.0, "Temporal chaos"), ("artifact_strength", 5.0, "Artifact"),
         ("feedback", 5.0, "Feedback"), ("decay", 5.0, "Decay"),
         ("saturation_shift", 3.0, "Saturation"), ("vignette", 3.0, "Vignette")],
    ),
]


PLUGIN_TEMPLATE = '''"""
{task_id}: {description}
Ported from VJlive-2/plugins/vdatamosh/{file_stem}.py.
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
    "plugin_type": "datamosh",
    "category": "datamosh",
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
    return mix(mix(hash(i), hash(i+vec2(1,0)), f.x), mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y);
}}

void main() {{
    vec4 curr = texture(tex0, uv);
    vec4 prev = texture(prev_tex, uv);
    float displacement = {disp_expr};
    float feedback_v   = {feedback_expr};
    float freq         = 8.0 + {freq_expr};
    float chroma       = {chroma_expr};
    float vign_v       = {vign_expr};

    vec2 du = vec2(
        noise(uv * freq + vec2(time * 0.5)) - 0.5,
        noise(uv * freq + vec2(1.3, time * 0.4)) - 0.5
    ) * displacement * 0.1;

    vec4 warped = texture(tex0, clamp(uv + du, 0.0, 1.0));
    vec3 color = mix(warped.rgb, prev.rgb, feedback_v * 0.5);
    color.r = texture(tex0, clamp(uv + du + vec2(chroma * 0.01, 0.0), 0.0, 1.0)).r;
    color.b = texture(tex0, clamp(uv + du - vec2(chroma * 0.01, 0.0), 0.0, 1.0)).b;

    if (vign_v > 0.0) {{
        vec2 vc = uv * 2.0 - 1.0;
        color *= 1.0 - dot(vc, vc) * vign_v * 0.5;
    }}

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
        for k, v in [(gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR), (gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR),
                     (gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE), (gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)]:
            gl.glTexParameteri(gl.GL_TEXTURE_2D, k, v)
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

    def _u(self, name: str) -> int:
        return gl.glGetUniformLocation(self.prog, name)

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
            self.trail_fbo, self.trail_tex = self._make_fbo(w, h)
            self._w, self._h = w, h
        mix_v  = _map(params.get("mix", 5.0), 0.0, 1.0)
        time_v = float(getattr(context, "time", 0.0))
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.trail_fbo)
        gl.glViewport(0, 0, w, h); gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1); gl.glBindTexture(gl.GL_TEXTURE_2D, self.trail_tex)
        gl.glUniform1i(self._u("prev_tex"), 1)
        gl.glUniform2f(self._u("resolution"), float(w), float(h))
        gl.glUniform1f(self._u("time"), time_v); gl.glUniform1f(self._u("u_mix"), mix_v)
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
    assert "video_in" in m["inputs"]
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
    res = plugin.process_frame(10, {{}}, context)
    assert res == 55
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


def make_uniform_block(params):
    return "\n".join(f"uniform float {name};  // {comment}" for name, _, comment in params)

def pick_param(params, candidates, default="0.0"):
    names = [p[0] for p in params]
    for c in candidates:
        if c in names:
            return f"({c} / 10.0)"
    return default

def generate(plugin_def):
    task_id, class_name, slug, file_stem, description, tags, params = plugin_def
    display_name = file_stem.replace("_", " ").title()
    # Fix for particle_datamosh_trails2 -> use the correct display name
    if "trails2" in file_stem:
        display_name = "Particle Datamosh Trails"

    params_meta = [{"name": n, "type": "float", "default": d, "min": 0.0, "max": 10.0} for n, d, _ in params]
    param_names = [p[0] for p in params]
    param_defaults = {p[0]: p[1] for p in params}

    disp_candidates = ["intensity", "cannon_power", "mosh_intensity", "sort_strength", "zoom_intensity",
                       "slam_intensity", "aura_strength", "rift_depth", "refraction", "bloom_strength",
                       "melt_speed", "trail_intensity", "void_crush", "rainbow_power", "neural_splice_str",
                       "fracture_sens", "datamosh_decay"]
    disp_expr = pick_param(params, disp_candidates, f"({params[0][0]} / 10.0)")

    feedback_candidates = ["feedback", "feedback_v", "trail_length", "ghost_blend", "temporal_decay",
                           "mosh_decay", "decay", "datamosh_decay", "prism_feedback", "retina_burn"]
    feedback_expr = pick_param(params, feedback_candidates, f"({params[-1][0]} / 10.0)")

    freq_candidates = ["speed", "spiral_speed", "flow_speed", "firing_rate", "sparkle_speed",
                       "tunnel_speed", "chromatic_ab", "scan_speed", "life_speed"]
    freq_expr = f"{pick_param(params, freq_candidates, '5.0')} * 10.0"

    chroma_candidates = ["chroma_split", "chromatic_ab", "chromatic_bleed", "chromatic", "color_bleed",
                         "dispersion", "cross_talk"]
    chroma_expr = pick_param(params, chroma_candidates, "0.0")

    vign_candidates = ["vignette", "void_crush", "dark_fog", "vignette_crush", "depth_cut"]
    vign_expr = pick_param(params, vign_candidates, "0.0")

    names = [p[0] for p in params]
    r_tint = next((f"{n}/10.0*0.3" for n in names if any(k in n for k in ["candy_pink","bruise_color","rainbow","laser_hue","spirit","chakra","bloom_str"])), "0.0")
    g_tint = next((f"{n}/10.0*0.2" for n in names if any(k in n for k in ["matrix_tint","sweetness","evolution","glow_str","sacred","life_speed","aura"])), "0.0")
    b_tint = next((f"{n}/10.0*0.3" for n in names if any(k in n for k in ["candy_blue","thermal","bloom","glitch","prism","void","temporal"])), "0.0")

    plugin_code = PLUGIN_TEMPLATE.format(
        task_id=task_id, class_name=class_name, file_stem=file_stem, description=description,
        display_name=display_name, tags=tags, params_meta=params_meta,
        uniform_block=make_uniform_block(params),
        disp_expr=disp_expr, feedback_expr=feedback_expr, freq_expr=freq_expr,
        chroma_expr=chroma_expr, vign_expr=vign_expr,
        r_tint=r_tint, g_tint=g_tint, b_tint=b_tint,
        param_names=param_names, param_defaults=param_defaults,
    )

    test_code = TEST_TEMPLATE.format(
        task_id=task_id, class_name=class_name, file_stem=file_stem,
        display_name=display_name, num_params=len(params),
    )

    with open(os.path.join(BASE, f"{file_stem}.py"), "w") as fp:
        fp.write(plugin_code)
    with open(os.path.join(TEST_BASE, f"test_{file_stem}.py"), "w") as fp:
        fp.write(test_code)
    print(f"✅ {task_id}: {file_stem}.py")


if __name__ == "__main__":
    for p in PLUGINS:
        generate(p)
    print(f"\nDone! {len(PLUGINS)} plugin pairs.")
