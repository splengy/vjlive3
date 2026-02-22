# Implementation Tasks — P0-INF2: Legacy Feature Parity Phase 1

**Assigned By:** Manager
**Date:** 2026-02-22
**Priority:** P0 — Critical Depth Collection Porting

---

## Context
Worker Beta, your Phase 7 Business obligations are suspended. We are formally initiating the **P0-INF2 Legacy Feature Parity** protocol. 

The legacy codebases (`vjlive` and `VJlive-2`) house incredible depth, including 423 unique effect/plugin classes. We are saving the soul of this project.

You are assigned **Phase 1: Critical Depth Collection**. There are 87 depth processing plugins that must be ported from the legacy models to the new VJLive3 standard.

## Master Specification
Your absolute Source of Truth for this massive initiative is:
`docs/specs/P0-INF2_legacy_feature_parity.md`

## The Initial Workload
Begin porting the highest-priority depth plugins into `src/vjlive3/plugins/depth`:
1. `Depth Loop Injection`
2. `Depth Parallel Universe`
3. `Depth Portal Composite`
4. `Depth Neural Quantum Hyper Tunnel`
5. `Depth Reality Distortion`

## Phase Gate Checklist
For every single module you port, you MUST achieve the following before returning execution:

- [ ] **No-Stub Policy**: Absolutely no dead code logic paths.
- [ ] **Interface**: Inherit correctly from `vjlive3.plugins.api.PluginBase`.
- [ ] **Test Coverage**: You must write Pytest hardware mocks and achieve >= 80% coverage per module.
- [ ] **Performance Limit**: Real-time 60fps capability. Do not bloat the system. Run `scripts/check_performance_regression.py`.
- [ ] **Security**: Run `scripts/check_souls.py` and `scripts/check_stubs.py` and ensure zero violations.

---

**Execution is yours. Begin porting Depth Loop Injection.**