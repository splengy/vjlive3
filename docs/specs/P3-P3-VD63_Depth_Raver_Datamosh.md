# P3-VD63: Depth Raver Datamosh

> **Task ID:** `P3-VD63`  
> **Priority:** P0 (Critical)  
> **Source:** VJlive-2 (`plugins/vdepth/depth_raver_datamosh.py`)  
> **Class:** `DepthRaverDatamoshEffect`  
> **Phase:** Phase 3  
> **Status:** ⬜ Todo  

## Mission Context

Port the `DepthRaverDatamoshEffect` effect from `VJlive-2` codebase into VJLive3's clean architecture. This plugin is part of the Depth collection and is essential for complete feature parity.

## Technical Requirements

- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from appropriate base class (likely `Effect` or specialized depth/audio base)
- Ensure 60 FPS performance (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)

## Implementation Notes

**Original Location:** `VJlive-2/plugins/vdepth/depth_raver_datamosh.py`  
**Description:** No description available

### Porting Strategy

1. Study the original implementation in `VJlive-2/plugins/vdepth/depth_raver_datamosh.py`
2. Identify dependencies and required resources (shaders, textures, etc.)
3. Adapt to VJLive3's plugin architecture (see `src/vjlive3/plugins/`)
4. Write comprehensive tests (≥80% coverage)
5. Verify against original behavior with test vectors
6. Document any deviations or improvements

## Verification Checkpoints

- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum
- [ ] Test coverage ≥80%
- [ ] No safety rail violations
- [ ] Original functionality verified (side-by-side comparison)

## Resources

- Original source: `VJlive-2/plugins/vdepth/depth_raver_datamosh.py`
- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system spec: `docs/specs/P1-P1_plugin_registry.md` (or appropriate)
- Base classes: `src/vjlive3/plugins/`, `src/vjlive3/render/`

## Dependencies

- [ ] List any dependencies on other plugins or systems

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

