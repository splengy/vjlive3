# P7-VE52: Plugin Template (Guidance)

> **Task ID:** `P7-VE52`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/plugin_template.py`)
> **Class:** `CustomEffect` (template)
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out (guideline)

## Mission Context
This document serves as a template and checklist for authoring *any* new
plugin in the VJLive3 ecosystem. It can be copied and adapted when porting
existing effects or creating originals. The original `plugin_template.py`
merely provided an example skeleton; we capture its advice here so that the
pipeline remains consistent.

## Technical Requirements (for any plugin)
- Must register via the central manifest/registry system
- Subclass an appropriate base (`Effect`, `Generator`, etc.)
- Respect safety rails: 60 FPS on 1080p, ≥80 % tests, <750 lines, explicit
  error handling

## Implementation Notes
- Follow existing examples in `src/vjlive3/plugins/` for structure and naming
- Provide clear parameter ranges, descriptions, and sweet spots
- Support GPU and CPU code paths where appropriate
- Ensure parameter remapping from 0–10 sliders is documented

### Typical Porting Strategy
1. Locate original implementation (source file, class names, shaders)
2. Extract core logic and convert to GPU-friendly math (GLSL) or NumPy
3. Define the public interface and metadata (tags, features, usage)
4. Write comprehensive tests including regression vectors
5. Validate performance and correct any safety-rail violations
6. Document in a spec similar to this one

## Verification Checklist (generic)
- [ ] Plugin appears in registry and is selectable in UI
- [ ] All parameters are editable and have sane defaults
- [ ] GPU renderer works; CPU fallback exists if needed
- [ ] Tests pass and coverage is ≥80 %
- [ ] Performance meets 60 FPS requirement

## Resources
- Plugin system spec: `docs/specs/P1-P1_plugin_registry.md`
- Existing plugins for reference in `src/vjlive3/plugins/`
- Audit report for security practices `docs/audit_report_comprehensive.json`

## Dependencies
List external modules, shaders, or texture assets required by the plugin.

---

**Tip:** Start with this template when creating a new plugin; replace the
above sections with specifics for your effect. Remove or rename as appropriate.

