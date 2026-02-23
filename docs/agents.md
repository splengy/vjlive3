# VJLive3 — Agent System Reference

> Module: `vjlive3.agents` | Phase: P6-AG | Tests: 130 ✅

---

## Overview

The Agent System provides an autonomous 16-dimensional physics simulation that influences VJLive3's visual pipeline in real time. Agents roam a toroidal manifold, respond to audio (bass, beat), and publish their state to every plugin's render context.

```
AgentBridge
 ├── Manifold16D  ← toroidal phase space with gravity wells
 ├── AgentPhysics ← Euler integrator (damping + bass impulse)
 └── AgentMemory  ← 50-snapshot ring buffer per agent
```

---

## `Agent` (`agents/agent.py`)

Represents a single autonomous entity.

| Attribute | Type | Description |
|-----------|------|-------------|
| `position` | `ndarray (16,)` | Location in [0, 1)^16 |
| `velocity` | `ndarray (16,)` | Current velocity |
| `energy` | `float` | Life remaining; decays each tick |
| `state` | `AgentState` | `ACTIVE`, `DECAYING`, or `DEAD` |
| `age` | `float` | Total time alive (seconds) |
| `id` | `str` | Unique UUID string |

### Key methods

| Method | Returns | Notes |
|--------|---------|-------|
| `tick(dt)` | — | Advance position, decay energy, update state |
| `apply_impulse(v)` | — | Add velocity; clamps to `max_speed` |
| `is_alive()` | `bool` | `state != DEAD` |
| `screen_xy()` | `(float, float)` | Project 16D → 2D screen [0,1) |
| `to_param_influence(n)` | `ndarray (n,)` | Influence vector for plugin params |

---

## `Manifold16D` (`agents/manifold.py`)

A 16-dimensional torus: all coordinates are periodic in [0, 1).

```python
from vjlive3.agents.manifold import Manifold16D, GravityWell
import numpy as np

m = Manifold16D()
m.add_gravity_well(GravityWell(
    centre=np.full(16, 0.5, dtype='f'),
    strength=0.8,
    radius=2.0,
    label="centre_pull",
))
force = m.total_gravity_force(agent.position)
```

### `GravityWell`

| Field | Default | Description |
|-------|---------|-------------|
| `centre` | required | 16D centre point (padded if < 16 dims) |
| `strength` | `1.0` | Attraction magnitude |
| `radius` | `2.0` | Effective radius (0 = unbounded) |
| `softening` | `0.05` | Prevents infinite force at centre |
| `label` | `""` | Identifier for `remove_gravity_well()` |

### Key methods

| Method | Description |
|--------|-------------|
| `distance(a, b)` | Toroidal Euclidean distance |
| `total_gravity_force(pos)` | Sum of all well forces at position |
| `project_to_screen(pos)` | Project 16D → (x, y) in [0,1) |
| `wrap(pos)` | Apply toroidal boundary conditions |
| `add/remove/clear_wells(...)` | Manage gravity wells |

---

## `AgentPhysics` (`agents/physics.py`)

Frame-rate-independent Euler integrator.

```python
from vjlive3.agents.physics import AgentPhysics

physics = AgentPhysics(manifold, damping=0.85, bass_impulse_scale=0.3)
physics.step(agents, dt=1/60, audio={"bass": 0.7, "beat": 1.0})
```

Force pipeline per tick: **gravity wells → bass impulse → damping → position integration**.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `damping` | `0.85` | Velocity multiplier per second |
| `bass_impulse_scale` | `0.3` | Bass loudness → impulse strength |
| `gravity_scale` | `1.0` | Global gravity multiplier |

Static helpers: `spawn(energy, position)`, `cull_dead(agents)`.

---

## `AgentMemory` (`agents/memory.py`)

50-snapshot ring buffer per agent.

```python
from vjlive3.agents.memory import AgentMemory, Snapshot

mem = AgentMemory(capacity=50)
mem.push_from_agent(agent, context_hash=hash(ctx))

latest = mem.recall(1)          # Most recent snapshot
all_snaps = mem.replay()        # Chronological order
diff = mem.diff(n=5)            # Displacement vs 5 frames ago
traj = mem.trajectory_positions()  # (N, 16) position array
```

---

## `AgentBridge` (`agents/bridge.py`)

Central coordinator — call once per render frame.

```python
from vjlive3.agents.bridge import AgentBridge
from vjlive3.agents.manifold import GravityWell
import numpy as np

bridge = AgentBridge(max_agents=8, auto_spawn=True, snapshot_interval=0.1)
bridge.add_gravity_well(GravityWell(centre=np.full(16, 0.5, dtype='f'), strength=0.5))

# In your render loop:
bridge.step(context, dt=1/60)
# context.agent_state is now populated.
```

### After `bridge.step()`, `context.agent_state` contains:

| Key | Type | Description |
|-----|------|-------------|
| `agents` | `List[Agent]` | All alive agents |
| `screen_positions` | `List[(x, y)]` | 2D projections in [0,1) |
| `param_influences` | `ndarray (N, 8)` | Plugin parameter drivers |
| `agent_count` | `int` | Number of active agents |
| `time` | `float` | Total bridge clock (seconds) |

### Audio input (`context.inputs["audio_data"]`)

| Key | Range | Effect |
|-----|-------|--------|
| `bass` | 0–1 | Triggers auto-spawn + radial impulse |
| `beat` | 0–1 | Additional impulse on beat |
| `mid`, `treble` | 0–1 | Available for plugin use |

### Performance

`AgentBridge.step()` with 8 agents + 1 gravity well: **p50 = 0.47ms, p95 = 0.58ms** (budget: 16.67ms at 60fps).
