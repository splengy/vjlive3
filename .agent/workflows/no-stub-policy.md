---
description: no-stub policy - how to handle dead-end code paths in VJLive3
---

# No-Stub Policy

VJLive3 has a **zero-stub policy**. This workflow defines the correct pattern for every type of dead-end code path.

## The Rule

Any function or method that reaches a known termination point MUST NOT use:
- `pass`
- `raise NotImplementedError`
- `return False` / `return True` without real logic
- `...` (ellipsis placeholder)
- `# TODO` with no implementation

These patterns cause silent false-positive test results and are indistinguishable from working code.

## The Correct Pattern

```python
class MyClass:
    def __init__(self, name: str) -> None:
        self.name = name
        self._log = logging.getLogger(f"vjlive3.{name}")

    def hardware_not_yet_supported(self) -> None:
        """This hardware path is a known Phase 2 feature — not yet implemented."""
        self._log.info(
            f"[TERMINATION] {self.__class__.__name__}.hardware_not_yet_supported: "
            "NDI hardware path deferred to Phase 2-H5. "
            "Use software simulation fallback instead."
        )

    def branch_that_cannot_occur(self) -> None:
        """This branch exists to satisfy the type system but cannot be reached."""
        self._log.warning(
            f"[TERMINATION] {self.__class__.__name__}.branch_that_cannot_occur: "
            "Reached via invalid state — audio buffer was None after null check. "
            "This indicates upstream contract violation."
        )
```

## Decision Tree

When you reach a dead-end code path, ask:

1. **Is this a known future feature?**
   → Log with `[TERMINATION]` and the phase/task it belongs to. Return early with logged message.

2. **Is this a hardware/platform path not yet supported?**
   → Log with `[TERMINATION]` + fallback path. Use simulation mode if available.

3. **Is this a branch that satisfies the type system but cannot logically occur?**
   → Log with `[TERMINATION]` as a contract violation warning. Never silently pass.

4. **Is this a plugin/effect in early migration state?**
   → DO NOT create a stub plugin. Either port the full logic or do not create the file yet.

## Pre-commit Enforcement

The hook `check_stubs.py` scans all Python files for:
- Functions/methods whose only content is `pass`
- `raise NotImplementedError` usage
- Empty `except: pass` blocks

A commit with any of these will be rejected with a file:line report.

## Exception: Test Files

Test files in `tests/` may use `pass` in empty test stubs that have a `pytest.mark.skip` decorator. The scanner allows this specific pattern.

```python
@pytest.mark.skip(reason="Phase 2-H1 hardware not yet available in CI")
def test_midi_controller_connection() -> None:
    pass  # Allowed: marked skip, not a hidden stub
```
