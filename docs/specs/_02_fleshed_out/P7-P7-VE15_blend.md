# P7-VE15: blend

> **Task ID:** `P7-VE15`  
> **Priority:** P0 (Critical)  
> **Source:** vjlive (`plugins/vcore/blend.py`)  
> **Class:** `BloomEffect`  
> **Phase:** Phase 7  
> **Status:** ⬜ Todo  

## Mission Context

Port the `BloomEffect` effect from `vjlive` codebase into VJLive3's clean architecture. This plugin is part of the Other collection and is essential for complete feature parity.

## Technical Requirements

- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from appropriate base class (likely `Effect` or specialized depth/audio base)
- Ensure 60 FPS performance (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)

## Implementation Notes

**Original Location:** `vjlive/plugins/vcore/blend.py`  
**Description:** No description available

### Porting Strategy

1. Study the original implementation in `vjlive/plugins/vcore/blend.py`
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

- Original source: `vjlive/plugins/vcore/blend.py`
- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system spec: `docs/specs/P1-P1_plugin_registry.md` (or appropriate)
- Base classes: `src/vjlive3/plugins/`, `src/vjlive3/render/`

## Dependencies

- [ ] List any dependencies on other plugins or systems

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

