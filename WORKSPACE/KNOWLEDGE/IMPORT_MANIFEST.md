# IMPORT MANIFEST — VJLive3 The Reckoning

**Purpose:** Authoritative record of every third-party library used across all three codebases.
Agents must check this file before adding any new import.
**Rule:** One library per job. No duplicates. No aspirational installs.

> [!IMPORTANT]
> `pyproject.toml` [dependencies] must exactly match the **INSTALL** column here.
> If you need a new library, add it here first with justification, then add to pyproject.toml.

---

## Legend

| Status | Meaning |
|--------|---------|
| ✅ Installed | Available in current venv |
| ❌ Missing | In pyproject.toml but NOT installed |
| 🚫 Excluded | Explicitly NOT ported to VJLive3 |
| 🔬 Dreamer | Experimental — sandbox only, never in production hot-path |
| 📌 VJLive3 | Added fresh for VJLive3, not in legacy |

---

## Core Rendering & Vision

| Library | pip name | Import | Status | Origin | Reason |
|---------|----------|--------|--------|--------|--------|
| NumPy | `numpy>=1.24` | `import numpy as np` | ✅ Installed | v1, v2, v3 | Frame buffer arrays, all numerical ops. **Central to everything.** |
| OpenCV | `opencv-python-headless>=4.8` | `import cv2` | ✅ Installed | v1, v2 | Video decode, frame resize, color conversion. Headless = no display dep. **Do NOT install `opencv-python` alongside this.** |
| Pillow | `pillow>=10.0` | `from PIL import Image` | ✅ Installed | v1, v2 | Image I/O, thumbnail generation, format conversion. cv2 handles video; PIL handles image assets. |
| ModernGL | `moderngl>=5.8` | `import moderngl` | ✅ Installed | v1, v2 | High-level OpenGL context + shader management. Wraps PyOpenGL. Use this for render pipeline. |
| PyOpenGL | `PyOpenGL>=3.1.6` | `from OpenGL.GL import *` | ✅ Installed | v1, v2 | Raw OpenGL calls (FBO, VAO) needed by ModernGL internals + legacy effect nodes. |
| GLFW | `glfw>=2.5` | `import glfw` | ✅ Installed | v1 (implicit) | Window/context creation for headless rendering. Required by ModernGL. |
| SciPy | `scipy>=1.11` | `import scipy` | ✅ Installed | v1, v2 | Signal processing, FFT, audio analysis. Complements NumPy. |
| Matplotlib | `matplotlib>=3.8` | `import matplotlib` | ✅ Installed | v1, v2 | Debug visualization, waveform plots. **Not in hot-path.** |

---

## Audio

| Library | pip name | Import | Status | Origin | Reason |
|---------|----------|--------|--------|--------|--------|
| SoundDevice | `sounddevice>=0.4` | `import sounddevice as sd` | ✅ Installed | v3-planned | Real-time audio I/O. Cross-platform, wraps PortAudio. **Replaces PyAudio.** |
| PyAudio | `pyaudio` | `import pyaudio` | 🚫 Excluded | v1, v2 | **DO NOT PORT.** Replaced by sounddevice. Legacy code only. PyAudio has broken Python 3.12 wheels. |
| librosa | `librosa>=0.10` | `import librosa` | ❌ Missing | v3-planned | Audio feature extraction (BPM, onset, spectral). Install: `pip install librosa`. |

---

## Video & Streaming

| Library | pip name | Import | Status | Origin | Reason |
|---------|----------|--------|--------|--------|--------|
| PyAV | `av>=10.0` | `import av` | ❌ Missing | v3-planned | Video encode/decode (H.264, ProRes). Install: `pip install av`. |
| NDIlib | `NDIlib` | `import NDIlib` | 🚫 Excluded | v1, v2 | NDI SDK wrapper — system install required, not pip-installable. Use conditional import with graceful fallback. |
| FFmpeg (subprocess) | — | `subprocess` | ✅ (stdlib) | v1, v2 | FFmpeg invoked via subprocess for transcoding. No pip package needed. |

---

## Hardware (MIDI, OSC, DMX, USB)

