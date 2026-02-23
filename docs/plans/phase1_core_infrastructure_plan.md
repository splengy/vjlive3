# Phase 1 Core Infrastructure Expansion Plan

**Version:** 1.0 | **Date:** 2026-02-22 | **Manager:** ROO CODE (Manager-Gemini-3.1)

---

## Executive Summary

Based on the CORE_LOGIC_PARITY audit, we need to integrate **22 critical core logic systems** into Phase 1-2 to unblock subsequent plugin implementation. These are foundational systems that many plugins depend on.

---

## Phase 1 Additions (8 tasks)

### State & Persistence (P1-C1 through P1-C4)

| Task ID | Description | Priority | Spec Status |
|---------|-------------|----------|-------------|
| P1-C1 | ApplicationStateManager — centralized state broadcasting | P0 | ✅ Created |
| P1-C2 | StatePersistenceManager — comprehensive save/load | P0 | ✅ Created |
| P1-C3 | ProjectManager — project lifecycle management | P0 | ⏳ Needed |
| P1-C4 | ConfigManager — type-safe configuration | P0 | ⏳ Needed |

**Rationale:** These four systems form the state backbone. Without them, projects cannot be saved/loaded, configuration is ad-hoc, and state changes are not broadcast to components.

---

### AI/Agent Systems (P1-AI1 through P1-AI8)

| Task ID | Description | Priority | Spec Status |
|---------|-------------|----------|-------------|
| P1-AI1 | AIIntegration — AI subsystem management layer | P0 | ⏳ Needed |
| P1-AI2 | AgentManager — agent lifecycle management | P0 | ⏳ Needed |
| P1-AI3 | AgentOrchestrator — LangGraph orchestration | P0 | ⏳ Needed |
| P1-AI4 | AgentPersona — hot-swappable personalities with memory | P0 | ⏳ Needed |
| P1-AI5 | CreativeHive — AI-driven visual suggestions | P0 | ⏳ Needed |
| P1-AI6 | LLMService — LLM integration for analysis | P0 | ⏳ Needed |
| P1-AI7 | AISuggestionEngine — AI timeline optimization | P0 | ⏳ Needed |
| P1-AI8 | NeuralEngine — unified neural engine | P0 | ⏳ Needed |

**Rationale:** AI/Agent systems are core to VJLive's advanced features. They need to be available early for integration testing and to unblock Phase 6 Quantum/AI work.

---

## Phase 2 Additions (11 tasks)

### Hardware Systems (P2-H8 through P2-H13)

| Task ID | Description | Priority | Spec Status |
|---------|-------------|----------|-------------|
| P2-H8 | HardwareManager — central hardware coordinator | P0 | ⏳ Needed |
| P2-H9 | HardwareScanner — startup hardware audit | P0 | ⏳ Needed |
| P2-H10 | MultiCameraManager — multi-camera fusion | P0 | ⏳ Needed |
| P2-H11 | VisionWatchdog — hot-plug detection | P0 | ⏳ Needed |
| P2-H12 | DMXEngine — central DMX orchestrator | P0 | ✅ Already complete (Phase 2A) |
| P2-H13 | DMXInputController — Art-Net/sACN input | P0 | ✅ Already complete (Phase 2A) |

**Rationale:** Hardware abstraction is critical for the DMX and camera systems already in use. These need to be properly architected now.

---

### Web/API Systems (P2-W1 through P2-W4)

| Task ID | Description | Priority | Spec Status |
|---------|-------------|----------|-------------|
| P2-W1 | VJWebServer — FastAPI REST + WebSocket server | P0 | ⏳ Needed |
| P2-W2 | NodeGraphBridge — web UI ↔ backend signal flow | P0 | ⏳ Needed |
| P2-W3 | SceneBridge — web UI layer nodes ↔ backend Stage | P0 | ⏳ Needed |
| P2-W4 | WebSocketGateway — centralized WebSocket broadcasting | P0 | ⏳ Needed |

**Rationale:** Web UI integration is needed for remote control and collaborative features. These are blocking Phase 7 UI work.

---

## Implementation Strategy

### Immediate Next Steps (Priority Order)

1. **Create remaining Phase 1 specs** (P1-C3, P1-C4, P1-AI1 through P1-AI8)
   - These are blocking all state-related work
   - ProjectManager and ConfigManager are especially critical

2. **Create Phase 2 specs** (P2-H8, P2-H9, P2-H10, P2-H11, P2-W1-P2-W4)
   - Hardware and Web systems are blocking plugin integration

3. **Assign to Implementation Engineers via inbox**
   - Use `WORKSPACE/INBOXES/inbox_alpha.md` for task assignment
   - Each spec gets its own assignment with clear dependencies

4. **Begin implementation in parallel**
   - Multiple agents can work on different core systems simultaneously
   - Dependencies clearly marked in each spec

---

## Spec Creation Checklist

For each of the 19 remaining core system specs, ensure:

- [ ] Problem statement clearly defines the need
- [ ] Proposed solution matches VJLive3 architecture
- [ ] API/interface is complete with type hints
- [ ] Implementation plan is broken into days
- [ ] Test strategy includes unit + integration tests
- [ ] Performance requirements are specified
- [ ] Safety rail compliance is documented
- [ ] Dependencies are clearly listed
- [ ] Open questions are identified
- [ ] References to legacy code are provided

---

## Assignment Template

When assigning to inbox_alpha, include:

```
# Task Assignment

**Task ID:** P1-C3
**Task Name:** ProjectManager — project lifecycle management
**Priority:** P0
**Spec:** docs/specs/P1-C3_project_manager.md
**Dependencies:** P1-C1, P1-C2
**Blocking:** All project save/load operations
**Verification:** ≥80% test coverage, FPS ≥ 58, 0 safety rail violations
**Easter Egg Council:** Required before completion
```

---

## Timeline Estimate

| Phase | Tasks | Estimated Duration |
|-------|-------|-------------------|
| Phase 1 Core Expansion | 12 tasks | 2-3 weeks |
| Phase 2 Core Expansion | 11 tasks | 2-3 weeks |
| **Total Core Infrastructure** | **23 tasks** | **4-6 weeks** |

This is in addition to the already-completed Phase 0 and ongoing Phase 1-2 work.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Spec creation bottleneck | Manager creates all specs before delegation |
| Dependency conflicts | Clear dependency tracking in BOARD.md |
| Integration issues | Regular sync via AGENT_SYNC.md |
| Performance impact | Continuous profiling, FPS gates |
| Scope creep | Strict spec-first discipline, no deviations |

---

## Success Criteria

1. All 23 core system specs created and approved
2. All specs assigned to inbox with clear instructions
3. Implementation begins with ≥2 agents in parallel
4. No blocking dependencies unresolved
5. Quality gates (FPS, coverage, safety rails) enforced

---

**"The best code is code that knows what it is and does it well."**
*— WORKSPACE/PRIME_DIRECTIVE.md*