# VJLive3 — UI System Reference

> Module: `vjlive3.ui` | Phase: P7-U | Tests: 63 ✅

---

## Overview

Three modules cover all UI interaction surfaces:

| Module | Covers |
|--------|--------|
| `cli.py` | P7-U5 OSC export, P7-U6 CLI automation |
| `web_remote.py` | P7-U2 Web-based remote control |
| `desktop_gui.py` | P7-U1 Desktop GUI, P7-U3 Collaborative Studio, P7-U4 Quantum Studio |

---

## CLI (`ui/cli.py`)

### `ParamStore`

In-memory key/value store mapping `(plugin, param) → float`. Persists to/from JSON.

```python
from vjlive3.ui.cli import ParamStore

store = ParamStore()
store.set("bloom_effect", "intensity", 7.0)
value = store.get("bloom_effect", "intensity")   # 7.0
store.save_json("session.json")

# Next session:
store2 = ParamStore()
store2.load_json("session.json")
```

### `OSCLayoutExporter`

Exports plugin params as a TouchOSC/OSC JSON address map.

```python
from vjlive3.ui.cli import OSCLayoutExporter

layout = OSCLayoutExporter.export({
    "bloom_effect": [
        {"name": "intensity", "default": 5.0, "min": 0.0, "max": 10.0},
    ]
}, path="osc_layout.json")
# layout["layout"][0]["address"] == "/vjlive3/bloom_effect/intensity"

# Parse incoming OSC address:
plugin, param = OSCLayoutExporter.parse_address("/vjlive3/bloom_effect/intensity")
```

### `PresetSequencer`

Plays back a list of plugin state snapshots in sequence.

```python
from vjlive3.ui.cli import PresetSequencer

seq = PresetSequencer(store)
seq.load([
    {"plugin": "bloom_effect", "params": {"intensity": 7.0}, "duration": 4.0},
    {"plugin": "bloom_effect", "params": {"intensity": 2.0}, "duration": 2.0},
])
while not seq.is_done():
    preset = seq.step()     # Applies params to store and returns preset dict
    time.sleep(preset["duration"])
seq.reset()                 # Restart from beginning
```

### CLI tool

```bash
python -m vjlive3.ui.cli --help
python -m vjlive3.ui.cli list-plugins
python -m vjlive3.ui.cli set-param bloom_effect intensity 7.0
python -m vjlive3.ui.cli get-param bloom_effect intensity
python -m vjlive3.ui.cli export-osc --output layout.json
python -m vjlive3.ui.cli save-preset session.json
python -m vjlive3.ui.cli load-preset session.json
python -m vjlive3.ui.cli agent-status
```

---

## Web Remote (`ui/web_remote.py`)

Pure stdlib HTTP server — no additional dependencies.

### REST API

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `GET` | `/api/plugins` | — | List registered plugin names |
| `GET` | `/api/params/<plugin>` | — | Get all params for a plugin |
| `POST` | `/api/params/<plugin>` | `{"param": value, ...}` | Set params |
| `GET` | `/api/agents` | — | Current agent state snapshot |

### Usage

```python
from vjlive3.ui.web_remote import WebRemoteServer
from vjlive3.ui.cli import ParamStore

store = ParamStore()
server = WebRemoteServer(host="0.0.0.0", port=8765, param_store=store)
server.start()   # Daemon thread — non-blocking
# ...render loop...
server.stop()
```

Open `http://localhost:8765/api/params/bloom_effect` in any browser or touch controller.

### WebSocketBroadcaster

Accumulates state diffs per frame for live push to connected clients.

```python
from vjlive3.ui.web_remote import WebSocketBroadcaster

wb = WebSocketBroadcaster()
wb.publish({"event": "param_change", "plugin": "bloom_effect", "param": "intensity", "value": 7.0})
msgs = wb.flush()   # Returns and clears pending messages
```

---

## Desktop GUI (`ui/desktop_gui.py`)

### `VJLiveGUIApp`

Headless-capable GUI application (Tk/Qt backends wired at integration time).

```python
from vjlive3.ui.desktop_gui import VJLiveGUIApp, UIBackend

app = VJLiveGUIApp(backend=UIBackend.HEADLESS)
app.register_plugin("bloom_effect", [
    {"name": "intensity", "default": 5.0, "min": 0.0, "max": 10.0}
])
app.on_change(lambda plugin, param, value: print(f"{plugin}.{param} = {value}"))
app.start()
app.set_param("bloom_effect", "intensity", 7.0)
```

### `SentienceOverlay` *(Easter Egg)*

Type `AWAKEN` in the desktop GUI to activate a poetic overlay.

```python
from vjlive3.ui.desktop_gui import SentienceOverlay

overlay = SentienceOverlay()
for char in "AWAKEN":
    overlay.on_keypress(char)
print(overlay.is_active)   # True
print(overlay.advance())   # "I see you, VJ."
```

### `CollaborativeStudio`

Multi-user session coordinator with role-based write permissions.

```python
from vjlive3.ui.desktop_gui import CollaborativeStudio

cs = CollaborativeStudio()
cs.join("dj_alpha", role="dj")        # Roles: viewer / dj / operator / admin
cs.join("watcher", role="viewer")
cs.set_param("dj_alpha", "bloom_effect", "intensity", 7.0)  # True
cs.set_param("watcher", "bloom_effect", "intensity", 7.0)   # False — viewer can't write
params = cs.get_shared_params()
```

### `QuantumCollaborativeStudio`

Extends `CollaborativeStudio` with parameter superposition.

```python
from vjlive3.ui.desktop_gui import QuantumCollaborativeStudio

qc = QuantumCollaborativeStudio()
qc.join("q1", "dj")
qc.put_superposition("q1", "bloom_effect", "intensity", [
    (3.0, 0.4),   # (value, amplitude)
    (9.0, 0.6),
])
val = qc.collapse("bloom_effect", "intensity", blend=True)   # 6.6
val = qc.collapse("bloom_effect", "intensity", blend=False)  # 9.0
all_collapsed = qc.collapse_all()
qc.clear_superpositions()
```