| Library | pip name | Import | Status | Origin | Reason |
|---------|----------|--------|--------|--------|--------|
| Mido | `mido>=1.3` | `import mido` | ✅ Installed | v1, v2 | MIDI message parsing and routing. Pure Python. |
| python-rtmidi | `python-rtmidi>=1.5` | `import rtmidi` | ✅ Installed (dep of mido) | v3-planned | Low-latency MIDI I/O backend. Used by mido's RtMidi backend. |
| python-osc | `python-osc>=1.8` | `from pythonosc import ...` | ✅ Installed | v1, v2 | OSC (Open Sound Control) protocol for TouchDesigner/VCV integration. |
| PyUSB | `pyusb>=1.2` | `import usb` | ✅ Installed | v1, v2 | Direct DMX USB device access (Enttec Open DMX). |

---

## Web API & Real-Time Comms

| Library | pip name | Import | Status | Origin | Reason |
|---------|----------|--------|--------|--------|--------|
| FastAPI | `fastapi>=0.104` | `from fastapi import ...` | ✅ Installed | v1, v2 | REST API for frontend control panel + agent comms. **Primary API framework.** |
| Uvicorn | `uvicorn>=0.24` | `import uvicorn` | ✅ Installed | v1, v2 | ASGI server for FastAPI. Production-grade async server. |
| WebSockets | `websockets>=12.0` | `import websockets` | ✅ Installed | v1, v2 | Low-level WebSocket protocol for real-time node graph updates. |
| Flask | `flask>=3.0` | `from flask import ...` | ✅ Installed | v1, v2 | **Legacy only** — VJlive-2 used Flask for its web UI. **DO NOT add new Flask code in VJLive3.** FastAPI is the choice. |
| Flask-SocketIO | `flask-socketio>=5.3` | `from flask_socketio import ...` | ✅ Installed | v1, v2 | **Legacy only** — tied to Flask. Replaced by WebSockets + FastAPI in VJLive3. |
| Eventlet | `eventlet>=0.33` | `import eventlet` | ✅ Installed | v1, v2 | **Legacy only** — Flask-SocketIO async backend. Not needed in VJLive3. |
| python-multipart | `python-multipart>=0.0.6` | (auto) | ✅ Installed | v3 | FastAPI file upload support. Required by FastAPI for form data. |

---

## Configuration & Validation

| Library | pip name | Import | Status | Origin | Reason |
|---------|----------|--------|--------|--------|--------|
| Pydantic v2 | `pydantic>=2.0` | `from pydantic import BaseModel, Field` | ✅ Installed | v2, v3 | Data validation, schema enforcement, MCP entry serialization. **Core to the brain DB schema.** |
| pydantic-settings | `pydantic-settings>=2.0` | `from pydantic_settings import ...` | ✅ Installed | v3 | Config loading from env vars + .env files. |
| python-dotenv | `python-dotenv>=1.0` | `from dotenv import load_dotenv` | ✅ Installed | v3-planned | .env file loading for local dev. Already handled by pydantic-settings. **May be redundant — audit before using.** |
| PyYAML | `PyYAML>=6.0` | `import yaml` | ✅ Installed | v1, v2 | Config files, node graph serialization (plugin manifests). |
| jsonschema | `jsonschema` | `import jsonschema` | 🚫 Excluded | v1, v2 | **DO NOT add.** Pydantic v2 replaces jsonschema entirely in VJLive3. |

---

## System & Utilities

| Library | pip name | Import | Status | Origin | Reason |
|---------|----------|--------|--------|--------|--------|
| psutil | `psutil>=5.9` | `import psutil` | ✅ Installed | v1, v2 | CPU/GPU/memory monitoring for performance HUD and FPS governor. |
| watchdog | `watchdog>=3.0` | `from watchdog.observers import ...` | ✅ Installed | v1, v2 | Filesystem watching for plugin hot-reload. |
| Requests | `requests>=2.31` | `import requests` | ✅ Installed | v1, v2 | HTTP client for asset download, license checks. |
| NetworkX | `networkx>=3.1` | `import networkx as nx` | ✅ Installed | v2, v3-planned | Node graph topology (effect chain DAG). |
| SQLAlchemy | `SQLAlchemy>=2.0` | `from sqlalchemy import ...` | ✅ Installed | v2 | **Not active in VJLive3 yet.** Brain DB uses raw sqlite3. Reserve for future ORM use. |
| mss | `mss>=9.0` | `import mss` | ✅ Installed | v3-planned | Screen capture (source input). |
| tqdm | `tqdm>=4.65` | `from tqdm import tqdm` | ✅ Installed | v3-planned | Progress bars for long seeding/indexing operations. |
| click | `click>=8.1` | `import click` | ✅ Installed | v3-planned | CLI tool construction (seeder, enricher scripts). |
| Rich | `rich>=13.0` | `from rich import ...` | ✅ Installed | v3-planned | Formatted terminal output, log tables. |
| ZeroConf | `zeroconf` | `import zeroconf` | 🚫 Excluded | v1 | Bonjour/mDNS discovery. **Not in pyproject.toml — add only when implementing multi-machine sync.** |

