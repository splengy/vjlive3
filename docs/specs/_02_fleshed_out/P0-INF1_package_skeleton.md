# Spec: P0-INF1 — VJLive3 Package Skeleton + Test Infrastructure

## What This Does
Creates the `src/vjlive3/` sub-package directories and a shared `tests/conftest.py` with reusable fixtures for headless OpenGL, mock audio streams, and temporary plugin directories. This is a prerequisite for every Phase 1 worker — without it, each worker will invent their own directory structure and import paths, causing immediate merge conflicts.

## What This Does NOT Do
- Does not implement any rendering, audio, or node graph logic
- Does not create any `.py` implementation files beyond `__init__.py` stubs and conftest
- Does not modify BOARD.md, DISPATCH.md, or DECISIONS.md
- Does not exceed 750 lines in any file

## Public Interface

### Package structure created:
```
src/vjlive3/
├── __init__.py          (exists — no change)
├── core/
│   └── __init__.py      (exists — has sigil, no change)
├── rendering/
│   └── __init__.py      [NEW — package declaration + module docstring]
├── audio/
│   └── __init__.py      [NEW — package declaration + module docstring]
├── node_graph/
│   └── __init__.py      [NEW — package declaration + module docstring]
├── hardware/
│   └── __init__.py      [NEW — package declaration + module docstring]
├── api/
│   └── __init__.py      [NEW — package declaration + module docstring]
└── effects/
    └── __init__.py      [NEW — package declaration + module docstring]

tests/
├── conftest.py          [NEW — shared fixtures]
├── unit/
│   ├── test_plugin_system.py    (exists — no change)
│   ├── rendering/
│   │   └── __init__.py  [NEW]
│   ├── audio/
│   │   └── __init__.py  [NEW]
│   └── node_graph/
│       └── __init__.py  [NEW]
└── integration/
    └── __init__.py      [NEW]
```

### conftest.py fixtures:
```python
tmp_plugin_dir(tmp_path)      → Path  # isolated plugin directory per test
mock_audio_stream()           → MagicMock  # fake sounddevice.InputStream
headless_gl_context()         → moderngl.Context | MagicMock  # OPENGL_AVAILABLE aware
sample_frame()                → np.ndarray  # (720, 1280, 3) uint8 blank frame
plugin_manifest(tmp_path)     → dict  # valid plugin.json dict written to tmp_path
```

## Inputs and Outputs
- Input: none (creates new files only)
- Output: importable package paths, usable fixtures

## Edge Cases
- `headless_gl_context`: if `moderngl` cannot create a standalone context (CI/no GPU), falls back to `MagicMock` with the same attribute surface. All rendering tests must handle both cases.
- `opengl_raii.py` from VJlive-2 shows the graceful-fallback pattern: `try: from opengl_safe import *; except ImportError: use DummyGL`. Same pattern in conftest.

## Legacy Reference
- `VJlive-2/core/opengl_raii.py` → graceful fallback pattern for GPU unavailability
- `VJlive-2/core/engine.py` → Engine/Matrix/Window layering (informs sub-package split)
- `VJlive-2/core/renderer.py` → Renderer class lives in `rendering/` sub-package

## Test Plan
```bash
# Verify all packages are importable
PYTHONPATH="src:." python3 -c "
import vjlive3.rendering
import vjlive3.audio
import vjlive3.node_graph
import vjlive3.hardware
import vjlive3.api
import vjlive3.effects
print('All packages importable')
"

# Verify conftest fixtures load without error
PYTHONPATH="src:." pytest tests/ -q --collect-only 2>&1 | grep -v "test session"

# Full suite still passes
PYTHONPATH="src:." pytest tests/ -q
```
