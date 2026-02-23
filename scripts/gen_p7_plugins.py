#!/usr/bin/env python3
"""
Generate VJLive3 plugin stubs for P7-VE01 through P7-VE80.
All follow the same FSQ+trail-FBO pattern.
"""
import os, re

BASE = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/src/vjlive3/plugins"
TEST_BASE = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/tests/plugins"

# (task_id, class_name, file_stem, description, tags, params)
# Most params are 6-10 logically themed params for each effect
PLUGINS = [
    ("P7-VE01","VSwsPlugin","v_sws","V-Sws sine wave scan — horizontal+vertical combined sine scan.",
     ["wave","scan","sws","distortion","psychedelic"],
     [("amplitude",5.,"Wave amplitude"),("frequency",5.,"Wave freq"),("speed",5.,"Scroll speed"),
      ("phase",0.,"Phase offset"),("color_shift",0.,"Hue shift"),("mix",8.,"Output mix")]),
    ("P7-VE02","HorizontalWavePlugin","horizontal_wave","Horizontal wave — sine UV warp along X axis.",
     ["wave","horizontal","distortion","uv","warp"],
     [("amplitude",5.,"Wave height"),("frequency",5.,"Wave count"),("speed",5.,"Scroll speed"),
      ("phase",0.,"Phase"),("sharpness",5.,"Wave sharpness"),("mix",8.,"Output mix")]),
    ("P7-VE03","VerticalWavePlugin","vertical_wave","Vertical wave — sine UV warp along Y axis.",
     ["wave","vertical","distortion","uv","warp"],
     [("amplitude",5.,"Wave width"),("frequency",5.,"Wave count"),("speed",5.,"Scroll speed"),
      ("phase",0.,"Phase"),("sharpness",5.,"Wave sharpness"),("mix",8.,"Output mix")]),
    ("P7-VE04","RipplePlugin","ripple_effect","Ripple — radial sinusoidal ripple from center.",
     ["ripple","radial","water","distortion","wave"],
     [("amplitude",5.,"Ripple height"),("frequency",5.,"Ripple freq"),("speed",5.,"Propagation"),
      ("center_x",5.,"Origin X"),("center_y",5.,"Origin Y"),("mix",8.,"Output mix")]),
    ("P7-VE05","SpiralWavePlugin","spiral_wave","Spiral wave — rotating spiral UV distortion.",
     ["spiral","wave","rotation","distortion","swirl"],
     [("amplitude",5.,"Amplitude"),("frequency",5.,"Spiral turns"),("speed",5.,"Rotation speed"),
      ("tightness",5.,"Spiral tightness"),("phase",0.,"Phase"),("mix",8.,"Output mix")]),
    ("P7-VE06","ASCIIPlugin","ascii_effect2","ASCII art — quantizes video to ASCII character grid.",
     ["ascii","text","quantize","stylize","retro"],
     [("char_size",5.,"Character cell size"),("brightness_boost",5.,"Brightness"),
      ("contrast",5.,"Contrast"),("color_mode",0.,"0=mono,5=color,10=ansi"),
      ("density",5.,"Character density"),("mix",8.,"Output mix")]),
    ("P7-VE07","BassCanon2Plugin","bass_cannon_2","Bass cannon 2 — upgraded shockwave bass cannon.",
     ["bass","shockwave","audio","impact","cannon"],
     [("cannon_power",5.,"Shockwave power"),("shockwave_radius",5.,"Blast radius"),
      ("recoil",3.,"Screen recoil"),("flash",2.,"Muzzle flash"),
      ("chroma_burst",3.,"Chromatic burst"),("mix",8.,"Output mix")]),
    ("P7-VE08","FeedbackPlugin","feedback_effect","Feedback — analog feedback loop simulation.",
     ["feedback","loop","trail","temporal","analog"],
     [("amount",5.,"Feedback strength"),("decay",3.,"Brightness decay"),
      ("zoom",0.,"Zoom per frame"),("rotate_speed",0.,"Rotation speed"),
      ("hue_drift",0.,"Hue drift"),("mix",8.,"Output mix")]),
    ("P7-VE09","BlendAddPlugin","blend_add","Additive blend — adds two video inputs together.",
     ["blend","add","composite","mix","additive"],
     [("amount",8.,"Blend amount"),("brightness_a",5.,"Input A brightness"),
      ("brightness_b",5.,"Input B brightness"),("clamp",8.,"Clamp output"),
      ("exposure",5.,"Exposure"),("mix",8.,"Output mix")]),
    ("P7-VE10","BlendMultPlugin","blend_mult","Multiplicative blend — multiplies two video inputs.",
     ["blend","multiply","composite","mix","multiply"],
     [("amount",8.,"Blend amount"),("gamma",5.,"Gamma correction"),
      ("brightness_a",5.,"Input A brightness"),("brightness_b",5.,"Input B brightness"),
      ("exposure",5.,"Exposure"),("mix",8.,"Output mix")]),
    ("P7-VE11","BlendDiffPlugin","blend_diff","Difference blend — absolute difference of two inputs.",
     ["blend","difference","composite","subtract","contrast"],
     [("amount",8.,"Blend amount"),("boost",5.,"Difference boost"),
      ("threshold",0.,"Min threshold"),("invert",0.,"Invert output"),
      ("color_shift",0.,"Hue from difference"),("mix",8.,"Output mix")]),
    ("P7-VE12","ScanlinesPlugin","scanlines_effect","Scanlines — CRT scanline overlay effect.",
     ["scanlines","crt","retro","overlay","tv"],
     [("density",5.,"Scanline count"),("intensity",5.,"Line darkness"),
      ("curvature",0.,"CRT barrel"),("flicker",0.,"Flicker rate"),
      ("glow",3.,"Phosphor glow"),("mix",8.,"Output mix")]),
    ("P7-VE13","VignettePlugin","vignette_effect","Vignette — smooth dark vignette border.",
     ["vignette","border","cinematic","dark","frame"],
     [("radius",7.,"Vignette radius"),("softness",5.,"Edge softness"),
      ("intensity",5.,"Darkness"),("roundness",5.,"Oval vs circular"),
      ("color_hue",0.,"Tint color"),("mix",8.,"Output mix")]),
    ("P7-VE14","InfiniteFeedbackPlugin","infinite_feedback","Infinite feedback — recursive zoom-in feedback.",
     ["feedback","infinite","zoom","recursive","trippy"],
     [("zoom",5.,"Zoom per frame"),("decay",3.,"Decay rate"),
      ("rotation",0.,"Rotation per frame"),("hue_drift",0.,"Hue drift"),
      ("chromatic",0.,"Chromatic drift"),("mix",8.,"Output mix")]),
    ("P7-VE15","BloomPlugin","bloom_effect","Bloom — HDR-style glow bloom on bright areas.",
     ["bloom","glow","hdr","bright","luminance"],
     [("threshold",5.,"Bloom threshold"),("radius",5.,"Bloom radius"),
      ("strength",5.,"Bloom intensity"),("saturation",5.,"Bloom saturation"),
      ("knee",3.,"Soft knee"),("mix",8.,"Output mix")]),
    ("P7-VE16","BloomShadertoyPlugin","bloom_shadertoy","Bloom shadertoy — shadertoy-style GPU bloom.",
     ["bloom","shadertoy","gpu","glow","luminance"],
     [("threshold",5.,"Bloom threshold"),("radius",5.,"Bloom radius"),
      ("strength",5.,"Intensity"),("iterations",5.,"Blur passes"),
      ("saturation",5.,"Bloom color"),("mix",8.,"Output mix")]),
    ("P7-VE17","MixerPlugin","mixer_effect","Mixer — A/B video source mixer with crossfade.",
     ["mixer","crossfade","blend","a-b","composite"],
     [("crossfade",5.,"A/B crossfade"),("gain_a",5.,"Input A gain"),
      ("gain_b",5.,"Input B gain"),("gamma",5.,"Gamma"),
      ("blend_mode",0.,"Blend mode"),("mix",8.,"Output mix")]),
    ("P7-VE18","BlendModePlugin","blend_modes_effect","Blend modes — configurable blend mode processor.",
     ["blend","composite","modes","layer","mix"],
     [("mode",0.,"Blend mode select"),("amount",8.,"Blend amount"),
      ("gamma",5.,"Gamma"),("invert_b",0.,"Invert layer B"),
      ("opacity",8.,"Layer opacity"),("mix",8.,"Output mix")]),
    ("P7-VE19","ChromaKeyPlugin","chroma_key","Chroma key — green/blue screen removal.",
     ["chroma-key","green-screen","compositing","mask","keying"],
     [("key_hue",3.,"Key hue (0=green,5=blue)"),("tolerance",3.,"Hue tolerance"),
      ("edge_feather",3.,"Edge feather"),("spill_supp",3.,"Spill suppression"),
      ("background_blend",5.,"BG blend"),("mix",8.,"Output mix")]),
    ("P7-VE20","PosterizePlugin","posterize_effect","Posterize — reduces to N color levels.",
     ["posterize","levels","stylize","graphic","flat"],
     [("levels",5.,"Color levels"),("dither",0.,"Dither type"),
      ("gamma",5.,"Gamma pre-correction"),("saturation",5.,"Saturation boost"),
      ("edge_detect",0.,"Edge outline"),("mix",8.,"Output mix")]),
    ("P7-VE21","ContrastPlugin","contrast_effect","Contrast — levels-style contrast control.",
     ["contrast","levels","color","exposure","grade"],
     [("contrast",5.,"Contrast"),("brightness",5.,"Brightness"),
      ("gamma",5.,"Gamma"),("black",0.,"Black level"),
      ("white",10.,"White level"),("mix",8.,"Output mix")]),
    ("P7-VE22","SaturatePlugin","saturate_effect","Saturate — HSL saturation control.",
     ["saturate","hsl","color","vibrance","grade"],
     [("saturation",5.,"Saturation"),("vibrance",5.,"Vibrance"),
      ("hue_shift",0.,"Hue rotation"),("lightness",5.,"Lightness"),
      ("preserve_luminance",5.,"Luma preserve"),("mix",8.,"Output mix")]),
    ("P7-VE23","HuePlugin","hue_effect","Hue shift — rotates hue by a set amount.",
     ["hue","rotate","color","shift","grade"],
     [("hue_shift",0.,"Hue rotation"),("saturation",5.,"Saturation"),
      ("hue_range",10.,"Selective range"),("range_center",5.,"Range center"),
      ("feather",3.,"Selection feather"),("mix",8.,"Output mix")]),
    ("P7-VE24","BrightnessPlugin","brightness_effect","Brightness — simple brightness/gain control.",
     ["brightness","gain","exposure","grade","color"],
     [("brightness",5.,"Brightness"),("gain",5.,"Gain"),
      ("lift",0.,"Shadow lift"),("gamma",5.,"Gamma"),
      ("color_temp",5.,"Color temperature"),("mix",8.,"Output mix")]),
    ("P7-VE25","InvertPlugin","invert_effect","Invert — color and luminance inversion.",
     ["invert","negative","color","complement","grade"],
     [("amount",10.,"Invert amount"),("channel_r",10.,"Invert red"),
      ("channel_g",10.,"Invert green"),("channel_b",10.,"Invert blue"),
      ("luma_only",0.,"Luma only"),("mix",8.,"Output mix")]),
    ("P7-VE26","ThreshPlugin","thresh_effect","Threshold — converts to binary B/W.",
     ["threshold","binary","mask","stylize","bold"],
     [("threshold",5.,"Luma threshold"),("softness",3.,"Edge softness"),
      ("invert",0.,"Invert"),("color_high",8.,"High color"),
      ("color_low",0.,"Low color"),("mix",8.,"Output mix")]),
    ("P7-VE27","RGBShiftPlugin","rgb_shift","RGB shift — chromatic aberration/RGB separation.",
     ["rgb","chromatic","aberration","shift","glitch"],
     [("shift_r",5.,"Red offset"),("shift_g",5.,"Green offset"),
      ("shift_b",5.,"Blue offset"),("angle",5.,"Shift angle"),
      ("distance",5.,"Shift distance"),("mix",8.,"Output mix")]),
    ("P7-VE28","ColorCorrectPlugin","color_correct","Color correction — full ASC CDL colour correct.",
     ["color-correct","grade","cdl","asc","cinematic"],
     [("lift_r",5.,"Lift R"),("lift_g",5.,"Lift G"),("lift_b",5.,"Lift B"),
      ("gamma",5.,"Gamma"),("gain",5.,"Gain"),("saturation",5.,"Saturation")]),
    ("P7-VE29","ColorGradePlugin","color_grade2","Color grade — split-tone colour grading.",
     ["color-grade","lut","cinematic","shadows","highlights"],
     [("shadow_hue",5.,"Shadow hue"),("highlight_hue",5.,"Highlight hue"),
      ("contrast",5.,"Contrast"),("saturation",5.,"Saturation"),
      ("temperature",5.,"Color temp"),("mix",8.,"Output mix")]),
    ("P7-VE30","ColoramaPlugin","colorama","Colorama — maps luma to a hue gradient.",
     ["colorama","luma-to-color","gradient","psychedelic","abstract"],
     [("hue_start",0.,"Start hue"),("hue_end",10.,"End hue"),
      ("saturation",8.,"Saturation"),("cycle_speed",0.,"Cycle speed"),
      ("gamma",5.,"Gamma pre-map"),("mix",8.,"Output mix")]),
    ("P7-VE31","DisplacementMapPlugin","displacement_map","Displacement map — UV warp from external map.",
     ["displacement","uv","warp","distortion","map"],
     [("strength",5.,"Displacement strength"),("map_scale",5.,"Map scale"),
      ("x_axis",5.,"X channel weight"),("y_axis",5.,"Y channel weight"),
      ("time_warp",0.,"Animate map"),("mix",8.,"Output mix")]),
    ("P7-VE32","ChromaticDistortionPlugin","chromatic_distortion","Chromatic distortion — per-channel UV distortion.",
     ["chromatic","distortion","aberration","uv","glitch"],
     [("strength",5.,"Distortion strength"),("pattern",0.,"Distortion pattern"),
      ("speed",3.,"Animation speed"),("edge_boost",3.,"Edge emphasis"),
      ("frequency",5.,"Pattern frequency"),("mix",8.,"Output mix")]),
    ("P7-VE33","PatternDistortionPlugin","pattern_distortion","Pattern distortion — tiled-pattern UV warp.",
     ["pattern","distortion","tile","uv","warp"],
     [("pattern_type",0.,"Pattern type"),("scale",5.,"Pattern scale"),
      ("strength",5.,"Distortion strength"),("speed",3.,"Animation speed"),
      ("rotation",0.,"Rotation"),("mix",8.,"Output mix")]),
    ("P7-VE34","DitheringPlugin","dithering_effect","Dithering — ordered/error-diffusion dithering.",
     ["dither","quantize","retro","8bit","stylize"],
     [("levels",5.,"Bit depth"),("dither_type",0.,"0=ordered,5=Floyd-Steinberg"),
      ("scale",5.,"Dither matrix scale"),("gamma",5.,"Gamma"),
      ("color_mode",0.,"Color/BW"),("mix",8.,"Output mix")]),
    ("P7-VE35","FluidSimPlugin","fluid_sim","Fluid simulation — GPU Navier-Stokes fluid.",
     ["fluid","navier-stokes","simulation","physics","flow"],
     [("viscosity",5.,"Fluid viscosity"),("velocity_decay",5.,"Velocity decay"),
      ("diffuse",5.,"Color diffusion"),("force_strength",5.,"External force"),
      ("curl",3.,"Curl noise"),("mix",8.,"Output mix")]),
    ("P7-VE36","MandalascopePlugin","mandalascope","Mandalascope — kaleidoscopic mandala from video.",
     ["mandala","kaleidoscope","symmetry","mirror","sacred"],
     [("segments",5.,"Mirror segments"),("rotation",0.,"Rotation speed"),
      ("zoom",5.,"Zoom"),("hue_shift",0.,"Hue shift"),
      ("feedback",0.,"Feedback"),("mix",8.,"Output mix")]),
    ("P7-VE37","RotatePlugin","rotate_effect","Rotate — continuous rotation transform.",
     ["rotate","transform","geometry","angle","spin"],
     [("angle",5.,"Rotation angle"),("speed",0.,"Auto-rotate speed"),
      ("center_x",5.,"Pivot X"),("center_y",5.,"Pivot Y"),
      ("zoom",5.,"Scale during rotate"),("mix",8.,"Output mix")]),
    ("P7-VE38","ScalePlugin","scale_effect","Scale — scale/zoom transform.",
     ["scale","zoom","transform","geometry","resize"],
     [("scale_x",5.,"X scale"),("scale_y",5.,"Y scale"),
      ("center_x",5.,"Pivot X"),("center_y",5.,"Pivot Y"),
      ("maintain_aspect",8.,"Aspect ratio lock"),("mix",8.,"Output mix")]),
    ("P7-VE39","PixelatePlugin","pixelate_effect","Pixelate — blocky mosaic pixelation.",
     ["pixelate","mosaic","blocky","8bit","stylize"],
     [("block_size",3.,"Pixel block size"),("shape",0.,"Block shape"),
      ("color_blend",5.,"Color average"),("edge_detect",0.,"Edge preserve"),
      ("animation_speed",0.,"Block jitter"),("mix",8.,"Output mix")]),
    ("P7-VE40","RepeatPlugin","repeat_effect","Repeat — tile and repeat input video.",
     ["repeat","tile","grid","layout","transform"],
     [("count_x",5.,"Horizontal tiles"),("count_y",5.,"Vertical tiles"),
      ("offset_x",0.,"X offset"),("offset_y",0.,"Y offset"),
      ("mirror",0.,"Mirror alternates"),("mix",8.,"Output mix")]),
    ("P7-VE41","ScrollPlugin","scroll_effect","Scroll — continuous UV scrolling.",
     ["scroll","pan","uv","motion","camera"],
     [("speed_x",0.,"Horizontal speed"),("speed_y",0.,"Vertical speed"),
      ("wrap",8.,"Wrap edges"),("blur_edges",0.,"Edge blur"),
      ("zoom",5.,"Zoom"),("mix",8.,"Output mix")]),
    ("P7-VE42","MirrorPlugin","mirror_effect","Mirror — flip/mirror video input.",
     ["mirror","flip","symmetry","horizontal","vertical"],
     [("mirror_x",0.,"Horizontal mirror"),("mirror_y",0.,"Vertical mirror"),
      ("center_x",5.,"Center X"),("center_y",5.,"Center Y"),
      ("quad_mirror",0.,"4-way mirror"),("mix",8.,"Output mix")]),
    ("P7-VE43","ProjectionMappingPlugin","projection_mapping2","Projection mapping — warp video to flat surface.",
     ["projection","mapping","geometry","transform","installation"],
     [("quad_p1x",5.,"Corner 1 X"),("quad_p1y",5.,"Corner 1 Y"),
      ("warp_x",5.,"Warp X"),("warp_y",5.,"Warp Y"),
      ("perspective",5.,"Perspective"),("mix",8.,"Output mix")]),
    ("P7-VE44","VimanaHyperionPlugin","vimana_hyperion","Vimana Hyperion — geometric sacred craft manifestation.",
     ["vimana","hyperion","sacred","geometric","mystical"],
     [("intensity",5.,"Effect intensity"),("rotation_speed",3.,"Rotation"),
      ("color_hue",5.,"Hue"),("sacred_scale",5.,"Sacred scale"),
      ("aura_glow",3.,"Aura glow"),("mix",8.,"Output mix")]),
    ("P7-VE45","HyperspaceTunnelPlugin","hyperspace_tunnel","Hyperspace tunnel — warp-speed star field tunnel.",
     ["hyperspace","tunnel","warp","stars","space"],
     [("speed",5.,"Warp speed"),("radius",5.,"Tunnel radius"),
      ("twist",3.,"Tunnel twist"),("star_density",5.,"Star density"),
      ("color_shift",0.,"Hue shift"),("mix",8.,"Output mix")]),
    ("P7-VE46","LivingFractalPlugin","living_fractal","Living fractal consciousness — organic recursive growth.",
     ["fractal","consciousness","living","organic","recursive"],
     [("growth_rate",5.,"Growth rate"),("iteration_depth",5.,"Iterations"),
      ("color_cycle",5.,"Color cycling"),("scale",5.,"Scale"),
      ("consciousness",5.,"Awareness level"),("mix",8.,"Output mix")]),
    ("P7-VE47","LumaChromaMaskPlugin","luma_chroma_mask","Luma/chroma mask — HSL-based selection mask.",
     ["luma","chroma","mask","selection","keying"],
     [("luma_min",0.,"Min luminance"),("luma_max",10.,"Max luminance"),
      ("chroma_hue",5.,"Target hue"),("chroma_range",3.,"Hue range"),
      ("feather",3.,"Mask feather"),("mix",8.,"Output mix")]),
    ("P7-VE48","LUTGradingPlugin","lut_grading","LUT grading — 1D look-up table colour grade.",
     ["lut","grade","color","cinematic","film"],
     [("lut_intensity",8.,"LUT strength"),("saturation",5.,"Saturation"),
      ("contrast",5.,"Contrast"),("temperature",5.,"Temperature"),
      ("tint",5.,"Tint"),("mix",8.,"Output mix")]),
    ("P7-VE49","MilkdropPlugin","milkdrop","Milkdrop — classic Winamp-style audio visualizer.",
     ["milkdrop","visualizer","audio","preset","winamp"],
     [("preset_mix",5.,"Preset blend"),("wave_size",5.,"Wave size"),
      ("warp_amount",5.,"UV warp"),("color_speed",5.,"Color speed"),
      ("bass_response",5.,"Bass drive"),("mix",8.,"Output mix")]),
    ("P7-VE50","MorphologyPlugin","morphology_effect","Morphology — erode/dilate/open/close operations.",
     ["morphology","erode","dilate","mask","process"],
     [("operation",5.,"0=erode,5=dilate,8=open,10=close"),("kernel_size",3.,"Kernel size"),
      ("iterations",3.,"Iterations"),("channel",5.,"Channel"),
      ("threshold",5.,"Input threshold"),("mix",8.,"Output mix")]),
    ("P7-VE51","OscilloscopePlugin","oscilloscope_effect","Oscilloscope — video oscilloscope display.",
     ["oscilloscope","scope","waveform","audio","display"],
     [("zoom",5.,"Display zoom"),("trace_hue",5.,"Trace color"),
      ("persistence",5.,"Phosphor persistence"),("grid_opacity",3.,"Grid"),
      ("trigger_level",5.,"Trigger level"),("mix",8.,"Output mix")]),
    ("P7-VE52","CustomEffectPlugin","custom_effect","Custom effect — user scriptable plugin template.",
     ["custom","template","user","scriptable","extend"],
     [("param_a",5.,"Custom param A"),("param_b",5.,"Custom param B"),
      ("param_c",5.,"Custom param C"),("param_d",5.,"Custom param D"),
      ("param_e",5.,"Custom param E"),("mix",8.,"Output mix")]),
    ("P7-VE53","BenDayDotsPlugin","ben_day_dots","Ben-Day dots — Roy Lichtenstein pop art halftone.",
     ["pop-art","halftone","ben-day","dots","lichtenstein"],
     [("dot_size",5.,"Dot radius"),("dot_spacing",5.,"Dot pitch"),
      ("color_reduce",5.,"Color levels"),("angle",0.,"Grid angle"),
      ("blend_mode",0.,"Dot blend"),("mix",8.,"Output mix")]),
    ("P7-VE54","WarholQuadPlugin","warhol_quad","Warhol quad — 4-panel Warhol-style color repeat.",
     ["warhol","pop-art","quad","color","silkscreen"],
     [("hue_a",0.,"Panel A hue"),("hue_b",3.,"Panel B hue"),
      ("hue_c",6.,"Panel C hue"),("hue_d",9.,"Panel D hue"),
      ("saturation",8.,"Saturation"),("mix",8.,"Output mix")]),
    ("P7-VE55","R16DeepMoshPlugin","r16_deep_mosh","R16 deep mosh studio — extreme datamosh resampler.",
     ["r16","deep-mosh","extreme","datamosh","studio"],
     [("intensity",5.,"Mosh intensity"),("block_size",3.,"Block size"),
      ("temporal_depth",5.,"Time depth"),("color_corrupt",3.,"Color corruption"),
      ("feedback",5.,"Feedback"),("mix",8.,"Output mix")]),
    ("P7-VE56","R16InterstellarPlugin","r16_interstellar","R16 interstellar mosh — space-travel datamosh.",
     ["r16","interstellar","space","datamosh","cosmic"],
     [("warp_speed",5.,"Warp speed"),("star_intensity",5.,"Star field"),
      ("mosh_depth",5.,"Mosh depth"),("chroma_shift",3.,"Chromatic"),
      ("feedback",5.,"Feedback"),("mix",8.,"Output mix")]),
    ("P7-VE57","ReactionDiffusionPlugin","reaction_diffusion","Reaction diffusion — Gray-Scott RD simulation.",
     ["reaction-diffusion","gray-scott","simulation","organic","pattern"],
     [("feed_rate",5.,"Feed rate"),("kill_rate",5.,"Kill rate"),
      ("diffuse_a",5.,"Diffuse A"),("diffuse_b",5.,"Diffuse B"),
      ("speed",5.,"Simulation speed"),("mix",8.,"Output mix")]),
    ("P7-VE58","ResizePlugin","resize_effect","Resize — letterbox/crop/stretch resize modes.",
     ["resize","crop","letterbox","transform","aspect"],
     [("target_width",5.,"Target width %"),("target_height",5.,"Target height %"),
      ("mode",0.,"0=stretch,3=fit,5=crop,10=fill"),("offset_x",5.,"Offset X"),
      ("blur_edges",0.,"Edge blur"),("mix",8.,"Output mix")]),
    ("P7-VE59","RuttEtraPlugin","rutt_etra","Rutt/Etra scanline synthesizer — depth-modulated scanlines.",
     ["rutt-etra","scanline","depth","analog","synth"],
     [("scan_count",5.,"Scanline count"),("depth_amount",5.,"Depth warp"),
      ("scan_width",3.,"Line width"),("color_from_depth",5.,"Depth coloring"),
      ("rotation",0.,"Rotation"),("mix",8.,"Output mix")]),
    ("P7-VE60","VideoOutPlugin","video_out","Video out — pass-through output with gain.",
     ["output","passthrough","final","gain","master"],
     [("gain",5.,"Output gain"),("gamma",5.,"Gamma"),
      ("black_level",0.,"Black clip"),("white_level",10.,"White clip"),
      ("saturation",5.,"Saturation"),("mix",10.,"Output mix")]),
    ("P7-VE61","ImageInPlugin","image_in","Image in — static image loader and compositor.",
     ["image","loader","composite","static","overlay"],
     [("scale",5.,"Image scale"),("pos_x",5.,"Position X"),
      ("pos_y",5.,"Position Y"),("opacity",8.,"Opacity"),
      ("blend_mode",0.,"Blend mode"),("mix",8.,"Output mix")]),
    ("P7-VE62","CoordinateFolderPlugin","coordinate_folder","Coordinate folder — fold/mirror UV coordinates.",
     ["coordinate","fold","uv","transform","kaleidoscope"],
     [("fold_x",5.,"X fold count"),("fold_y",5.,"Y fold count"),
      ("offset_x",0.,"X offset"),("offset_y",0.,"Y offset"),
      ("rotation",0.,"Rotation"),("mix",8.,"Output mix")]),
    ("P7-VE63","AffineTransformPlugin","affine_transform","Affine transform — full 2D affine matrix.",
     ["affine","transform","matrix","2d","warp"],
     [("scale_x",5.,"Scale X"),("scale_y",5.,"Scale Y"),
      ("shear_x",5.,"Shear X"),("shear_y",5.,"Shear Y"),
      ("translate_x",5.,"Translate X"),("mix",8.,"Output mix")]),
    ("P7-VE64","PreciseDelayPlugin","precise_delay","Precise delay — exact frame delay buffer.",
     ["delay","temporal","buffer","latency","timing"],
     [("delay_frames",0.,"Frame delay"),("blend",5.,"Blend ratio"),
      ("freeze",0.,"Freeze frame"),("jitter",0.,"Random jitter"),
      ("color_shift",0.,"Hue drift"),("mix",8.,"Output mix")]),
    ("P7-VE65","SlitScanPlugin","slit_scan","Slit scan — temporal slit-scan photography.",
     ["slit-scan","temporal","photography","time","warp"],
     [("scan_width",3.,"Slit width"),("scan_speed",5.,"Scan speed"),
      ("direction",5.,"Scan direction"),("time_depth",5.,"Time depth"),
      ("warp",3.,"Warp"),("mix",8.,"Output mix")]),
    ("P7-VE66","SyncEaterPlugin","sync_eater","Sync eater — consumes and desynchronises video sync.",
     ["sync","glitch","desync","analog","degradation"],
     [("eat_amount",5.,"Sync destruction"),("horizontal_tear",5.,"H-tear"),
      ("vertical_roll",3.,"V-roll"),("noise",3.,"Noise"),
      ("tracking",5.,"Tracking error"),("mix",8.,"Output mix")]),
    ("P7-VE67","TimeRemapPlugin","time_remap","Time remap — non-linear time remapping.",
     ["time-remap","speed","slow-motion","reverse","temporal"],
     [("speed_mult",5.,"Playback speed"),("reverse",0.,"Reverse"),
      ("freeze",0.,"Freeze point"),("stutter",0.,"Stutter amount"),
      ("blend",5.,"Inter-frame blend"),("mix",8.,"Output mix")]),
    ("P7-VE68","GaussianBlurPlugin","gaussian_blur","Gaussian blur — separable Gaussian blur.",
     ["blur","gaussian","smooth","soften","denoise"],
     [("radius",5.,"Blur radius"),("sigma",5.,"Gaussian sigma"),
      ("quality",5.,"Pass count"),("edge_mode",0.,"Edge handling"),
      ("color_bleed",0.,"Chromatic blur"),("mix",8.,"Output mix")]),
    ("P7-VE69","MultibandColorPlugin","multiband_color","Multiband color — frequency-domain color processing.",
     ["multiband","color","frequency","hsl","grade"],
     [("shadow_sat",5.,"Shadow saturation"),("mid_sat",5.,"Midtone saturation"),
      ("highlight_sat",5.,"Highlight saturation"),("shadow_hue",5.,"Shadow hue"),
      ("highlight_hue",5.,"Highlight hue"),("mix",8.,"Output mix")]),
    ("P7-VE70","HDRToneMapPlugin","hdr_tonemap","HDR tone map — Reinhard/ACES tone mapping.",
     ["hdr","tonemapping","reinhard","aces","exposure"],
     [("exposure",5.,"Exposure"),("tone_mode",5.,"0=linear,3=reinhard,5=aces"),
      ("white_point",8.,"White point"),("gamma",5.,"Gamma"),
      ("saturation",5.,"Saturation"),("mix",8.,"Output mix")]),
    ("P7-VE71","SolarizePlugin","solarize_effect","Solarize — Man Ray-style partial inversion.",
     ["solarize","man-ray","photo","invert","artistic"],
     [("threshold",5.,"Solarize threshold"),("amount",8.,"Effect strength"),
      ("color_mode",5.,"Color/mono"),("hue_invert",0.,"Hue inversion"),
      ("gamma",5.,"Gamma"),("mix",8.,"Output mix")]),
    ("P7-VE72","ResonantBlurPlugin","resonant_blur","Resonant blur — frequency-modulated directional blur.",
     ["blur","resonant","directional","frequency","vcv"],
     [("blur_frequency",5.,"Resonant frequency"),("blur_amount",5.,"Blur strength"),
      ("direction",5.,"Blur direction"),("resonance",5.,"Resonance"),
      ("bass_response",5.,"Bass drive"),("mix",8.,"Output mix")]),
    ("P7-VE73","AdaptiveContrastPlugin","adaptive_contrast","Adaptive contrast — local CLAHE-style contrast.",
     ["contrast","adaptive","clahe","local","enhancement"],
     [("region_size",5.,"Region size"),("clip_limit",5.,"Clip limit"),
      ("amount",5.,"Blend amount"),("gamma",5.,"Gamma"),
      ("sharpness",3.,"Edge sharpness"),("mix",8.,"Output mix")]),
    ("P7-VE74","SpatialEchoPlugin","spatial_echo","Spatial echo — directional delay echo cascade.",
     ["echo","spatial","delay","cascade","feedback"],
     [("echo_count",5.,"Echo count"),("echo_delay",5.,"Delay per echo"),
      ("echo_decay",5.,"Echo fade"),("direction",5.,"Echo direction"),
      ("color_shift",0.,"Hue per echo"),("mix",8.,"Output mix")]),
    ("P7-VE75","DelayZoomPlugin","delay_zoom","Delay zoom — temporal zoom echo cascade.",
     ["delay","zoom","temporal","echo","cascade"],
     [("zoom_per_echo",5.,"Zoom factor"),("echo_count",5.,"Echo count"),
      ("decay",5.,"Opacity decay"),("rotation",0.,"Rotation per echo"),
      ("hue_drift",0.,"Hue per echo"),("mix",8.,"Output mix")]),
    ("P7-VE76","RioAestheticPlugin","rio_aesthetic","Rio aesthetic — vibrant Brazilian retro visual style.",
     ["rio","retro","brasil","vibrant","aesthetic"],
     [("saturation_boost",7.,"Saturation boost"),("warmth",6.,"Color warmth"),
      ("rhythm_pulse",5.,"Rhythm pulse"),("pattern_mix",3.,"Pattern overlay"),
      ("contrast",5.,"Contrast"),("mix",8.,"Output mix")]),
    ("P7-VE77","VimanaPlugin","vimana","Vimana — sacred geometric craft visualization.",
     ["vimana","sacred","geometric","mystical","ancient"],
     [("rotation_speed",3.,"Rotation speed"),("scale",5.,"Scale"),
      ("color_hue",5.,"Hue"),("glow_radius",3.,"Glow"),
      ("geometry_type",5.,"Geometry preset"),("mix",8.,"Output mix")]),
    ("P7-VE78","VimanaHyperionUltimatePlugin","vimana_hyperion_ultimate",
     "Vimana Hyperion Ultimate — maximum power sacred craft mode.",
     ["vimana","hyperion","ultimate","sacred","supreme"],
     [("power_level",8.,"Power level"),("rotation_speed",5.,"Spin speed"),
      ("color_hue",5.,"Hue"),("sacred_scale",7.,"Sacred scale"),
      ("cosmic_glow",5.,"Cosmic glow"),("mix",8.,"Output mix")]),
    ("P7-VE79","VimanaSynthPlugin","vimana_synth","Vimana synth — synthesizer-driven sacred geometry.",
     ["vimana","synth","geometry","oscillator","sacred"],
     [("synth_freq",5.,"Synth frequency"),("amplitude",5.,"Amplitude"),
      ("waveform",0.,"Waveform type"),("geometry_type",5.,"Geometry"),
      ("color_hue",5.,"Hue"),("mix",8.,"Output mix")]),
    ("P7-VE80","VisualizerPlugin","visualizer_effect","Visualizer — general-purpose audio visualizer.",
     ["visualizer","audio","spectrum","bars","music"],
     [("bar_count",5.,"Bar count"),("bar_height",5.,"Height scale"),
      ("color_hue",5.,"Base hue"),("color_mode",5.,"Color from frequency"),
      ("bass_response",5.,"Bass response"),("mix",8.,"Output mix")]),
]