---

## MCP / Agent Infrastructure

| Library | pip name | Import | Status | Origin | Reason |
|---------|----------|--------|--------|--------|--------|
| MCP SDK | `mcp>=1.0` | `from mcp.server.fastmcp import FastMCP` | ✅ Installed (v27.1.0) | v3 | Model Context Protocol server framework. Powers vjlive3brain + vjlive_switchboard. **Not in pyproject.toml — add it.** |

---

## Networking / Distributed

| Library | pip name | Import | Status | Origin | Reason |
|---------|----------|--------|--------|--------|--------|
| PyZMQ | `pyzmq>=25.0` | `import zmq` | ✅ Installed | v1, v2 | ZeroMQ sockets for multi-machine sync (optional feature). In pyproject.toml as [distributed] extra. |
| Redis | `redis` | `import redis` | 🚫 Excluded | v2 | Rate limiting in VJlive-2. **Not in pyproject.toml.** Add only if adding distributed session cache. |

---

## AI / ML (Dreamer Tier — Sandbox Only)

> [!CAUTION]
> These libraries are from the Dreamer layer of v1/v2. They are NOT production dependencies.
> They live in `[project.optional-dependencies]` under `dreamer =` — never in base `dependencies`.
> **Any Dreamer import in a non-sandboxed code path is a SAFETY_RAILS violation.**

| Library | pip name | Import | Status | Origin | Reason |
|---------|----------|--------|--------|--------|--------|
| PyTorch | `torch` | `import torch` | 🔬 Dreamer | v1, v2 | Neural effects, VQGAN. Huge (2GB+). Optional, user-installed. |
| Qiskit | `qiskit` | `from qiskit import ...` | 🔬 Dreamer | v1 | Quantum algorithm effects. [DREAMER_LOGIC] territory. |
| scikit-learn | `scikit-learn` | `from sklearn import ...` | 🔬 Dreamer | v2 | ML clustering for color palette generation. Optional. |
| MediaPipe | `mediapipe` | `import mediapipe as mp` | 🔬 Dreamer | v2 | Pose/hand tracking for audience interaction. |
| OpenAI SDK | `openai` | `from openai import ...` | 🔬 Dreamer | v1, v2 | GPT calls for generative effects. |
| Anthropic SDK | `anthropic` | `import anthropic` | 🔬 Dreamer | v1, v2 | Claude API access. Agent bridge. |
| LangGraph | `langgraph` | `import langgraph` | 🔬 Dreamer | v1, v2 | Agent graph orchestration. |
| ImGui | `imgui` | `import imgui` | 🔬 Dreamer | v1, v2 | Debug overlay GUI. Optional dev tool. |
| GPUtil | `gputil` | `import GPUtil` | 🔬 Dreamer | v1 | GPU metrics (redundant with psutil on most systems). |

---

## Explicitly Excluded from VJLive3

| Library | Reason |
|---------|--------|
| `pyaudio` | Broken on Python 3.12. Replaced by `sounddevice`. |
| `jsonschema` | Replaced by Pydantic v2 entirely. |
| `loguru` | In pyproject.toml but not installed and not used. **Remove from pyproject.toml.** Python `logging` standard library is the project standard. |
| `pygame` | In pyproject.toml, not installed, not needed. **Remove from pyproject.toml.** No game engine use case. |
| `bcrypt` | v2 password hashing for web auth. VJLive3 has no user auth layer yet. |
| `cryptography` | v2 JWT/signing. Not needed in current scope. |
| `PyJWT` | v2 auth tokens. Not needed in current scope. |

