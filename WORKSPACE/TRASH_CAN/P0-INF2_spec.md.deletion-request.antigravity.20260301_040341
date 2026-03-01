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

- What happens if hardware is missing? → [NEEDS RESEARCH]  
  *Note: This audit is metadata-based and does not depend on hardware. No fallback required.*  
- What happens on bad input? → Raises `FileNotFoundError` or `NotADirectoryError` with clear message indicating invalid path.  
- What is the cleanup path? → No external resources are allocated; no cleanup needed. Object state is preserved after scan completion.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `pathlib`, `os`, `glob` — used for file scanning and directory traversal — fallback: built-in Python standard library  
  - `json` — used to export audit results — fallback: native JSON support  
- Internal modules this depends on:  
  - `vjlive3.core.effect_registry.EffectRegistry` — for metadata schema validation (if available)  
  - `vjlive3.utils.file_utils` — for path resolution and file scanning  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_scan_missing_plugins_empty_dir` | Audit returns empty list when legacy directory is empty or missing |
| `test_scan_missing_plugins_valid_path` | Correctly identifies 218 plugins from known legacy path |
| `test_generate_report_structure` | Output JSON has correct schema: `{ "plugin_id": { "name", "path", "parameters", "behavior", "status" } }` |
| `test_export_to_json_success` | Report is written to file without errors |
| `test_filter_plugins_by_type` | Filtered results only include specified plugin types |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-2] P0-INF2: Audit 218 missing legacy plugins` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

--- 

## LEGACY CODE REFERENCES

See detailed implementation in:

- `vjlive1/core/effects/legacy_trash/background_subtraction.py` (L1–84)  
  - Describes structure of legacy plugin: initialization, parameters (`threshold`, `blur`, `opacity`, `effectMode`), OpenCV background subtraction logic using MOG2.  
  - Defines three modes: silhouette, ghosting, foreground isolation — used as reference for behavior mapping in audit.  
  - Shows parameter schema and effect flow that must be mirrored in new VJLive3 modules.  

This legacy file serves as a canonical example of the plugin format, parameter structure, and rendering logic to be preserved during migration. The audit will extract all such patterns across the entire `legacy_trash` directory and beyond.