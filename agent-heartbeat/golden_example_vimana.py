"""
Vimana GVS010 (Atomic Port)
Unified Software Emulation of the Gleix GVS010.

METADATA MIRROR:
The parameter structure is derived directly from the embedded manifest.
"""

from core.effects.shader_base import Effect
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ============================================================================
# UNIFIED VIMANA FRAGMENT SHADER
# ============================================================================
VIMANA_FRAGMENT = r"""
#version 330 core
in vec2 uv;
out vec4 fragColor;

// === Texture Inputs ===
uniform sampler2D tex0;       // Current input frame (or external video)
uniform sampler2D texPrev;    // Previous output frame (feedback source)
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// ========================================================================
// FEEDBACK ENGINE — Directional Controls
// ========================================================================
uniform float shift_up;       // Upward drift speed (0-10)
uniform float shift_down;     // Downward drift speed (0-10)
uniform float shift_left;     // Left drift speed (0-10)
uniform float shift_right;    // Right drift speed (0-10)
uniform float zoom;           // Zoom: 5=neutral, <5=out, >5=in (0-10)
uniform float freeze;         // Frame freeze: <5=off, >=5=frozen (0-10)
uniform float feedback_amount; // Feedback intensity (0-10)
uniform float decay;          // Signal degradation per loop (0-10)
uniform float edge_blur;      // Edge softening / bandwidth limit (0-10)
uniform float persistence;    // CRT phosphor persistence (0-10)
uniform float bypass_h;       // Bypass horizontal shift: <5=active, >=5=bypass
uniform float bypass_v;       // Bypass vertical shift: <5=active, >=5=bypass
uniform float bypass_zoom;    // Bypass zoom: <5=active, >=5=bypass

// ========================================================================
// COLOR PROCESSING — RGB Mix + Pulse
// ========================================================================
uniform float red_mix;        // Red channel gain (0-10, 5=unity)
uniform float green_mix;      // Green channel gain (0-10, 5=unity)
uniform float blue_mix;       // Blue channel gain (0-10, 5=unity)
uniform float red_pulse;      // Red pulse: <5=off, >=5=full inject
uniform float green_pulse;    // Green pulse
uniform float blue_pulse;     // Blue pulse

// ========================================================================
// OSCILLATOR MODULE — Dual-range modulation source
// ========================================================================
uniform float osc_enable;     // On/off: <5=off, >=5=on
uniform float rate;           // Frequency control (0-10)
uniform float shape;          // Waveform: 0=sine, 3.3=tri, 6.6=saw, 10=square
uniform float depth;          // Modulation amplitude (0-10)
uniform float range_select;   // <5=low (LFO), >=5=high (video-rate)
uniform float send_red;       // Route to red: <5=off, >=5=on
uniform float send_green;     // Route to green: <5=off, >=5=on
uniform float send_blue;      // Route to blue: <5=off, >=5=on
uniform float send_freeze;    // Route to freeze: <5=off, >=5=on

// ========================================================================
// AUDIO INTEGRATION — Audio/noise reactive modulation
// ========================================================================
uniform float u_audio_level;  // Audio RMS level (0.0-1.0) from audio analyzer
uniform float u_bass;         // Bass frequency band
uniform float u_mid;          // Mid frequency band
uniform float u_high;         // High frequency band
uniform float amp_enable;     // Amplifier on/off: <5=off, >=5=on
uniform float amp_gain;       // Amplifier gain (0-10)
uniform float amp_bypass;     // Bypass amplifier: <5=off, >=5=bypass
uniform float noise_enable;   // Internal noise gen: <5=off, >=5=on
uniform float noise_type;     // 0=white, 10=pink
uniform float audio_send_red;   // Audio → Red (0-10)
uniform float audio_send_green; // Audio → Green (0-10)
uniform float audio_send_blue;  // Audio → Blue (0-10)
uniform float envelope_speed; // Envelope attack/release speed (0-10)

// ========================================================================
// IMAGE ADJUSTMENT — Final output stage
// ========================================================================
uniform float brightness;     // Brightness (0-10, 5=neutral)
uniform float contrast;       // Contrast (0-10, 5=neutral)
uniform float saturation;     // Saturation (0-10, 5=neutral)
uniform float hue_rotate;     // Hue rotation (0-10, mapped to 0-360°)

// ========================================================================
// COMPOSITE VIDEO SIMULATION
// ========================================================================
uniform float composite_enable; // Master on/off: <5=off, >=5=on
uniform float sync_jitter;     // H-sync instability (0-10)
uniform float vertical_drift;  // V-sync instability (0-10)
uniform float chroma_bleed;    // Color bleeding amount (0-10)
uniform float dot_crawl;       // NTSC dot crawl intensity (0-10)
uniform float signal_clip;     // Hard signal clipping (0-10)
uniform float interlace;       // Interlace simulation: <5=off, >=5=on
uniform float ntsc_pal;        // 0=NTSC, 10=PAL
uniform float noise_amount;    // Analog noise level (0-10)
uniform float vhs_tracking;    // VHS tracking error bars (0-10)

// ========================================================================
// PATCHBAY — Virtual cross-routing switches
// ========================================================================
uniform float patch_sw1;         // Switch 1: <5=off, >=5=on
uniform float patch_sw2;         // Switch 2: <5=off, >=5=on
uniform float patch_sw3;         // Switch 3: <5=off, >=5=on
uniform float patch_sw4;         // Switch 4: <5=off, >=5=on
uniform float patch_osc_to_zoom;   // Route oscillator → zoom (0-10)
uniform float patch_audio_to_shift; // Route audio → directional shift (0-10)
uniform float patch_osc_to_freeze; // Route oscillator → freeze (0-10)
uniform float patch_audio_to_zoom; // Route audio → zoom (0-10)

// ========================================================================
// CV INPUTS — External modulation
// ========================================================================
uniform float cv_red;          // CV → Red channel (0-10)
uniform float cv_green;        // CV → Green channel (0-10)
uniform float cv_blue;         // CV → Blue channel (0-10)
uniform float cv_up;           // CV → Shift up (0-10)
uniform float cv_down;         // CV → Shift down (0-10)
uniform float cv_left;         // CV → Shift left (0-10)
uniform float cv_right;        // CV → Shift right (0-10)
uniform float cv_zoom;         // CV → Zoom (0-10)


// ========================================================================
// UTILITY FUNCTIONS
// ========================================================================

// --- Pseudo-random noise ---
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

// White noise
float white_noise(vec2 co, float t) {
    return fract(sin(dot(co + t, vec2(12.9898, 78.233))) * 43758.5453);
}

// Pink noise approximation (1/f spectrum via octave mixing)
float pink_noise(vec2 co, float t) {
    float n = 0.0;
    float amp = 0.5;
    float freq = 1.0;
    for (int i = 0; i < 5; i++) {
        n += white_noise(co * freq, t * freq) * amp;
        amp *= 0.5;
        freq *= 2.0;
    }
    return n;
}

// --- Oscillator waveform generation ---
float generate_wave(float phase, float shape_param) {
    float norm = shape_param / 10.0;
    float p = fract(phase);

    // Generate all four waveforms
    float sine = sin(p * 6.28318530718);
    float tri = abs(p * 4.0 - 2.0) - 1.0;
    float saw = p * 2.0 - 1.0;
    float sq = step(0.5, p) * 2.0 - 1.0;

    // Morph between them based on shape parameter
    float wave;
    if (norm < 0.333) {
        float t = norm / 0.333;
        wave = mix(sine, tri, t);
    } else if (norm < 0.666) {
        float t = (norm - 0.333) / 0.333;
        wave = mix(tri, saw, t);
    } else {
        float t = (norm - 0.666) / 0.334;
        wave = mix(saw, sq, t);
    }

    return wave;  // Range: -1.0 to 1.0
}

// --- HSV conversion utilities ---
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

// --- YIQ (NTSC) color space conversion ---
vec3 rgb2yiq(vec3 rgb) {
    return mat3(
        0.299,  0.596,  0.211,
        0.587, -0.274, -0.523,
        0.114, -0.322,  0.312
    ) * rgb;
}

vec3 yiq2rgb(vec3 yiq) {
    return mat3(
        1.0,  1.0, 1.0,
        0.956, -0.272, -1.106,
        0.621, -0.647, 1.703
    ) * yiq;
}

// --- YUV (PAL) color space conversion ---
vec3 rgb2yuv(vec3 rgb) {
    return mat3(
        0.299, -0.147,  0.615,
        0.587, -0.289, -0.515,
        0.114,  0.436, -0.100
    ) * rgb;
}

vec3 yuv2rgb(vec3 yuv) {
    return mat3(
        1.0,    1.0,   1.0,
        0.0,   -0.395, 2.032,
        1.14,  -0.581, 0.0
    ) * yuv;
}


// ========================================================================
// MAIN — Complete signal flow in one pass
// ========================================================================
void main() {
    vec2 tc = uv;
    vec4 input_color = texture(tex0, uv);

    // ================================================================
    // STAGE 0: AUDIO SIGNAL PREPARATION (needed for patchbay routing)
    // ================================================================
    float audio_signal = 0.0;

    if (noise_enable >= 5.0) {
        if (noise_type >= 5.0) {
            audio_signal = pink_noise(uv * resolution, time) * 2.0 - 1.0;
        } else {
            audio_signal = white_noise(uv * resolution, time) * 2.0 - 1.0;
        }
    } else {
        audio_signal = u_audio_level * 2.0 - 1.0;
    }

    // Amplifier processing
    float processed_audio;
    if (amp_bypass >= 5.0) {
        processed_audio = audio_signal;
    } else if (amp_enable >= 5.0) {
        float gain = amp_gain / 5.0;
        processed_audio = audio_signal * gain;
        processed_audio = tanh(processed_audio);
    } else {
        processed_audio = 0.0;
    }

    float env_speed = envelope_speed / 10.0;
    float smoothed_audio = abs(processed_audio);
    smoothed_audio = mix(smoothed_audio, smoothed_audio * smoothed_audio, 1.0 - env_speed);

    // ================================================================
    // STAGE 0b: OSCILLATOR SIGNAL PREPARATION (needed for patchbay)
    // ================================================================
    float osc_value = 0.0;
    if (osc_enable >= 5.0) {
        float rate_norm = rate / 10.0;
        float freq;
        if (range_select >= 5.0) {
            freq = mix(15.0, 15000.0, rate_norm);
        } else {
            freq = mix(0.01, 5.0, rate_norm);
        }
        float phase_global = time * freq;
        float phase;
        if (range_select >= 5.0) {
            float scanline_phase = uv.y * freq / 60.0;
            phase = phase_global + scanline_phase;
        } else {
            phase = phase_global;
        }
        osc_value = generate_wave(phase, shape);
    }

    // ================================================================
    // STAGE 1: DIRECTIONAL SHIFT — Scroll the framebuffer
    // ================================================================
    // Combine direct controls with CV inputs
    float eff_shift_up    = shift_up    + cv_up    / 10.0 * 5.0;
    float eff_shift_down  = shift_down  + cv_down  / 10.0 * 5.0;
    float eff_shift_left  = shift_left  + cv_left  / 10.0 * 5.0;
    float eff_shift_right = shift_right + cv_right / 10.0 * 5.0;

    // Patchbay: audio → directional shift
    float patch_shift = patch_audio_to_shift / 10.0;
    if (patch_sw2 >= 5.0 && patch_shift > 0.01) {
        eff_shift_up   += smoothed_audio * patch_shift * 3.0;
        eff_shift_left += smoothed_audio * patch_shift * 2.0;
    }

    // Apply horizontal shift (if not bypassed)
    if (bypass_h < 5.0) {
        float h_shift = (eff_shift_right - eff_shift_left) / 10.0 * 0.02;
        tc.x = fract(tc.x + h_shift);
    }

    // Apply vertical shift (if not bypassed)
    if (bypass_v < 5.0) {
        float v_shift = (eff_shift_up - eff_shift_down) / 10.0 * 0.02;
        tc.y = fract(tc.y + v_shift);
    }

    // ================================================================
    // STAGE 2: ZOOM — Scale from center
    // ================================================================
    float eff_zoom = zoom + cv_zoom / 10.0 * 2.0;

    // Patchbay: oscillator → zoom
    float patch_zoom_osc = patch_osc_to_zoom / 10.0;
    if (patch_sw1 >= 5.0 && patch_zoom_osc > 0.01) {
        eff_zoom += osc_value * patch_zoom_osc * 2.0;
    }

    // Patchbay: audio → zoom
    float patch_zoom_aud = patch_audio_to_zoom / 10.0;
    if (patch_sw4 >= 5.0 && patch_zoom_aud > 0.01) {
        eff_zoom += smoothed_audio * patch_zoom_aud * 2.0;
    }

    if (bypass_zoom < 5.0) {
        float zoom_factor = pow(2.0, (eff_zoom - 5.0) / 5.0);
        tc = (tc - 0.5) / zoom_factor + 0.5;
    }

    // ================================================================
    // STAGE 3: SAMPLE FEEDBACK FRAME
    // ================================================================
    float fb_amt = feedback_amount / 10.0;
    vec4 feedback_color = texture(texPrev, tc);

    // ================================================================
    // STAGE 4: FREEZE / FRAME HOLD
    // ================================================================
    float eff_freeze = freeze;

    // Patchbay: oscillator → freeze
    float patch_frz = patch_osc_to_freeze / 10.0;
    if (patch_sw3 >= 5.0 && patch_frz > 0.01) {
        eff_freeze += (osc_value * 0.5 + 0.5) * patch_frz * 10.0;
    }

    // Oscillator send to freeze
    if (osc_enable >= 5.0 && send_freeze >= 5.0) {
        float depth_amt = depth / 10.0;
        if (range_select < 5.0) {
            // Low range: periodic full-frame freeze
            if (osc_value > 0.0) {
                feedback_color = texture(texPrev, uv);
            }
        } else {
            // High range: slit-scan effect
            float scan_gate = step(0.0, osc_value) * depth_amt;
            feedback_color = mix(feedback_color, texture(texPrev, uv), scan_gate);
        }
    }

    if (eff_freeze >= 5.0) {
        feedback_color = texture(texPrev, uv);
    }

    // ================================================================
    // STAGE 5: EDGE SOFTENING — Analog bandwidth limits
    // ================================================================
    float blur_amt = edge_blur / 10.0;
    if (blur_amt > 0.01) {
        vec2 texel = 1.0 / resolution;
        float spread = blur_amt * 2.0;

        vec4 blurred = feedback_color * 4.0;
        blurred += texture(texPrev, tc + vec2(-texel.x, 0.0) * spread);
        blurred += texture(texPrev, tc + vec2( texel.x, 0.0) * spread);
        blurred += texture(texPrev, tc + vec2(0.0, -texel.y) * spread);
        blurred += texture(texPrev, tc + vec2(0.0,  texel.y) * spread);
        blurred += texture(texPrev, tc + vec2(-texel.x, -texel.y) * spread) * 0.5;
        blurred += texture(texPrev, tc + vec2( texel.x, -texel.y) * spread) * 0.5;
        blurred += texture(texPrev, tc + vec2(-texel.x,  texel.y) * spread) * 0.5;
        blurred += texture(texPrev, tc + vec2( texel.x,  texel.y) * spread) * 0.5;
        feedback_color = blurred / 8.0;
    }

    // ================================================================
    // STAGE 6: SIGNAL DEGRADATION — Analog loss per loop
    // ================================================================
    float decay_amt = decay / 10.0;
    if (decay_amt > 0.01) {
        // Slight desaturation per loop (analog color loss)
        float luma = dot(feedback_color.rgb, vec3(0.299, 0.587, 0.114));
        feedback_color.rgb = mix(feedback_color.rgb, vec3(luma), decay_amt * 0.15);

        // Subtle brightness reduction
        feedback_color.rgb *= (1.0 - decay_amt * 0.05);

        // Tiny chroma shift (analog signal crosstalk)
        float shift_amt = decay_amt * 0.003;
        feedback_color.r = texture(texPrev, tc + vec2(shift_amt, 0.0)).r * (1.0 - decay_amt * 0.03)
                          + feedback_color.r * (decay_amt * 0.03);

        // Natural saturation buildup (characteristic of analog feedback)
        float sat = dot(abs(feedback_color.rgb - vec3(luma)), vec3(1.0));
        feedback_color.rgb = mix(feedback_color.rgb,
                                  feedback_color.rgb * (1.0 + sat * 0.15),
                                  fb_amt * 0.5);
    }

    // ================================================================
    // STAGE 7: RGB MIX — Independent channel gain
    // ================================================================
    // Include CV modulation for RGB
    float r_gain = (red_mix   + cv_red   / 10.0 * 2.5) / 5.0;
    float g_gain = (green_mix + cv_green / 10.0 * 2.5) / 5.0;
    float b_gain = (blue_mix  + cv_blue  / 10.0 * 2.5) / 5.0;

    feedback_color.r *= r_gain;
    feedback_color.g *= g_gain;
    feedback_color.b *= b_gain;

    // ================================================================
    // STAGE 8: RGB PULSE — Full-intensity color injection
    // ================================================================
    if (red_pulse >= 5.0) {
        feedback_color.r = max(feedback_color.r, 1.0);
    }
    if (green_pulse >= 5.0) {
        feedback_color.g = max(feedback_color.g, 1.0);
    }
    if (blue_pulse >= 5.0) {
        feedback_color.b = max(feedback_color.b, 1.0);
    }

    // ================================================================
    // STAGE 9: OSCILLATOR MODULATION — Per-channel sends
    // ================================================================
    if (osc_enable >= 5.0) {
        float depth_amt = depth / 10.0;
        float mod_value = osc_value * 0.5 + 0.5;  // Scale to 0-1

        if (send_red >= 5.0) {
            float phase_r = osc_value;  // No offset for red
            float mod_r = phase_r * 0.5 + 0.5;
            if (range_select >= 5.0) {
                feedback_color.r = mix(feedback_color.r, feedback_color.r * (0.5 + mod_r * depth_amt), depth_amt);
            } else {
                feedback_color.r = mix(feedback_color.r, mod_r * depth_amt, depth_amt * 0.7);
            }
        }

        if (send_green >= 5.0) {
            // Phase offset for green channel — creates color separation
            float phase_g_val = generate_wave(time * mix(0.01, range_select >= 5.0 ? 15000.0 : 5.0, rate / 10.0) + 0.333, shape);
            float mod_g = phase_g_val * 0.5 + 0.5;
            if (range_select >= 5.0) {
                feedback_color.g = mix(feedback_color.g, feedback_color.g * (0.5 + mod_g * depth_amt), depth_amt);
            } else {
                feedback_color.g = mix(feedback_color.g, mod_g * depth_amt, depth_amt * 0.7);
            }
        }

        if (send_blue >= 5.0) {
            float phase_b_val = generate_wave(time * mix(0.01, range_select >= 5.0 ? 15000.0 : 5.0, rate / 10.0) + 0.666, shape);
            float mod_b = phase_b_val * 0.5 + 0.5;
            if (range_select >= 5.0) {
                feedback_color.b = mix(feedback_color.b, feedback_color.b * (0.5 + mod_b * depth_amt), depth_amt);
            } else {
                feedback_color.b = mix(feedback_color.b, mod_b * depth_amt, depth_amt * 0.7);
            }
        }
    }

    // ================================================================
    // STAGE 10: AUDIO MODULATION — Per-channel RGB sends
    // ================================================================
    float a_send_r = audio_send_red / 10.0;
    float a_send_g = audio_send_green / 10.0;
    float a_send_b = audio_send_blue / 10.0;

    if (a_send_r > 0.01) {
        float r_mod = smoothed_audio;
        if (noise_enable < 5.0) {
            r_mod = mix(smoothed_audio, u_bass, 0.5);
        }
        feedback_color.r = mix(feedback_color.r, feedback_color.r + r_mod, a_send_r);
    }

    if (a_send_g > 0.01) {
        float g_mod = smoothed_audio;
        if (noise_enable < 5.0) {
            g_mod = mix(smoothed_audio, u_mid, 0.5);
        }
        feedback_color.g = mix(feedback_color.g, feedback_color.g + g_mod, a_send_g);
    }

    if (a_send_b > 0.01) {
        float b_mod = smoothed_audio;
        if (noise_enable < 5.0) {
            b_mod = mix(smoothed_audio, u_high, 0.5);
        }
        feedback_color.b = mix(feedback_color.b, feedback_color.b + b_mod, a_send_b);
    }

    // ================================================================
    // STAGE 11: MIX FEEDBACK WITH INPUT
    // ================================================================
    vec4 result = mix(input_color, feedback_color, fb_amt);

    // ================================================================
    // STAGE 12: PHOSPHOR PERSISTENCE — CRT afterimage
    // ================================================================
    float persist_amt = persistence / 10.0;
    if (persist_amt > 0.01) {
        vec4 prev_frame = texture(texPrev, uv);
        // Blend with decaying previous frame for phosphor trail
        result = mix(result, max(result, prev_frame * persist_amt), persist_amt * 0.5);
    }

    // ================================================================
    // STAGE 13: BRIGHTNESS
    // ================================================================
    float bright_offset = (brightness - 5.0) / 10.0;
    result.rgb += bright_offset;

    // ================================================================
    // STAGE 14: CONTRAST
    // ================================================================
    float contrast_mult = contrast / 5.0;
    result.rgb = (result.rgb - 0.5) * contrast_mult + 0.5;

    // ================================================================
    // STAGE 15: SATURATION + HUE
    // ================================================================
    float sat_mult = saturation / 5.0;
    vec3 hsv = rgb2hsv(result.rgb);
    hsv.y *= sat_mult;
    hsv.y = clamp(hsv.y, 0.0, 1.0);

    float hue_shift = hue_rotate / 10.0;
    hsv.x = fract(hsv.x + hue_shift);

    result.rgb = hsv2rgb(hsv);

    // ================================================================
    // STAGE 16: COMPOSITE VIDEO SIMULATION
    // ================================================================
    if (composite_enable >= 5.0) {
        vec2 comp_tc = uv;

        // --- Horizontal sync jitter ---
        float h_jitter = sync_jitter / 10.0;
        if (h_jitter > 0.01) {
            float scanline = floor(comp_tc.y * resolution.y);
            float jitter = hash(vec2(scanline, floor(time * 60.0)));
            jitter = jitter * 2.0 - 1.0;

            // Occasional larger glitches
            float spike = step(0.95 - h_jitter * 0.3, abs(jitter));
            jitter *= spike;
            comp_tc.x = fract(comp_tc.x + jitter * h_jitter * 0.015);
        }

        // --- Vertical drift ---
        float v_drift = vertical_drift / 10.0;
        if (v_drift > 0.01) {
            float drift_offset = sin(time * 0.3) * v_drift * 0.005;
            drift_offset += sin(time * 1.7) * v_drift * 0.002;
            comp_tc.y = fract(comp_tc.y + drift_offset);
        }

        // --- VHS tracking error bars ---
        float vhs = vhs_tracking / 10.0;
        if (vhs > 0.01) {
            float bar_pos = fract(time * 0.1) * 1.2 - 0.1;
            float bar_width = 0.02 + vhs * 0.05;
            float in_bar = smoothstep(bar_pos - bar_width, bar_pos, comp_tc.y)
                         - smoothstep(bar_pos, bar_pos + bar_width, comp_tc.y);

            float bar_noise = hash(vec2(floor(comp_tc.y * resolution.y), floor(time * 30.0)));
            comp_tc.x = fract(comp_tc.x + in_bar * bar_noise * vhs * 0.1);
        }

        // --- Interlace simulation ---
        float interlace_fade = 1.0;
        if (interlace >= 5.0) {
            float scanline = floor(comp_tc.y * resolution.y);
            float field = mod(floor(time * 60.0), 2.0);
            if (mod(scanline + field, 2.0) < 1.0) {
                interlace_fade = 0.7;
            }
        }

        // Re-sample with displacement
        vec4 comp_sample = texture(tex0, comp_tc);
        // Blend composite artifacts into result
        result.rgb = mix(result.rgb, comp_sample.rgb, 0.0);  // UV displacement already applied

        // --- Chroma / luma separation artifacts ---
        float bleed = chroma_bleed / 10.0;
        if (bleed > 0.01) {
            vec2 texel = 1.0 / resolution;

            if (ntsc_pal < 5.0) {
                // NTSC mode — YIQ
                vec3 yiq_center = rgb2yiq(result.rgb);
                vec3 yiq_left   = rgb2yiq(texture(texPrev, tc + vec2(-texel.x * 2.0, 0.0)).rgb);
                vec3 yiq_right  = rgb2yiq(texture(texPrev, tc + vec2( texel.x * 2.0, 0.0)).rgb);

                float y = yiq_center.x;
                float i = mix(yiq_center.y, (yiq_left.y + yiq_center.y + yiq_right.y) / 3.0, bleed);
                float q = mix(yiq_center.z, (yiq_left.z + yiq_center.z + yiq_right.z) / 3.0, bleed);

                result.rgb = yiq2rgb(vec3(y, i, q));
            } else {
                // PAL mode — YUV
                vec3 yuv_center = rgb2yuv(result.rgb);
                vec3 yuv_left   = rgb2yuv(texture(texPrev, tc + vec2(-texel.x * 2.0, 0.0)).rgb);
                vec3 yuv_right  = rgb2yuv(texture(texPrev, tc + vec2( texel.x * 2.0, 0.0)).rgb);

                float y = yuv_center.x;
                float u = mix(yuv_center.y, (yuv_left.y + yuv_center.y + yuv_right.y) / 3.0, bleed);
                float v = mix(yuv_center.z, (yuv_left.z + yuv_center.z + yuv_right.z) / 3.0, bleed);

                result.rgb = yuv2rgb(vec3(y, u, v));
            }
        }

        // --- Dot crawl (NTSC characteristic) ---
        float crawl = dot_crawl / 10.0;
        if (crawl > 0.01 && ntsc_pal < 5.0) {
            float scanline = floor(uv.y * resolution.y);
            float dot_phase = uv.x * resolution.x * 0.5 + scanline * 0.5 + time * 15.0;
            float dot_pattern = sin(dot_phase * 6.28318) * crawl * 0.1;

            result.r += dot_pattern;
            result.b -= dot_pattern;
        }

        // --- Signal clipping ---
        float clip = signal_clip / 10.0;
        if (clip > 0.01) {
            float clip_threshold = 1.0 - clip * 0.4;
            float clip_floor = clip * 0.1;

            result.rgb = smoothstep(clip_floor, clip_threshold, result.rgb);
            result.rgb = mix(result.rgb, step(0.5, result.rgb), clip * 0.3);
        }

        // --- Analog noise ---
        float noise_amt = noise_amount / 10.0;
        if (noise_amt > 0.01) {
            float n = hash(uv * resolution + time * 100.0) * 2.0 - 1.0;
            result.rgb += n * noise_amt * 0.1;
        }

        // Apply interlace fade
        result.rgb *= interlace_fade;
    }

    // ================================================================
    // FINAL OUTPUT
    // ================================================================
    result.rgb = clamp(result.rgb, 0.0, 1.0);
    fragColor = mix(texture(tex0, uv), result, u_mix);
}
"""