---

## Required pyproject.toml Corrections

```toml
# ADD to [dependencies]:
"mcp>=1.0",          # MCP SDK — brain server (currently missing!)
"librosa>=0.10.0",   # Audio analysis (currently missing — pip install librosa)  
"av>=10.0.0",        # Video encode/decode (currently missing — pip install av)

# REMOVE from [dependencies] (not installed, not used):
# "loguru>=0.7.0"      — remove, use stdlib logging
# "pygame>=2.5.0"      — remove, no game engine role

# ADD to [optional-dependencies] under dreamer =:
"torch",
"qiskit",
"openai",
"anthropic",
"langgraph",
"mediapipe",
"scikit-learn",
"imgui",
```

---

## Verified Import Check

Run this to verify the core stack is importable:
```bash
PYTHONPATH="src:." python3 - <<'EOF'
imports = [
    ("numpy", "import numpy as np; print(f'numpy {np.__version__}')"),
    ("cv2", "import cv2; print(f'cv2 {cv2.__version__}')"),
    ("PIL", "from PIL import Image; print('PIL OK')"),
    ("moderngl", "import moderngl; print(f'moderngl {moderngl.__version__}')"),
    ("OpenGL", "from OpenGL.GL import glGetError; print('OpenGL OK')"),
    ("sounddevice", "import sounddevice; print(f'sounddevice {sounddevice.__version__}')"),
    ("mido", "import mido; print(f'mido {mido.__version__}')"),
    ("fastapi", "import fastapi; print(f'fastapi {fastapi.__version__}')"),
    ("pydantic", "from pydantic import BaseModel; print(f'pydantic OK')"),
    ("mcp", "from mcp.server.fastmcp import FastMCP; print('mcp OK')"),
    ("watchdog", "import watchdog; print('watchdog OK')"),
    ("networkx", "import networkx; print(f'networkx {networkx.__version__}')"),
    ("psutil", "import psutil; print(f'psutil {psutil.__version__}')"),
    ("yaml", "import yaml; print(f'yaml (PyYAML) OK')"),
]
for name, code in imports:
    try:
        exec(code)
    except Exception as e:
        print(f'FAIL {name}: {e}')
EOF
```

---

## Analysis: Duplicate Roles, Substitutions & Technical Debt

### 🔴 Critical: Two Web Frameworks Installed

**Problem:** Both Flask (legacy) and FastAPI (VJLive3 standard) are installed. Entire v1/v2 web layer is Flask-based.

| Old (v1/v2) | New (VJLive3) | Debt |
|-------------|---------------|------|
| `flask` + `flask_socketio` + `eventlet` | `fastapi` + `uvicorn` + `websockets` | All Flask routes in legacy must be rewritten as FastAPI endpoints. Flask-SocketIO events → FastAPI WebSocket handlers. Estimated: **large** (200+ route handlers in v2). |

**Migration rule:** `from flask import` → error in VJLive3 source. Only FastAPI, Uvicorn, WebSockets in `src/`.

---

### 🔴 Critical: Two Audio I/O Libraries

**Problem:** v1/v2 both use `pyaudio` which is **broken on Python 3.12** (no pre-built wheels, requires PortAudio dev headers).

| Old | New | Debt |
|-----|-----|------|
| `import pyaudio` | `import sounddevice as sd` | API is different but close. `pyaudio.open(...)` → `sd.Stream(...)`. All audio callbacks need rewriting. ~20 files in v2 affected. |

**SoundDevice advantages:** handles duplex I/O, numpy arrays natively (no struct.pack), works headless, Python 3.12 compatible.

---

### 🟡 Moderate: Two Image Libraries with Overlapping Coverage

**Problem:** Both `cv2` and `PIL` do image manipulation. In legacy, they're sometimes used interchangeably for the same operation.

| cv2 | PIL | VJLive3 Rule |
|-----|-----|--------------|
| Video decode, pixel ops, color space conversion | Image file I/O, format conversion, thumbnail | **cv2 = motion/video. PIL = static assets.** Never use PIL to process video frames. Never use cv2 to load/save static image assets. |

