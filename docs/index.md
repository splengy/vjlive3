# VJLive3 — Documentation Index

> **Version**: 3.0 Alpha | **Tests**: 1,241 green

---

## Guides

| Document | Description |
|----------|-------------|
| [Plugin API](plugin_api.md) | How to write and use effect plugins |
| [Agent System](agents.md) | 16D manifold, physics, memory, bridge |
| [UI System](ui.md) | CLI, web remote, collaborative studio |

---

## Quick Reference

### Plugin directories

| Path | Contents |
|------|----------|
| `src/vjlive3/plugins/` | 249 effect plugin modules |
| `tests/plugins/` | 1,091 plugin unit tests |

### Agent directories

| Path | Contents |
|------|----------|
| `src/vjlive3/agents/` | 5 agent modules (agent, manifold, physics, memory, bridge) |
| `tests/agents/` | 130 agent tests |

### UI directories

| Path | Contents |
|------|----------|
| `src/vjlive3/ui/` | cli.py, web_remote.py, desktop_gui.py |
| `tests/ui/` | 63 UI tests |

### Integration

| Path | Contents |
|------|----------|
| `tests/integration/` | 25 E2E integration tests |

---

## Phase Completion

| Phase | Status |
|-------|--------|
| P0 Environment | ✅ |
| P1 Plugin System | ✅ |
| P2 Hardware | ✅ |
| P3 Core Pipeline | ✅ |
| P4–P7 Plugin Ports (249) | ✅ |
| P6-AG Agent System | ✅ |
| P7-U UI System | ✅ |
| P8-I1 Integration Tests | ✅ |
| P8-I2 Performance | ✅ |
| P8-I4 Coverage | ✅ |
| P8-I5 Documentation | ✅ |

---

## Key Numbers

- **249** plugins ported
- **1,241** tests total, all green
- **94%** test coverage across agents + UI modules
- **AgentBridge.step() p50 = 0.47ms** (vs 16.67ms budget)
