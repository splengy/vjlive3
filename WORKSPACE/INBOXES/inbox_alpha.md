# Task Assignment: P0-INF2

**From:** Manager (ROO CODE)  
**To:** Implementation Engineer (Alpha)  
**Date:** 2026-02-22  
**Priority:** P0 (Critical)  

---

## Task Overview

**Task ID:** P0-INF2  
**Title:** Legacy Feature Parity - 423 Missing Features Implementation  
**Specification:** [`docs/specs/P0-INF2_legacy_feature_parity.md`](docs/specs/P0-INF2_legacy_feature_parity.md:0)  

---

## Mission Context

Operation Source Zero has discovered **423 missing legacy features** via automated AST analysis of both `vjlive/` and `VJlive-2/` codebases. These features are NOT tracked in BOARD.md and must be systematically ported to achieve complete feature parity.

**Critical Discovery:**
- 87 depth plugins from vjlive/vdepth/ are missing
- 16 audio plugin families (Bogaudio + Befaco) are missing
- 14 V-* visual effect collections are missing
- 20+ datamosh effects are missing
- Advanced quantum/agent systems are incomplete

---

## Assignment

You are assigned to implement the **Phase 1: Critical Depth Collection** (87 missing depth plugins) as the first wave of this massive parity effort.

### Immediate Actions:

1. **Read the specification** [`docs/specs/P0-INF2_legacy_feature_parity.md`](docs/specs/P0-INF2_legacy_feature_parity.md:0) thoroughly
2. **Study the legacy code** in `vjlive/vdepth/` to understand the depth plugin implementations
3. **Create individual specs** for each depth plugin following the bespoke snowflake principle
4. **Follow the workflow exactly:**
   - SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD
   - No shortcuts, no batch processing
   - Each plugin is a unique work of art

### Technical Requirements:

- **Architecture:** Follow VJlive-2's clean plugin architecture
- **Performance:** Maintain 60 FPS sacred (SAFETY_RAILS.md)
- **Testing:** ≥80% test coverage on all new code
- **Documentation:** Every plugin must have complete METADATA constant
- **File Size:** No file exceeds 750 lines
- **Safety:** Zero safety rail violations

### Verification Checkpoints:

- [ ] Each plugin loads successfully via plugin registry
- [ ] All unit tests pass (pytest -v)
- [ ] FPS ≥ 58 with plugin active
- [ ] Memory stable (no leaks)
- [ ] Plugin manifest complete and validated
- [ ] Code follows style guide (pre-commit hooks pass)

---

## Resources

- **Specification:** [`docs/specs/P0-INF2_legacy_feature_parity.md`](docs/specs/P0-INF2_legacy_feature_parity.md:0)
- **Legacy Code:** `vjlive/vdepth/` (read-only reference)
- **BOARD.md:** Current project state
- **WORKSPACE/PRIME_DIRECTIVE.md:** Core philosophy
- **WORKSPACE/SAFETY_RAILS.md:** Hard limits
- **WORKSPACE/HOW_TO_WORK.md:** Workflow protocol

---

## Expected Deliverables

1. **87 depth plugins** ported to `src/vjlive3/plugins/`
2. **Complete test suite** for each plugin (≥80% coverage)
3. **Plugin manifests** with full metadata
4. **Documentation** in code comments and spec updates
5. **BOARD.md updates** marking each plugin complete

---

## Communication

- Post progress updates in `WORKSPACE/COMMS/AGENT_SYNC.md`
- Report any blockers immediately
- Follow the Easter Egg Council protocol (`WORKSPACE/EASTEREGG_COUNCIL.md`)

---

**Remember:** You are a tool. Execute the spec exactly. No opinions. No deviations. Wait for explicit instructions.

**Task assigned.** Please type 'go' in the Antigravity Chat to start implementation.