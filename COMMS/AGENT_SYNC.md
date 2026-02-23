### 2026-02-23 — Manager — RESEARCH COMPLETE
**Task:** RESEARCH:P3-EXT078
**Found in v1:** vjlive/core/effects/shadertoy_particles.py — FireParticles
**Found in v2:** VJlive-2/core/effects/shadertoy_particles.py — FireParticles
**Port decision:** v2 — Preserves the sentience AI params and accurate numpy physics loops
**Spec updated:** yes — Created new docs/specs/P3-EXT078_fire_particles_effect.md
**Ready for:** Coding task P3-EXT078 can now proceed

### 2026-02-23 — Manager — RESEARCH COMPLETE
**Task:** RESEARCH:P3-EXT074
**Found in v1:** vjlive/effects/erbe_verb.py
**Found in v2:** vjlive/effects/shaders/shaders/erbe_verb.frag
**Port decision:** Maintain exact shader logic and procedural noise generation while rewriting the OpenGL framebuffer ping-pong logic utilizing modern VJLive3 Context injection.
**Spec updated:** yes — Created docs/specs/P3-EXT074_erbe_verb_effect.md
**Ready for:** Coding task P3-EXT074 can now proceed

### 2026-02-23 — Manager — RESEARCH COMPLETE
**Task:** RESEARCH:P3-EXT075
**Found in v1:** vjlive/effects/example_glitch.py
**Port decision:** Port the CPU-bound OpenCV array manipulations (pixelation, rgb split, scanlines, corruption) directly into a highly efficient GLSL fragment shader, bypassing the legacy np.random bottleneck.
**Spec updated:** yes — Created docs/specs/P3-EXT075_example_glitch_effect.md
**Ready for:** Coding task P3-EXT075 can now proceed

### 2026-02-23 — Manager — RESEARCH COMPLETE
**Task:** RESEARCH:P3-EXT142
**Found in v2:** VJlive-2/plugins/vdepth/r16_simulated_depth.py
**Port decision:** Port the legacy offline CPU `np.uint16` array generation logic into a true GPU-bound OpenGL Fragment Shader using an FBO and `GL_R16` target to generate standardized depth textures at 60 FPS natively.
**Spec updated:** yes — Created docs/specs/P3-EXT142_r16_simulated_depth.md
**Ready for:** Coding task P3-EXT142 can now proceed
