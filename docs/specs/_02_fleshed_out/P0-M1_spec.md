# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-M1 — MCP Server (vjlive3brain)

**Phase:** Phase 2 / P2-H3  
**Assigned To:** Agent-7  
**Spec Written By:** Agent-7  
**Date:** 2025-04-05

---

## What This Module Does

This module implements the `vjlive3brain` MCP server, a knowledge base backend that provides access to architectural concepts, decision logs, and system metadata. It serves as the "Hippocampus" for VJLive3 agents, enabling them to retrieve structured information via tools like `get_concept(name)` and `search_concepts(query)`. The module ported from legacy `vjlive2/tools/knowledge_server` to align with VJLive3’s modular architecture and runtime environment.

---

## What It Does NOT Do

- It does not perform real-time data processing or machine learning inference.  
- It does not generate new content or write to external databases.  
- It does not manage agent authentication, session tokens, or access control.  
- It does not replace the `BOARD.md` or `COMMS/DECISIONS.md` files directly — only provides read access via tool interfaces.

---

## Public Interface

```python
class MCPKnowledgeServer:
    def __init__(self, config_path: str = "config/knowledge_server.json") -> None:
        """Initialize server with configuration file."""
        pass

    def get_concept(self, name: str) -> dict | None:
        """
        Retrieve a concept from the knowledge base.
        
        Args:
            name (str): Name of the concept (e.g., "plaits_protocol", "vimana_metadata")
            
        Returns:
            dict or None: Concept data if found; otherwise None
        """
        pass

    def search_concepts(self, query: str) -> list[dict]:
        """
        Search for relevant architectural rules based on a natural language query.
        
        Args:
            query (str): Natural language query (e.g., "how do agents claim tasks?")
            
        Returns:
            List of matching concept dictionaries
        """
        pass

    def log_decision(self, context: dict) -> None:
        """
        Record an architectural decision to COMMS/DECISIONS.md.
        
        Args:
            context (dict): Decision metadata including agent, timestamp, and rationale
        """
        pass
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config_path` | `str` | Path to JSON configuration file containing server settings | Must be absolute path; defaults to `"config/knowledge_server.json"` |
| `name` | `str` | Concept name to retrieve (e.g., "prime_directive") | Must not be empty or None; max length 100 characters |
| `query` | `str` | Natural language search query for concept matching | Max length 256 characters; must contain at least one non-whitespace character |
| `context` | `dict` | Metadata about a decision (agent, timestamp, rationale) | Must include keys: "agent", "timestamp", "rationale"; all required |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Uses the **NullDevice pattern**: returns empty or default values without crashing.  
- What happens on bad input? → Raises `ValueError` with descriptive message (e.g., `"Invalid concept name: must be non-empty"`).  
- What is the cleanup path? → On shutdown, logs a final status entry and closes file handles; no active resources are held beyond normal Python object lifecycle.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `json` — used for reading configuration files — fallback: built-in, no impact  
  - `os.path` — used to validate paths — fallback: standard library  
- Internal modules this depends on:  
  - `vjlive3.utils.file_reader` — for safe file access and parsing of `BOARD.md`, `COMMS/DECISIONS.md`  
  - `vjlive3.concepts.plaits_protocol` — provides the core protocol logic referenced in Prime Directive  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_config_file` | Module starts without crashing if config file is missing or invalid |
| `test_get_concept_valid_name` | Returns correct concept data for known names (e.g., "prime_directive") |
| `test_get_concept_missing_name` | Returns None when concept does not exist |
| `test_search_concepts_empty_query` | Raises ValueError on empty query input |
| `test_search_concepts_finds_matches` | Returns relevant concepts matching a natural language query |
| `test_log_decision_valid_context` | Records decision to COMMS/DECISIONS.md with correct metadata |
| `test_log_decision_missing_required_field` | Raises ValueError when required context fields are missing |
| `test_cleanup_on_shutdown` | Server releases file handles and logs shutdown status cleanly |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-2] P0-M1: Implement vjlive3brain MCP server` message  
- [ ] BOARD.md updated with new module entry and tool reference  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

- vjlive2/MCP_SETUP_GUIDE.md (L1-20): Describes server entry point at `/tools/knowledge_server/src/server.py`, configuration via `claude_desktop_config.json`.  
- vjlive2/MCP_SETUP_GUIDE.md (L17-36): Specifies exact command structure for launching the knowledge server in agent configurations.  
- vjlive2/MCP_SETUP_GUIDE.md (L33-40): Lists available tools: `get_concept(name)`, `search_concepts(query)`, and `log_decision(context)` with file destination (`COMMS/DECISIONS.md`).  
- vjlive2/MCP_SETUP_GUIDE.md (L37-40): Defines agent onboarding flow — call `get_concept("prime_directive")` or read `BOARD.md`, claim task, adhere to **Plaits Protocol**.  
- vjlive2/MCP_SETUP_GUIDE.md (L38-40): Repeats the same onboarding sequence with emphasis on protocol adherence and file access.

