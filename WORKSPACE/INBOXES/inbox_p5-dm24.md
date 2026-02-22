# Task Assignment: P5-DM24

> **From:** Manager (ROO CODE)
> **To:** Implementation Engineer (Alpha)
> **Task ID:** `P5-DM24`
> **Plugin:** mosh_pit_datamosh
> **Spec:** `docs/specs/P5-P5-DM24_mosh_pit_datamosh.md`
> **Priority:** P0 (Critical)
> **Phase:** Phase 5

## Mission

Port the `mosh_pit_datamosh` effect from the legacy codebases into VJLive3's clean architecture. This is a **bespoke** plugin port — treat it as a unique snowflake, not a batch job.

## Immediate Actions

1. Read the specification file: `docs/specs/P5-P5-DM24_mosh_pit_datamosh.md`
2. Study the original implementation in the legacy codebase (see spec for location)
3. Create the plugin file in `src/vjlive3/plugins/`
4. Implement the effect following VJLive3 patterns
5. Write comprehensive tests in `tests/plugins/`
6. Verify 60 FPS performance and ≥80% test coverage
7. Update BOARD.md status to ✅ Done
8. Notify Manager via the Antigravity Chat

## Technical Constraints

- **60 FPS Sacred:** No frame drops
- **750-Line Limit:** Keep files concise
- **80% Coverage:** Minimum test coverage
- **Zero Silent Failures:** All errors must be explicit
- **Bespoke Treatment:** Every plugin gets individual attention

## Workflow

```
SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD
```

Do not proceed to next task until this one is complete and verified.

## Resources

- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system: `src/vjlive3/plugins/`
- Examples: See existing plugins in `src/vjlive3/plugins/` (depth_*, audio_*, etc.)
- Base classes: `Effect`, `DepthEffect`, `AudioEffect` as appropriate

## Communication

- Use Antigravity Chat for questions
- Report any blockers immediately
- Document any deviations from original behavior

**Remember:** The best code is code that knows what it is and does it well.

