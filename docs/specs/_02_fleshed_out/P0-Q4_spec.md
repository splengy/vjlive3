# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P0-Q4_pre_commit_config.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-Q4 — pre-commit-config.yaml

**Phase:** Phase 0 / P0  
**Assigned To:** [Agent name]  
**Spec Written By:** [Agent name]  
**Date:** 2025-04-05  

---

## What This Module Does

The `pre-commit-config.yaml` file defines the pre-commit hooks and linting rules that enforce code quality standards across the repository. It ensures consistency in formatting, style, type checking, and code safety before any changes are committed to version control.

This configuration enforces:
- Code formatting via Black and Isort
- Static type checking using mypy with type hints
- Style enforcement via flake8 and bugbear rules
- Prevention of large added files and trailing whitespace

It serves as a foundational quality gate for all contributions, reducing technical debt and improving maintainability.

---

## What It Does NOT Do

- It does not perform runtime code execution or application logic.
- It does not manage CI/CD pipelines or deployment workflows.
- It does not validate business logic or feature behavior — only code structure and style.
- It does not enforce documentation standards (e.g., docstrings) beyond flake8 rules.

---

## Public Interface

```python
# pre-commit-config.yaml is a configuration file, not a class or function
# The interface is defined through YAML schema and hook definitions
# No direct Python API; only consumed by pre-commit tooling
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `repos` | list of dict | Defines external repositories with hooks to run before commits | Must contain valid GitHub URLs, correct hook IDs, and supported revisions |
| `hooks` | list of dict | Individual pre-commit checks (e.g., formatting, linting) | Each must have a unique `id`, valid `repo`, and optional `args` or dependencies |
| `additional_dependencies` | list of strings | External packages required for hooks (e.g. types-requests) | Must be valid PyPI package names; used only when specified in hook config |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Not applicable — this file has no hardware dependencies.
- What happens on bad input? → Invalid YAML syntax or malformed hook definitions will cause pre-commit to fail during setup. The tooling will report specific errors (e.g., "unknown hook", "invalid repo URL").
- What is the cleanup path? → No runtime resources are allocated; configuration is static and loaded at commit time. No explicit cleanup required.

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `pre-commit-hooks` — used for trailing whitespace, YAML validation, file size checks — fallback: no linting, but commits proceed
  - `black` — enforces Python formatting — fallback: unformatted code is committed
  - `isort` — sorts imports — fallback: import order is unsorted
  - `flake8` and `flake8-bugbear` — style and bug detection — fallback: style issues are ignored
  - `mypy` — type checking — fallback: type errors are not caught, leading to potential runtime bugs

- Internal modules this depends on:
  - None (this is a configuration file)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_valid_config_structure` | YAML parses without syntax error and contains all required sections |
| `test_hook_id_uniqueness` | Each hook has a unique ID across repos to avoid conflicts |
| `test_dependency_resolution` | All additional_dependencies are valid PyPI packages and installable |
| `test_large_file_check` | The `check-added-large-files` hook correctly flags files over 5000 KB |
| `test_trailing_whitespace` | Trailing whitespace is caught and reported before commit |
| `test_mypy_type_checking` | mypy detects missing types or invalid type annotations in Python files |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-Q4: Add pre-commit-config.yaml` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 0, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### vjlive2/.pre-commit-config.yaml (L1-20)
```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
        args: ['--maxkb=5000']
    -   id: debug-statements

-   repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
    -   id: black

-   repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
    -   id: isort
```

### vjlive2/.pre-commit-config.yaml (L17-33)
```yaml
-   repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
    -   id: isort

-   repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-bugbear]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
    -   id: mypy
        additional_dependencies: [types-requests, types-PyYAML]
        args: [--ignore-missing-imports]
```

### vjlive2/.pre-commit-config.yaml (L30-33)
```yaml
    hooks:
    -   id: mypy
        additional_dependencies: [types-requests, types-PyYAML]
        args: [--ignore-missing-imports]
```

### vjlive2/.pre-commit-config.yaml (L31-33)
```yaml
    -   id: mypy
        additional_dependencies: [types-requests, types-PyYAML]
        args: [--ignore-missing-imports]
```

### vjlive2/.pre-commit-config.yaml (L33-33)
```yaml
        additional_dependencies: [types-requests, types-PyYAML]
        args: [--ignore-missing-imports]
```