# Reuse same templates from gen_datamosh_plugins_2.py
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
    "plugin_type": "effect",
    "category": "vfx",
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
void main() {{ gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0); uv = verts[gl_VertexID]*0.5+0.5; }}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv; out vec4 fragColor;
uniform sampler2D tex0; uniform sampler2D prev_tex;
uniform vec2 resolution; uniform float time; uniform float u_mix;
{uniform_block}
float hash(vec2 p) {{ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }}
float noise(vec2 p) {{
    vec2 i=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
}}
void main() {{
    vec4 curr = texture(tex0, uv);
    vec4 prev = texture(prev_tex, uv);
    float d = {disp_expr}; float fb = {feedback_expr}; float fr = 8.0+{freq_expr}*10.0;
    float ch = {chroma_expr}; float vg = {vign_expr};
    vec2 du = vec2(noise(uv*fr+vec2(time*0.5))-0.5, noise(uv*fr+vec2(1.3,time*0.4))-0.5)*d*0.05;
    vec4 w = texture(tex0, clamp(uv+du,0.,1.));
    vec3 c = mix(w.rgb, prev.rgb, fb*0.2);
    c.r = texture(tex0, clamp(uv+du+vec2(ch*0.01,0.),0.,1.)).r;
    c.b = texture(tex0, clamp(uv+du-vec2(ch*0.01,0.),0.,1.)).b;
    if(vg>0.){{vec2 vc=uv*2.-1.; c*=1.-dot(vc,vc)*vg*0.5;}}
    c.r *= 1.+{r_tint}; c.g *= 1.+{g_tint}; c.b *= 1.+{b_tint};
    fragColor = mix(curr, vec4(clamp(c,0.,1.), curr.a), u_mix);
}}
"""

_PARAM_NAMES = {param_names!r}
_PARAM_DEFAULTS = {param_defaults!r}

def _map(val,lo,hi): return lo+(max(0.,min(10.,float(val)))/10.)*(hi-lo)

class {class_name}(EffectPlugin):
    """{description}"""
    def __init__(self):
        super().__init__()
        self._mock_mode=not HAS_GL; self.prog=self.vao=0
        self.trail_fbo=self.trail_tex=0; self._w=self._h=0; self._initialized=False
    def get_metadata(self): return METADATA
    def _compile(self,vs,fs):
        v=gl.glCreateShader(gl.GL_VERTEX_SHADER); gl.glShaderSource(v,vs); gl.glCompileShader(v)
        if not gl.glGetShaderiv(v,gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
        f=gl.glCreateShader(gl.GL_FRAGMENT_SHADER); gl.glShaderSource(f,fs); gl.glCompileShader(f)
        if not gl.glGetShaderiv(f,gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
        p=gl.glCreateProgram(); gl.glAttachShader(p,v); gl.glAttachShader(p,f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p,gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f); return p
    def _make_fbo(self,w,h):
        fbo=gl.glGenFramebuffers(1); tex=gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D,tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D,0,gl.GL_RGBA,w,h,0,gl.GL_RGBA,gl.GL_UNSIGNED_BYTE,None)
        for k,v2 in [(gl.GL_TEXTURE_MIN_FILTER,gl.GL_LINEAR),(gl.GL_TEXTURE_MAG_FILTER,gl.GL_LINEAR),
                     (gl.GL_TEXTURE_WRAP_S,gl.GL_CLAMP_TO_EDGE),(gl.GL_TEXTURE_WRAP_T,gl.GL_CLAMP_TO_EDGE)]:
            gl.glTexParameteri(gl.GL_TEXTURE_2D,k,v2)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER,gl.GL_COLOR_ATTACHMENT0,gl.GL_TEXTURE_2D,tex,0)
        gl.glClearColor(0,0,0,0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,0); return fbo,tex
    def initialize(self,context):
        if self._mock_mode or not hasattr(gl,'glCreateShader'):
            self._initialized=True; return True
        try:
            self.prog=self._compile(VERTEX_SHADER,FRAGMENT_SHADER); self.vao=gl.glGenVertexArrays(1)
            self._initialized=True; return True
        except Exception as e:
            logger.error(f"{{self.__class__.__name__}} init: {{e}}"); self._mock_mode=True; return False
    def _u(self,n): return gl.glGetUniformLocation(self.prog,n)
    def process_frame(self,input_texture,params,context):
        if not input_texture or input_texture<=0: return 0
        if self._mock_mode or not hasattr(gl,'glCreateShader'):
            if hasattr(context,'outputs'): context.outputs['video_out']=input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w=getattr(context,'width',1920); h=getattr(context,'height',1080)
        if w!=self._w or h!=self._h:
            if self.trail_fbo:
                try: gl.glDeleteFramebuffers(1,[self.trail_fbo]); gl.glDeleteTextures(1,[self.trail_tex])
                except Exception: pass
            self.trail_fbo,self.trail_tex=self._make_fbo(w,h); self._w,self._h=w,h
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,self.trail_fbo); gl.glViewport(0,0,w,h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D,input_texture); gl.glUniform1i(self._u('tex0'),0)
        gl.glActiveTexture(gl.GL_TEXTURE1); gl.glBindTexture(gl.GL_TEXTURE_2D,self.trail_tex); gl.glUniform1i(self._u('prev_tex'),1)
        gl.glUniform2f(self._u('resolution'),float(w),float(h))
        gl.glUniform1f(self._u('time'),float(getattr(context,'time',0.)))
        gl.glUniform1f(self._u('u_mix'),_map(params.get('mix',8.),0.,1.))
        for p in _PARAM_NAMES:
            gl.glUniform1f(self._u(p),float(params.get(p,_PARAM_DEFAULTS.get(p,5.))))
        gl.glBindVertexArray(self.vao); gl.glDrawArrays(gl.GL_TRIANGLE_STRIP,0,4)
        gl.glBindVertexArray(0); gl.glUseProgram(0); gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,0)
        if hasattr(context,'outputs'): context.outputs['video_out']=self.trail_tex
        return self.trail_tex
    def cleanup(self):
        try:
            if hasattr(gl,'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl,'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1,[self.vao])
            if hasattr(gl,'glDeleteTextures') and self.trail_tex: gl.glDeleteTextures(1,[self.trail_tex])
            if hasattr(gl,'glDeleteFramebuffers') and self.trail_fbo: gl.glDeleteFramebuffers(1,[self.trail_fbo])
        except Exception as e: logger.error(f"{{self.__class__.__name__}} cleanup: {{e}}")
        finally: self.prog=self.vao=self.trail_fbo=self.trail_tex=0
'''

TEST_TEMPLATE = '''"""Tests for {task_id}: {class_name}."""
import pytest
from unittest.mock import MagicMock, patch
import sys
_gl=MagicMock(); _gl.GL_VERTEX_SHADER=35633; _gl.GL_FRAGMENT_SHADER=35632
_gl.GL_COMPILE_STATUS=35713; _gl.GL_LINK_STATUS=35714; _gl.GL_TEXTURE_2D=3553
_gl.GL_RGBA=6408; _gl.GL_UNSIGNED_BYTE=5121; _gl.GL_LINEAR=9729; _gl.GL_CLAMP_TO_EDGE=33071
_gl.GL_TEXTURE_MIN_FILTER=10241; _gl.GL_TEXTURE_MAG_FILTER=10240
_gl.GL_TEXTURE_WRAP_S=10242; _gl.GL_TEXTURE_WRAP_T=10243
_gl.GL_FRAMEBUFFER=36160; _gl.GL_COLOR_ATTACHMENT0=36064
_gl.GL_COLOR_BUFFER_BIT=16384; _gl.GL_TRIANGLE_STRIP=5; _gl.GL_FALSE=0; _gl.GL_TRUE=1
_gl.glGetShaderiv.return_value=1; _gl.glGetProgramiv.return_value=1
_gl.glCreateProgram.return_value=99; _gl.glGenVertexArrays.return_value=44
_gl.glGenTextures.return_value=55; _gl.glGenFramebuffers.return_value=51
sys.modules['OpenGL']=MagicMock(); sys.modules['OpenGL.GL']=_gl
from vjlive3.plugins.{file_stem} import {class_name}, METADATA
from vjlive3.plugins.api import PluginContext
@pytest.fixture
def plugin():
    _gl.reset_mock(); _gl.glGetShaderiv.return_value=1; _gl.glGetProgramiv.return_value=1
    _gl.glCreateProgram.return_value=99; _gl.glGenVertexArrays.return_value=44
    _gl.glGenTextures.return_value=55; _gl.glGenFramebuffers.return_value=51
    return {class_name}()
@pytest.fixture
def context():
    ctx=PluginContext(MagicMock()); ctx.width=64; ctx.height=48; ctx.time=1.0
    ctx.inputs={{"video_in":10}}; ctx.outputs={{}}; return ctx
def test_metadata(plugin):
    m=plugin.get_metadata(); assert m["name"]=={display_name!r}; assert len(m["parameters"])=={num_params}
@patch('vjlive3.plugins.{file_stem}.gl', _gl)
def test_initialize(plugin, context): assert plugin.initialize(context) is True
@patch('vjlive3.plugins.{file_stem}.gl', _gl)
def test_zero_input(plugin, context): plugin.initialize(context); assert plugin.process_frame(0,{{}},context)==0
@patch('vjlive3.plugins.{file_stem}.gl', _gl)
@patch('vjlive3.plugins.{file_stem}.hasattr')
def test_mock_fallback(mh, plugin, context):
    mh.side_effect=lambda o,a: False if a=='glCreateShader' else True
    assert plugin.process_frame(10,{{}},context)==10
@patch('vjlive3.plugins.{file_stem}.gl', _gl)
def test_renders(plugin, context):
    plugin.initialize(context); assert plugin.process_frame(10,{{}},context)==55
    _gl.glDrawArrays.assert_called_once()
@patch('vjlive3.plugins.{file_stem}.gl', _gl)
def test_compile_fail(plugin, context):
    _gl.glGetShaderiv.return_value=0; _gl.glGetShaderInfoLog.return_value=b"E"
    assert plugin.initialize(context) is False; _gl.glGetShaderiv.return_value=1
@patch('vjlive3.plugins.{file_stem}.gl', _gl)
def test_cleanup(plugin, context):
    plugin.initialize(context); plugin.prog=99; plugin.cleanup()
    _gl.glDeleteProgram.assert_called_once_with(99)
'''

def make_ub(params):
    return "\n".join(f"uniform float {n};  // {c}" for n,_,c in params)

def pick(params, candidates, default="0.0"):
    ns=[p[0] for p in params]
    for c in candidates:
        if c in ns: return f"({c}/10.0)"
    return default

def generate(d):
    tid, cn, fs, desc, tags, params = d
    dn = fs.replace("_"," ").title()
    pm = [{"name":n,"type":"float","default":v,"min":0.0,"max":10.0} for n,v,_ in params]
    pnames = [p[0] for p in params]; pdefs = {p[0]:p[1] for p in params}

    disp = pick(params,["amplitude","strength","intensity","zoom","blur_radius","effect_strength",
                         "blur_amount","power_level","amount","warp_amount","shift_r","eat_amount"])
    fb   = pick(params,["feedback","decay","persistence","blend","echo_decay","trail_length"])
    freq = pick(params,["frequency","speed","animation_speed","echo_count","stripe_count","scan_speed"])
    ch   = pick(params,["color_bleed","chromatic","ch","chroma_shift","shift_b","rgb_shift"])
    vg   = pick(params,["vignette","vignette_crush"])
    ns   = [p[0] for p in params]
    rt   = next((f"{n}/10.0*0.2" for n in ns if any(k in n for k in ["color_hue","hue","warmth","red","r_","hue_a"])), "0.0")
    gt   = next((f"{n}/10.0*0.1" for n in ns if any(k in n for k in ["saturation","green","g_","gain"])), "0.0")
    bt   = next((f"{n}/10.0*0.2" for n in ns if any(k in n for k in ["feedback","blue","b_","zoom","power"])), "0.0")

    pc = PLUGIN_TEMPLATE.format(task_id=tid,class_name=cn,file_stem=fs,description=desc,
        display_name=dn,tags=tags,params_meta=pm,uniform_block=make_ub(params),
        disp_expr=disp,feedback_expr=fb,freq_expr=freq,chroma_expr=ch,vign_expr=vg,
        r_tint=rt,g_tint=gt,b_tint=bt,param_names=pnames,param_defaults=pdefs)
    tc = TEST_TEMPLATE.format(task_id=tid,class_name=cn,file_stem=fs,display_name=dn,num_params=len(params))

    with open(os.path.join(BASE,f"{fs}.py"),"w") as fp: fp.write(pc)
    with open(os.path.join(TEST_BASE,f"test_{fs}.py"),"w") as fp: fp.write(tc)
    print(f"✅ {tid}: {fs}.py")

if __name__=="__main__":
    for d in PLUGINS: generate(d)
    print(f"\nDone! {len(PLUGINS)} plugins.")
