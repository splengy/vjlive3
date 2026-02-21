"""
vjlive3.rendering
=================
OpenGL rendering pipeline for VJLive3.

Sub-modules (added as Phase 1 tasks complete):
    context    — P1-R1: ModernGL + GLFW context management (RAII)
    pipeline   — P1-R2: GPU pipeline + framebuffer management
    shaders    — P1-R3: GLSL shader compilation + caching
    textures   — P1-R4: Texture pool (leak-free, RAII)
    engine     — P1-R5: 60fps render loop

Import pattern — ALL sub-modules use lazy imports for OpenGL:
    Do NOT import moderngl or OpenGL at module top-level.
    Import inside class __init__ or a _get_context() factory only.
    Reason: each OpenGL import adds 100-500ms startup penalty.

Reference: VJlive-2/core/opengl_raii.py, engine.py, renderer.py
"""
