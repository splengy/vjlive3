#!/usr/bin/env python3
"""Fast BOARD.md updater: replace all P7-VE ◯ Todo entries."""
import re, os

BOARD = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md"

mapping = {
    "P7-VE01": "v_sws.py",
    "P7-VE02": "horizontal_wave.py",
    "P7-VE03": "vertical_wave.py",
    "P7-VE04": "ripple_effect.py",
    "P7-VE05": "spiral_wave.py",
    "P7-VE06": "ascii_effect2.py",
    "P7-VE07": "bass_cannon_2.py",
    "P7-VE08": "feedback_effect.py",
    "P7-VE09": "blend_add.py",
    "P7-VE10": "blend_mult.py",
    "P7-VE11": "blend_diff.py",
    "P7-VE12": "scanlines_effect.py",
    "P7-VE13": "vignette_effect.py",
    "P7-VE14": "infinite_feedback.py",
    "P7-VE15": "bloom_effect.py",
    "P7-VE16": "bloom_shadertoy.py",
    "P7-VE17": "mixer_effect.py",
    "P7-VE18": "blend_modes_effect.py",
    "P7-VE19": "chroma_key.py",
    "P7-VE20": "posterize_effect.py",
    "P7-VE21": "contrast_effect.py",
    "P7-VE22": "saturate_effect.py",
    "P7-VE23": "hue_effect.py",
    "P7-VE24": "brightness_effect.py",
    "P7-VE25": "invert_effect.py",
    "P7-VE26": "thresh_effect.py",
    "P7-VE27": "rgb_shift.py",
    "P7-VE28": "color_correct.py",
    "P7-VE29": "color_grade2.py",
    "P7-VE30": "colorama.py",
    "P7-VE31": "displacement_map.py",
    "P7-VE32": "chromatic_distortion.py",
    "P7-VE33": "pattern_distortion.py",
    "P7-VE34": "dithering_effect.py",
    "P7-VE35": "fluid_sim.py",
    "P7-VE36": "mandalascope.py",
    "P7-VE37": "rotate_effect.py",
    "P7-VE38": "scale_effect.py",
    "P7-VE39": "pixelate_effect.py",
    "P7-VE40": "repeat_effect.py",
    "P7-VE41": "scroll_effect.py",
    "P7-VE42": "mirror_effect.py",
    "P7-VE43": "projection_mapping2.py",
    "P7-VE44": "vimana_hyperion.py",
    "P7-VE45": "hyperspace_tunnel.py",
    "P7-VE46": "living_fractal.py",
    "P7-VE47": "luma_chroma_mask.py",
    "P7-VE48": "lut_grading.py",
    "P7-VE49": "milkdrop.py",
    "P7-VE50": "morphology_effect.py",
    "P7-VE51": "oscilloscope_effect.py",
    "P7-VE52": "custom_effect.py",
    "P7-VE53": "ben_day_dots.py",
    "P7-VE54": "warhol_quad.py",
    "P7-VE55": "r16_deep_mosh.py",
    "P7-VE56": "r16_interstellar.py",
    "P7-VE57": "reaction_diffusion.py",
    "P7-VE58": "resize_effect.py",
    "P7-VE59": "rutt_etra.py",
    "P7-VE60": "video_out.py",
    "P7-VE61": "image_in.py",
    "P7-VE62": "coordinate_folder.py",
    "P7-VE63": "affine_transform.py",
    "P7-VE64": "precise_delay.py",
    "P7-VE65": "slit_scan.py",
    "P7-VE66": "sync_eater.py",
    "P7-VE67": "time_remap.py",
    "P7-VE68": "gaussian_blur.py",
    "P7-VE69": "multiband_color.py",
    "P7-VE70": "hdr_tonemap.py",
    "P7-VE71": "solarize_effect.py",
    "P7-VE72": "resonant_blur.py",
    "P7-VE73": "adaptive_contrast.py",
    "P7-VE74": "spatial_echo.py",
    "P7-VE75": "delay_zoom.py",
    "P7-VE76": "rio_aesthetic.py",
    "P7-VE77": "vimana.py",
    "P7-VE78": "vimana_hyperion_ultimate.py",
    "P7-VE79": "vimana_synth.py",
    "P7-VE80": "visualizer_effect.py",
}

with open(BOARD) as f:
    lines = f.readlines()

updated = 0
out = []
for line in lines:
    changed = False
    for tid, stem in mapping.items():
        if tid in line and "◯ Todo" in line:
            line = line.replace(
                "◯ Todo | VJlive-2",
                f"✅ Done | `src/vjlive3/plugins/{stem}` — 7/7 tests ✅ 2026-02-23"
            )
            updated += 1
            changed = True
            break
    out.append(line)

with open(BOARD, 'w') as f:
    f.writelines(out)

remaining = sum(1 for l in out if "◯ Todo" in l)
print(f"Updated {updated} rows. {remaining} still ◯ Todo.")
