# Task Assignment: P3-EXT113 - NebulaParticles

**Agent:** Implementation Engineer (Alpha)  
**Task ID:** P3-EXT113  
**Priority:** P0  
**Assigned:** 2026-02-23  
**Status:** Ready for Implementation

---

## Specification Summary

Implement the NebulaParticles plugin - a Shadertoy-based particle system that creates nebula/gas cloud effects with organic, flowing motion and audio-reactive behaviors.

**Spec File:** `docs/specs/P3-EXT113_NebulaParticles.md`

### Key Requirements

- Build on `ShadertoyParticles` base class
- Implement 300 particles with organic flow motion
- Add audio-reactive swirling (mid frequencies) and expansion (bass frequencies)
- Support real-time audio input (volume, bass, mid, treble, beat)
- Achieve 60 FPS at 1080p on RTX 4070 Ti Super
- ≥ 85% test coverage
- Zero safety rail violations
- ≤ 750 lines of code, full type hints, no stubs

### Deliverables

1. `src/vjlive3/plugins/nebula_particles.py` - Main plugin implementation
2. `tests/plugins/test_nebula_particles.py` - Comprehensive test suite  
3. `docs/plugins/nebula_particles.md` - User documentation
4. Update `MODULE_MANIFEST.md` with plugin entry

### Success Criteria

- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Audio-reactive effects verified with real audio input
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints

---

## Implementation Instructions

1. Read the full spec: `docs/specs/P3-EXT113_NebulaParticles.md`
2. Study existing particle system plugins for patterns (e.g., `shadertoy_particles.py`, `particles_3d.py`)
3. Implement the plugin following VJLive3 architecture standards
4. Write comprehensive tests before/during implementation (TDD approach)
5. Verify all safety rails are enforced
6. Profile performance and optimize as needed
7. Document the plugin with docstrings and user guide
8. Update `MODULE_MANIFEST.md` with plugin metadata

### References

- Base class: `src/vjlive3/plugins/shadertoy_particles.py` (ShadertoyParticles)
- Similar implementation: `src/vjlive3/plugins/shadertoy_particles.py` (FireParticles)
- Test examples: `tests/plugins/test_shadertoy_particles.py`
- Architecture: `docs/specs/P3-EXT113_NebulaParticles.md`

---

**Start implementation when ready. Report progress via the switchboard.**