class Vimana(Effect):
    """
    Vimana GVS010 - Unified Software Emulation.
    
    METADATA:
    The parameters below are a MIRROR of the original manifest.json.
    This structure effectively 'documents itself' to any Agent reading the code.
    """
    
    # Embedded Manifest - The Source of Truth
    METADATA = {
      "id": "vvimana_synth",
      "name": "Vimana GVS010",
      "params": [
        {"id": "shift_up", "name": "Shift Up", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "shift_down", "name": "Shift Down", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "shift_left", "name": "Shift Left", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "shift_right", "name": "Shift Right", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "zoom", "name": "Zoom", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "freeze", "name": "Freeze", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "feedback_amount", "name": "Feedback", "default": 8.0, "min": 0.0, "max": 10.0},
        {"id": "decay", "name": "Decay", "default": 2.0, "min": 0.0, "max": 10.0},
        {"id": "edge_blur", "name": "Edge Blur", "default": 3.0, "min": 0.0, "max": 10.0},
        {"id": "persistence", "name": "Persistence", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "bypass_h", "name": "Bypass H", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "bypass_v", "name": "Bypass V", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "bypass_zoom", "name": "Bypass Zoom", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "red_mix", "name": "Red Mix", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "green_mix", "name": "Green Mix", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "blue_mix", "name": "Blue Mix", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "red_pulse", "name": "Red Pulse", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "green_pulse", "name": "Green Pulse", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "blue_pulse", "name": "Blue Pulse", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "osc_enable", "name": "Osc Enable", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "rate", "name": "Rate", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "shape", "name": "Shape", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "depth", "name": "Depth", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "range_select", "name": "Range", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "send_red", "name": "Send Red", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "send_green", "name": "Send Green", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "send_blue", "name": "Send Blue", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "send_freeze", "name": "Send Freeze", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "amp_enable", "name": "Amp Enable", "default": 10.0, "min": 0.0, "max": 10.0},
        {"id": "amp_gain", "name": "Amp Gain", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "amp_bypass", "name": "Amp Bypass", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "noise_enable", "name": "Noise Enable", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "noise_type", "name": "Noise Type", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "audio_send_red", "name": "Audio → Red", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "audio_send_green", "name": "Audio → Green", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "audio_send_blue", "name": "Audio → Blue", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "envelope_speed", "name": "Envelope Speed", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "brightness", "name": "Brightness", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "contrast", "name": "Contrast", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "saturation", "name": "Saturation", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "hue_rotate", "name": "Hue Rotate", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "composite_enable", "name": "Composite Enable", "default": 10.0, "min": 0.0, "max": 10.0},
        {"id": "sync_jitter", "name": "Sync Jitter", "default": 3.0, "min": 0.0, "max": 10.0},
        {"id": "vertical_drift", "name": "V-Drift", "default": 1.0, "min": 0.0, "max": 10.0},
        {"id": "chroma_bleed", "name": "Chroma Bleed", "default": 5.0, "min": 0.0, "max": 10.0},
        {"id": "dot_crawl", "name": "Dot Crawl", "default": 3.0, "min": 0.0, "max": 10.0},
        {"id": "signal_clip", "name": "Signal Clip", "default": 2.0, "min": 0.0, "max": 10.0},
        {"id": "interlace", "name": "Interlace", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "ntsc_pal", "name": "NTSC/PAL", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "noise_amount", "name": "Noise", "default": 2.0, "min": 0.0, "max": 10.0},
        {"id": "vhs_tracking", "name": "VHS Tracking", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "patch_sw1", "name": "Patch SW1", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "patch_sw2", "name": "Patch SW2", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "patch_sw3", "name": "Patch SW3", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "patch_sw4", "name": "Patch SW4", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "patch_osc_to_zoom", "name": "Osc → Zoom", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "patch_audio_to_shift", "name": "Audio → Shift", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "patch_osc_to_freeze", "name": "Osc → Freeze", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "patch_audio_to_zoom", "name": "Audio → Zoom", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "cv_red", "name": "CV Red", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "cv_green", "name": "CV Green", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "cv_blue", "name": "CV Blue", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "cv_up", "name": "CV Up", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "cv_down", "name": "CV Down", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "cv_left", "name": "CV Left", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "cv_right", "name": "CV Right", "default": 0.0, "min": 0.0, "max": 10.0},
        {"id": "cv_zoom", "name": "CV Zoom", "default": 0.0, "min": 0.0, "max": 10.0}
      ]
    }

    def __init__(self):
        super().__init__("vimana", VIMANA_FRAGMENT)
        self._hydrate_parameters()
        
    def _hydrate_parameters(self):
        """Hydrate parameter dictionary from the metadata source of truth."""
        for param in self.METADATA["params"]:
            self.parameters[param["id"]] = param["default"]
            
    def get_manifest(self) -> Dict[str, Any]:
        """Return the embedded manifest for agent introspection."""
        return self.METADATA