No migration needed — just enforce the rule in code review.

---

### 🟡 Moderate: Two Database Layers

**Problem:** `SQLAlchemy` is in pyproject.toml (from v2) but Brain DB uses raw `sqlite3`. Both are installed.

| sqlite3 (stdlib) | SQLAlchemy |
|-----------------|------------|
| Brain DB (`ConceptDB`) | v2 used for app state, sessions, rate limits |
| Direct, fast, no overhead | ORM abstraction, migrations, relationships |

**VJLive3 Decision:** Brain DB stays on raw `sqlite3` (it's optimized for the schema). Future relational data (show presets, session state) → SQLAlchemy. **Do not mix them in the same module.**

---

### 🟡 Moderate: Validation — Two Approaches

**Problem:** v1/v2 used `jsonschema` for manifest validation. VJLive3 uses `pydantic` v2.

| jsonschema | Pydantic v2 |
|------------|-------------|
| Dict-based schema dicts | Python class models with type annotations |
| Manual error messages | Auto-generated validation errors |
| No IDE support | Full type checking, IDE autocomplete |

**Action:** Any ported code using `validate(manifest, schema)` → replace with `MyModel(**manifest)` and catch `ValidationError`. Zero new `jsonschema` imports allowed.

---

### 🟡 Moderate: Logging — Two Patterns

**Problem:** v1/v2 used `loguru` in some files, `logging` in others. VJLive3 declared `loguru` in pyproject.toml but it was never installed.

**Decision (final):** **stdlib `logging` only.** It's the lowest-overhead option (no monkey-patching), plays well with MCP stdio transport, and is already used everywhere in VJLive3 source.

```python
# ✅ Correct — every module
import logging
_logger = logging.getLogger(__name__)

# ❌ Never in VJLive3
from loguru import logger
```

---

### 🟢 Quick Win: Modernize `typing` Imports (Python 3.9+)

**Problem:** Every file in src/ currently imports from `typing`:
```python
# Old pattern (v1/v2 style — required for Python 3.7/3.8)
from typing import Dict, List, Optional, Tuple, Any, Callable, Type
```

**VJLive3 targets Python 3.9+**. Built-in types are subscriptable:
```python
# ✅ Modern — no import needed at all
def process(frames: list[dict[str, Any]]) -> tuple[bool, str | None]: ...

# ✅ Only import what built-ins can't cover
from typing import TYPE_CHECKING, overload, Protocol, TypedDict, Any
```

**Debt:** ~15 files in src/ have redundant typing imports. Low-risk refactor, high readability gain. Run `ruff check --select UP` to auto-fix.

---

### 🟢 Quick Win: Lazy Imports for Heavy Libraries

Heavy libraries (OpenGL, ModernGL, cv2, sounddevice) each add 100-500ms to import time. In VJLive3, import them **inside the class/function that first needs them**, not at module top-level:

```python
# ❌ Bad — loads OpenGL at plugin system startup (500ms penalty)
import moderngl

class DepthShaderPlugin:
    def process(self, frame): ...

# ✅ Good — OpenGL loads only when first plugin is instantiated
class DepthShaderPlugin:
    _mgl_ctx = None

    @classmethod
    def _get_ctx(cls):
        if cls._mgl_ctx is None:
            import moderngl  # lazy — only pays cost on first use
            cls._mgl_ctx = moderngl.create_standalone_context()
        return cls._mgl_ctx
```

**Priority targets for lazy imports:** `moderngl`, `OpenGL`, `cv2`, `sounddevice`, `matplotlib`.

---

### 🟠 Long-term: flask → FastAPI Migration Roadmap

Estimated debt by layer:

| Layer | Files | Effort | Priority |
|-------|-------|--------|----------|
| REST routes (JSON API) | ~40 route handlers | Low — direct translation | P1 |
| SocketIO events → WS | ~60 event handlers | Medium — protocol shift | P2 |
| Eventlet async model | Threading model | High — async refactor | P2 |
| Flask test client → httpx | ~30 test files | Low — API compatible | P1 (with routes) |

Flask and FastAPI can coexist during migration (both on different ports). Do NOT attempt a big-bang migration — port module by module.
