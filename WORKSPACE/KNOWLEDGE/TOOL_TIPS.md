# TOOL_TIPS.md — Shared Agent Knowledge Base

**Purpose:** Tips, tricks, and patterns discovered during development. Add yours!
**Format:** `[AgentName] tip description` then code or detail.

> [!TIP]
> Use MCP `vjlive-brain` → `search_concepts(tags=["your_tag"])` before writing any new code. The concept may already be indexed and partially ported.

---

## Environment Setup

### Finding the Active Workspace
The active workspace is always:
```
/home/happy/Desktop/claude projects/VJLive3_The_Reckoning
```
Legacy references:
```
/home/happy/Desktop/claude projects/VJlive-2    # v2 reference
/home/happy/Desktop/claude projects/vjlive       # v1 reference
```

### MCP Server Startup
```bash
# Knowledge base
python mcp_servers/vjlive_brain/server.py &

# Agent switchboard
python mcp_servers/vjlive_switchboard/server.py &
```

---

## File Lock Workflow
```bash
# Before editing a file:
# 1. Check WORKSPACE/COMMS/LOCKS.md - is it locked?
# 2. Add your lock entry
# 3. Edit, commit
# 4. Remove lock entry

# Via MCP:
checkout_file("/path/to/file.py", "MyAgent", eta_mins=30)
# ... edit ...
checkin_file("/path/to/file.py", "MyAgent")
```

---

## No-Stub Pattern

```python
# ❌ NEVER DO THIS:
def my_method(self) -> bool:
    pass  # TODO

# ❌ NEVER DO THIS:
def my_method(self) -> bool:
    raise NotImplementedError

# ✅ CORRECT — Known dead-end:
def my_method(self) -> None:
    self.logger.termination(
        "MyClass.my_method: This path terminates because "
        "<specific reason why this is a known endpoint>"
    )
```

---

## Logger.termination Pattern

```python
import logging

class Logger:
    """Structured logger with termination event support."""
    
    def __init__(self, name: str) -> None:
        self._log = logging.getLogger(name)
    
    def termination(self, description: str) -> None:
        """Log a known termination point — NOT a stub."""
        self._log.info(f"[TERMINATION] {description}")
```

---

## Plugin METADATA Pattern

Every plugin class must self-document:
```python
class MyEffect:
    METADATA: dict = {
        "name": "My Effect",
        "description": "2-3 evocative sentences describing what this does and why.",
        "version": "1.0.0",
        "api_version": "3.0",
        "origin": "vjlive-v2:effects/my_effect.py",
        "dreamer_flag": False,
        "logic_purity": "clean",  # clean | buggy | genius | unknown
        "role_assignment": "worker",  # manager | worker
        "kitten_status": True,  # contributes to windowed phase?
        "parameters": {
            "intensity": {
                "type": "float",
                "min": 0.0, "max": 1.0, "default": 0.5,
                "description": "Effect intensity — 0=subtle, 1=full"
            }
        },
        "tags": ["glitch", "audio_reactive"],
        "category": "core",
        "performance_impact": "low",
    }
```

---

## Pre-Commit Quick Reference

```bash
# Install hooks (once per clone)
pip install pre-commit
pre-commit install

# Run all checks manually
make quality

# Run just stub check
python scripts/check_stubs.py src/

# Run just size check
python scripts/check_file_size.py src/

# Full phase gate (quality + FPS)
make phase-gate
```

---

## Legacy Codebase Patterns

### Finding an effect in v2:
```bash
find "/home/happy/Desktop/claude projects/VJlive-2/core" -name "*.py" | xargs grep -l "class.*Effect"
```

### Finding "Dreamer" code indicators:
```bash
grep -r "quantum\|consciousness\|neural\|galactic\|cosmic\|infinite" \
  "/home/happy/Desktop/claude projects/VJlive-2/core" --include="*.py" -l
```

---

## Git Workflow

```bash
# Start of session: pull and check status
git pull
git status

# End of each task: commit with phase tag
git add -p  # interactive staging — review every hunk
git commit -m "[Phase-0] feat: description of what was done"

# Branch naming
git checkout -b phase-0/environment-setup
git checkout -b phase-1/audio-foundation
git checkout -b plugin/vimana-snowflake
```
