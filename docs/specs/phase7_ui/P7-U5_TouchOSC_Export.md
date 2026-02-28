# Spec: P7-U5 — TouchOSC Export / Mobile Interface

**File naming:** `docs/specs/phase7_ui/P7-U5_TouchOSC_Export.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P7-U5 — TouchOSC Export

**Phase:** Phase 7 / P7-U5
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

TouchOSC Export generates TouchOSC-compatible control surfaces for mobile devices. It automatically creates OSC layouts from plugin parameters, allowing users to control VJLive3 from iOS/Android devices using the TouchOSC app or any OSC-compatible controller.

---

## What It Does NOT Do

- Does not provide custom UI design (auto-generated only)
- Does not handle OSC server (delegates to OSC library)
- Does not include authentication (basic OSC only)
- Does not support other OSC controllers (TouchOSC format only)

---

## Public Interface

```python
class TouchOSCExport:
    def __init__(self, plugin_runtime: PluginRuntime) -> None: ...
    
    def generate_layout(self, plugin_id: str, template: str = "default") -> OSCLayout: ...
    def export_layout(self, layout: OSCLayout, filepath: str) -> bool: ...
    
    def import_layout(self, filepath: str) -> OSCLayout: ...
    def validate_layout(self, layout: OSCLayout) -> ValidationResult: ...
    
    def list_available_templates(self) -> List[str]: ...
    def get_template(self, name: str) -> Optional[OSCTemplate]: ...
    
    def send_to_device(self, layout: OSCLayout, device_ip: str) -> bool: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `plugin_runtime` | `PluginRuntime` | Plugin execution environment | Must be initialized |
| `plugin_id` | `str` | Plugin identifier | Valid plugin |
| `template` | `str` | Layout template name | Known template |
| `layout` | `OSCLayout` | OSC layout definition | Valid layout |
| `filepath` | `str` | Output file path | Valid path |
| `device_ip` | `str` | Device IP address | Valid IP |

**Output:** `OSCLayout`, `bool`, `ValidationResult` — Layout generation and export results

---

## Edge Cases and Error Handling

- What happens if plugin has no parameters? → Generate empty layout
- What happens if template missing? → Use default template
- What happens if device unreachable? → Log error, continue
- What happens if layout invalid? → Return validation errors
- What happens on cleanup? → Close any open connections

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `python-osc` — for OSC protocol — fallback: raise ImportError
  - `liblo` — for low-level OSC — fallback: use python-osc only
- Internal modules this depends on:
  - `vjlive3.plugins.plugin_runtime`
  - `vjlive3.plugins.api`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_layout_generation` | Generates valid OSC layouts |
| `test_layout_export` | Exports layouts to files |
| `test_layout_import` | Imports layouts from files |
| `test_template_selection` | Uses correct templates |
| `test_device_send` | Sends layouts to devices |
| `test_validation` | Validates layouts correctly |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-7] P7-U5: TouchOSC export / mobile interface` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Checkpoint

- [ ] Spec reviewed and approved
- [ ] Implementation ready to begin
- [ ] All dependencies verified
- [ ] Test plan complete
- [ ] Definition of Done clear

---

*Specification based on VJlive-2 TouchOSC export module.*