"""
vjlive3.effects
===============
Visual effect plugin implementations — the artisanal snowflakes.

This package holds the ported effect plugins themselves.
Each plugin lives in its own subdirectory:
    effects/
        depth/       — Phase 3: depth camera effects
        audio/       — Phase 4: audio-reactive effects
        visual/      — Phase 5: V-* visual effects, modulators, datamosh
        neural/      — Phase 6: AI/neural effects (Dreamer tier)

Migration rules (PRIME_DIRECTIVE.md ADR-006):
    ONE plugin at a time. No batch processing.
    Each plugin must have a complete plugin.json manifest (SAFETY_RAILS.md Rail 3).
    Effect class signature: __init__(self, params) + process(self, frame, audio_data)
    Preserve "soul" — comments, weird logic, creative descriptions.

Reference: bespoke-plugin-migration workflow
"""
