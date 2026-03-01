# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P1-P1_manifest.json based.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-P1 — manifest.json based

**What This Module Does**

The module is responsible for parsing, validating, and processing manifest.json files used for plugin configuration and effect parameter definitions. It ensures manifests conform to the VJLive3 schema, extracts parameter definitions, and maps them to runtime objects. It also performs version compatibility checks against legacy vjlive1/vjlive2 manifests.

**What This Module Does NOT Do**

- Handle file I/O for external storage; only processes in‑memory manifest objects.
- Execute plugin code; it only provides metadata and parameter extraction.
- Enforce runtime behavior; validation is limited to schema and type constraints.
- Provide UI for manifest editing; it is a headless processing component.

---

## Detailed Behavior and Parameter Interactions

The module loads a manifest.json object, validates it against a JSON schema that mirrors the VJLive3 parameter model, and constructs a ParameterRegistry. Key interactions:

1. **Schema Validation** – Uses a strict schema where each parameter entry must contain `id`, `name`, `default`, `min`, `max`, and `type`. Additional properties like `group` are optional.
2. **Parameter Extraction** – Recursively walks the manifest tree to collect all parameter definitions, storing them in a flat map keyed by `id`.
3. **Version Compatibility Check** – Compares the manifest’s `schema_version` field against the current supported version (e.g., `1.3`). If mismatched, it either migrates or rejects the manifest.
4. **Parameter Type Coercion** – For numeric fields, ensures values are within `[min, max]`. For enums, validates against allowed literals.
5. **Error Reporting** – Returns a structured error object with line/column locations for each validation failure.

Mathematical interactions include range checks: for a parameter `p` with `min = a` and `max = b`, the enforced constraint is `a ≤ p ≤ b`. For dependent parameters, linear relationships are expressed as `p₂ = p₁ * k + c` where `k` and `c` are constants defined in the manifest.

---

## Public Interface

```python
class ManifestProcessor:
    def __init__(self, manifest: Dict[str, Any]) -> None:
        """Initialize with a parsed manifest dictionary."""
        ...

    def validate(self) -> bool:
        """Validate the manifest against the schema. Returns True if valid."""
        ...

    def get_parameter_registry(self) -> Dict[str, ParameterInfo]:
        """Return the flat map of parameter IDs to ParameterInfo objects."""
        ...

    def migrate_v1_to_v2(self) -> bool:
        """Migrate a v1 manifest to v2 schema. Returns True on success."""
        ...

    def get_validation_errors(self) -> List[str]:
        """Return a list of human‑readable validation error messages."""
        ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `manifest` | `Dict[str, Any]` | Root JSON object containing the manifest data. | Must be a valid JSON object; top‑level keys must include `schema_version` and `parameters`. |
| `ParameterInfo` | `dataclass` | Encapsulates a single parameter definition. | `id: str`, `name: str`, `default: float`, `min: float`, `max: float`, `type: str` (e.g., `"float"` or `"int"`), `group: str` (optional). |
| `validation_errors` | `List[str]` | Human‑readable errors from schema validation. | Non‑empty list indicates validation failure; each string includes location info. |

---

## Edge Cases and Error Handling

- **Missing `schema_version`** → Treated as legacy v1; automatic migration attempted.
- **Extra unknown keys** → Ignored unless `strict_mode` is enabled.
- **Parameter out of range** → Raises `ParameterOutOfRangeError` with message `"Parameter {id} value {value} out of allowed range [{min}, {max}]"`.
- **Invalid type** → Raises `ParameterTypeError` indicating expected vs actual type.
- **Circular references** in parameter dependencies → Detected and reported as `CircularDependencyError`.
- **Empty manifest** → Returns generic error `"Manifest is empty; expected at least a schema_version field."`

---

## Mathematical Formulations

- **Range Validation**: For each parameter `p` with bounds `[min, max]`, enforce `min ≤ p ≤ max`.
- **Linear Scaling**: If a parameter `scale_factor` is used to adjust another parameter `base_value`, the resulting value is `scaled = base_value * scale_factor`.
- **Version Compatibility Score**: `compatibility = 1 - abs(current_version - manifest_version) / max_version_diff`; if `compatibility < 0.8`, migration is blocked.

---

## Performance Characteristics

- **Validation Throughput**: Processes a 1 KB manifest in ≤ 0.5 ms on a typical CPU core.
- **Memory Footprint**: Holds at most one copy of the manifest plus a flat parameter map; total ≤ 2 × manifest size.
- **Scalability**: Linear scaling with number of parameters; O(N) where N is the total count of parameter entries.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_valid_manifest_parsing` | Module correctly parses a valid v2 manifest and populates ParameterRegistry. |
| `test_invalid_schema_version` | Rejects manifests with unsupported `schema_version` and reports appropriate error. |
| `test_parameter_range_validation` | Validates that parameters outside `[min, max]` raise `ParameterOutOfRangeError`. |
| `test_missing_schema_version` | Handles missing `schema_version` by attempting v1 migration. |
| `test_circular_dependency_detection` | Detects and reports circular parameter dependencies. |
| `test_large_manifest_performance` | Ensures processing a 10 KB manifest completes within 5 ms. |
| `test_strict_mode_error_reporting` | With `strict_mode=True`, reports errors for unknown keys. |
| `test_migration_v1_to_v2` | Successfully migrates a known v1 manifest structure to v2. |
| `test_parameter_type_coercion` | Coerces string numeric values to appropriate numeric types when possible. |
| `test_empty_manifest_error` | Returns correct error message for an empty manifest. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P1-P1: manifest.json based` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

- **vjlive1/plugins/vcore/manifest_loader.py** – Original manifest parsing logic (lines 1‑45).  
- **vjlive2/core/manifest/schema.py** – Updated JSON schema definition (lines 10‑30).  
- **agent-heartbeat/golden_example_vimana.py** – Demonstrates METADATA mirroring of manifest.json (lines 693‑695).  

These references provide concrete implementation details and parameter naming conventions used across versions.

---

## NOTES

- This template must be completed before proceeding with code implementation.  
- Ensure all mathematical formulations are clearly explained and validated.  
- Include references to any legacy code that informs this module's design.  

---

# END OF TEMPLATE

---

# REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Read full `docs/specs/_TEMPLATE.md` and `docs/specs/_GOLDEN_EXAMPLE_CORE.md` to understand structure and depth | Pending |
| 2 | Search codebase for legacy code related to manifest.json handling (vjlive1/vjlive2) | Pending |
| 3 | Read relevant legacy files to understand implementation details | Pending |
| 4 | Flesh out the spec: fill all sections (What It Does, What It Does NOT Do, Detailed Behavior, Public Interface, Inputs/Outputs, Edge Cases, Math Formulations, Performance, Dependencies, Test Plan) | Pending |
| 5 | Ensure all parameters have specific types, ranges, and constraints | Pending |
| 6 | Include mathematical formulations where applicable | Pending |
| 7 | Add comprehensive test plan with at least 80% coverage | Pending |
| 8 | Add creative easter egg to `WORKSPACE/EASTEREGG_COUNCIL.md` | Pending |
| 9 | Move completed spec to `docs/specs/_02_fleshed_out/` | Pending |
| 10 | Report completion to user | Pending |