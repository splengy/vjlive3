# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P0-INF2_infrastructure_audit.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-INF2 — Infrastructure Audit

**Phase:** Phase 2 / P2-H3  
**Assigned To:** Alex Turner  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-05

---

## What This Module Does

This module performs a comprehensive audit of missing plugins in the VJLive legacy codebase, specifically identifying and cataloging 218 features or effects that are currently absent from the VJLive3 platform. It establishes feature parity by mapping each missing plugin to its original implementation location, parameters, behavior, and intended use case in the legacy system (e.g., `vjlive1/core/effects/legacy_trash/background_subtraction.py`). The output is a structured inventory used to guide development of new effect modules in VJLive3 with full backward compatibility.

---

## What It Does NOT Do

- It does not implement or generate actual plugin code.  
- It does not modify existing VJLive3 core functionality.  
- It does not perform real-time rendering or effect processing.  
- It does not validate hardware support or performance characteristics.  
- It does not replace legacy plugins with new ones — only documents their absence and specifications.

---

## Public Interface

```python
class InfrastructureAudit:
    def __init__(self, legacy_path: str) -> None: ...
    def scan_for_missing_plugins(self) -> dict[str, dict] : ...
    def generate_feature_parity_report(self) -> dict[str, dict] : ...
    def export_to_json(self, output_path: str) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `legacy_path` | `str` | Path to legacy VJLive1 effects directory (e.g., `vjlive1/core/effects/legacy_trash`) | Must exist, readable; default: `"vjlive1/core/effects/legacy_trash"` |
| `output_path` | `str` | File path for exported JSON report | Must be writable; if omitted, output to `./audit_report.json` |
| `plugin_filter` | `list[str]` | List of plugin types (e.g., ["background_subtraction", "color_warp"]) | Optional; defaults to all plugins |

---

## Edge Cases and Error Handling

