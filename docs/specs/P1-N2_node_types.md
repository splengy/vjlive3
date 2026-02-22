# Spec: P1-N2 — Node Types (Full Collection)

**File naming:** `docs/specs/P1-N2_node_types.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-N2 — Node Types

**Phase:** Phase 1 / P1-N2
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

The node types system defines the complete catalog of node types available in VJLive3, including effect nodes, generator nodes, modifier nodes, and utility nodes. It provides detailed type information, parameter schemas, and port definitions for each node type, enabling the node graph UI to present a comprehensive palette of building blocks for visual programming.

---

## What It Does NOT Do

- Does not discover plugins (delegates to P1-N1)
- Does not instantiate nodes (delegates to plugin loader)
- Does not manage node graph connections (delegates to P1-N4)
- Does not handle node execution (delegates to render engine)

---

## Public Interface

```python
class NodeTypeRegistry:
    def __init__(self) -> None: ...
    
    def register_node_type(self, node_type: NodeType) -> None: ...
    def unregister_node_type(self, node_type: str) -> None: ...
    
    def get_node_type(self, node_type: str) -> Optional[NodeType]: ...
    def list_node_types(self) -> List[str]: ...
    def get_node_types_by_category(self, category: str) -> List[NodeType]: ...
    
    def get_parameter_schema(self, node_type: str) -> List[ParameterSchema]: ...
    def get_input_ports(self, node_type: str) -> List[PortInfo]: ...
    def get_output_ports(self, node_type: str) -> List[PortInfo]: ...
    
    def is_compatible(self, source_node: str, source_port: str, target_node: str, target_port: str) -> bool: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `node_type` | `str` | Unique node type identifier | Non-empty |
| `category` | `str` | Node category (effect, generator, etc.) | Known category |
| `source_node` | `str` | Source node type | Valid node type |
| `source_port` | `str` | Source port name | Valid port |
| `target_node` | `str` | Target node type | Valid node type |
| `target_port` | `str` | Target port name | Valid port |

**Output:** Various node type metadata, schemas, and compatibility info

---

## Edge Cases and Error Handling

- What happens if node type not registered? → Return None
- What happens if parameter schema missing? → Return empty list
- What happens if ports not defined? → Return empty lists
- What happens if compatibility check fails? → Return False with reason
- What happens on cleanup? → Clear all registered types

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - None required for basic functionality
- Internal modules this depends on:
  - `vjlive3.plugins.registry`
  - `vjlive3.plugins.api`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_register_node_type` | Registers node types correctly |
| `test_list_node_types` | Lists all registered types |
| `test_get_node_type` | Retrieves node type metadata |
| `test_parameter_schema` | Returns correct parameter schemas |
| `test_port_info` | Returns correct input/output ports |
| `test_compatibility` | Checks node compatibility correctly |
| `test_edge_cases` | Handles missing types gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-N2: Node types` message
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

*Specification based on VJlive-2 node type system.*