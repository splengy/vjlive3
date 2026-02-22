# Spec: P7-U6 — CLI Automation

**File naming:** `docs/specs/phase7_ui/P7-U6_CLI_Automation.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P7-U6 — CLI Automation

**Phase:** Phase 7 / P7-U6
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

CLI Automation provides a command-line interface for scripting and automating VJLive3 operations. It allows loading projects, triggering actions, adjusting parameters, and running headless performances from shell scripts, enabling integration with external tools and automated workflows.

---

## What It Does NOT Do

- Does not replace the GUI (complementary only)
- Does not provide interactive shell (non-interactive commands only)
- Does not include advanced scripting language (simple commands)
- Does not handle user authentication (assumes local trust)

---

## Public Interface

```python
class CLIAutomation:
    def __init__(self, vjlive3_app: VJLive3App) -> None: ...
    
    def execute_command(self, command: str, args: List[str], kwargs: Dict[str, Any]) -> CommandResult: ...
    def execute_script(self, script_path: str) -> None: ...
    
    def list_commands(self) -> List[CommandDef]: ...
    def get_command_help(self, command: str) -> str: ...
    
    def load_project(self, filepath: str) -> bool: ...
    def save_project(self, filepath: str) -> bool: ...
    
    def trigger_plugin_action(self, plugin_id: str, action: str, params: Dict) -> bool: ...
    def set_plugin_parameter(self, plugin_id: str, param_name: str, value: Any) -> bool: ...
    
    def start_performance(self) -> None: ...
    def stop_performance(self) -> None: ...
    def is_performing(self) -> bool: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `vjlive3_app` | `VJLive3App` | Main application instance | Must be initialized |
| `command` | `str` | Command name | Valid command |
| `args` | `List[str]` | Positional arguments | Valid for command |
| `kwargs` | `Dict[str, Any]` | Keyword arguments | Valid for command |
| `script_path` | `str` | Path to script file | Valid path |
| `filepath` | `str` | Project file path | Valid path |
| `plugin_id` | `str` | Plugin identifier | Valid plugin |
| `action` | `str` | Action name | Valid action |
| `params` | `Dict` | Action parameters | Valid dict |

**Output:** `CommandResult` — Command execution result

---

## Edge Cases and Error Handling

- What happens if command not found? → Return error with suggestions
- What happens if arguments invalid? → Return error with usage
- What happens if project file missing? → Return error, log warning
- What happens if performance already running? → Return error or restart
- What happens on cleanup? → Stop any running operations

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `argparse` — for command parsing — fallback: raise ImportError
  - `json` — for script/config files — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.core.app` (main application)
  - `vjlive3.plugins.plugin_runtime`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_command_execution` | Executes commands correctly |
| `test_script_execution` | Executes script files |
| `test_project_load_save` | Loads and saves projects |
| `test_plugin_control` | Controls plugins via CLI |
| `test_performance_control` | Starts/stops performance |
| `test_error_handling` | Handles invalid commands gracefully |
| `test_edge_cases` | Handles edge cases correctly |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-7] P7-U6: CLI automation` message
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

*Specification based on VJlive-2 CLI automation module.*