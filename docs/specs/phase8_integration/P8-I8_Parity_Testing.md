# Spec: P8-I8 — Parity Testing: Legacy VJLive vs VJLive3

**File naming:** `docs/specs/phase8_integration/P8-I8_Parity_Testing.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P8-I8 — Parity Testing

**Phase:** Phase 8 / P8-I8
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

P8-I8 conducts comprehensive parity testing between the legacy VJLive applications (VJLive, VJlive-2) and the current VJLive3 codebase. It systematically verifies that all features, plugins, APIs, and behaviors from the legacy applications are present and functional in VJLive3, ensuring no regressions or missing functionality during the migration.

---

## What It Does NOT Do

- Does not guarantee 100% behavioral identity (some improvements are expected)
- Does not test performance equivalence (only functional presence)
- Does not validate UI/UX similarity (only backend functionality)
- Does not cover deprecated features (only active features)

---

## Public Interface

```python
class ParityTester:
    def __init__(self, legacy_paths: List[str], current_path: str) -> None: ...
    
    def discover_legacy_features(self) -> FeatureManifest: ...
    def discover_current_features(self) -> FeatureManifest: ...
    
    def compare_manifests(self, legacy: FeatureManifest, current: FeatureManifest) -> ParityReport: ...
    def generate_test_matrix(self, report: ParityReport) -> TestMatrix: ...
    
    def run_automated_tests(self, matrix: TestMatrix) -> TestResults: ...
    def run_manual_verification(self, matrix: TestMatrix) -> ManualVerificationReport: ...
    
    def export_report(self, format: str = "markdown") -> str: ...
    def get_missing_features(self) -> List[FeatureGap]: ...
    def get_regression_features(self) -> List[FeatureRegression]: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `legacy_paths` | `List[str]` | Paths to legacy VJLive codebases | Valid directories |
| `current_path` | `str` | Path to VJLive3 codebase | Valid directory |
| `format` | `str` | Report output format | 'markdown', 'json', 'html' |
| `matrix` | `TestMatrix` | Generated test cases | Valid matrix |
| `report` | `ParityReport` | Comparison results | Valid report |

**Output:** `str` — Exported parity report; `List[FeatureGap]` — Missing features; `List[FeatureRegression]` — Regressions

---

## Edge Cases and Error Handling

- What happens if legacy path missing? → Raise FileNotFoundError with clear message
- What happens if current path incomplete? → Flag all features as missing
- What happens if feature comparison fails? → Log error, continue with other features
- What happens on cleanup? → Clear temporary files, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `ast` — for Python code analysis — fallback: raise ImportError
  - `json` — for manifest serialization — fallback: raise ImportError
  - `pytest` — for automated test execution — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.plugins.registry` (for plugin discovery)
  - `vjlive3.plugins.loader` (for plugin loading)
  - `vjlive3.audio.audio_analyzer` (for audio analysis)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_legacy_discovery` | Discovers legacy features correctly |
| `test_current_discovery` | Discovers current features correctly |
| `test_feature_comparison` | Compares manifests accurately |
| `test_gap_detection` | Identifies missing features |
| `test_regression_detection` | Identifies regressions |
| `test_report_generation` | Generates reports in all formats |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-8] P8-I8: Parity testing legacy vs VJLive3` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] Parity report generated and reviewed
- [ ] All missing features documented
- [ ] All regressions documented

---

## Verification Checkpoint

- [ ] Spec reviewed and approved
- [ ] Implementation ready to begin
- [ ] All dependencies verified
- [ ] Test plan complete
- [ ] Definition of Done clear

---

## Critical Success Criteria

1. **Feature Coverage:** ≥99% of legacy features present in VJLive3
2. **Plugin Parity:** All legacy plugins have VJLive3 equivalents
3. **API Compatibility:** Core APIs match or have documented migration paths
4. **No Silent Regressions:** All behavioral differences explicitly documented
5. **Test Validation:** Automated tests verify functional equivalence where possible

---

## Implementation Notes

### Feature Discovery Strategy

1. **Legacy Analysis:**
   - Parse `plugins/` directories in VJLive and VJlive-2
   - Extract plugin manifests (manifest.json, plugin.yaml)
   - Analyze Python modules for class definitions and methods
   - Document public APIs, parameters, and behaviors

2. **Current Analysis:**
   - Parse `src/vjlive3/plugins/` directory
   - Extract plugin registry entries
   - Analyze `PluginBase` implementations
   - Document current capabilities

3. **Comparison Algorithm:**
   - Match plugins by name and purpose
   - Compare method signatures
   - Compare parameter ranges and defaults
   - Identify missing methods or parameters
   - Flag behavioral differences

### Test Matrix Generation

- Create automated test cases for each feature pair
- Generate smoke tests for plugin loading and initialization
- Create integration tests for audio/video processing chains
- Document manual verification steps for UI/UX features

### Report Formats

- **Markdown:** Human-readable summary with tables
- **JSON:** Machine-parseable for CI/CD integration
- **HTML:** Interactive report with filtering and search

---

## References

- Legacy codebases: `VJLive/`, `vjlive/` (read-only)
- Current codebase: `src/vjlive3/`
- Feature matrix: `VJlive-2/FEATURE_MATRIX.md`
- Plugin registry: `src/vjlive3/plugins/registry.py`

---

*Specification for comprehensive parity testing between legacy and current VJLive versions.*