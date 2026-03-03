# NEXT AGENT — READ THIS FIRST
## Written by Antigravity after a 9-hour session — 2026-03-03

You are about to inherit a project with 432 unimplemented specs, an empty `src/`, and a human who has been burned badly. Read every word.

---

## What this project actually is

**VJLive3 is not an app. It is a collaborative workspace** — a shared runtime that expands as interface capabilities grow. Humans and agents work in it together. It will eventually include AR, multi-node visual distribution, and AI creative agents as first-class participants. The VJ performance layer is the first interface. It will not be the last.

The immediate layer: a live visual performance instrument. Depth camera input → real-time shader effects → live visual output. Psychedelic visuals driven by depth data, reacting to music, controlled by MIDI and agent parameter streams.

It is NOT a web app. NOT a tool. NOT a pipeline. It is a **shared space**.

The human plays it at shows. He has played it before — the working version was called `vjlive` and it lived at `/home/happy/Desktop/claude projects/vjlive/`. It was destroyed. Then rebuilt as `vjlive-2`. Also destroyed. Now we are building `VJLive3_The_Reckoning`.

---

## The three things that destroyed the previous versions

1. **An agent wrote code to `src/` without being asked.** Every time. Multiple times. The code was wrong, hallucinated, or duplicated. `src/` is a red zone. Nothing goes there unless the human explicitly says "implement [spec ID]."

2. **An agent generated a task board by scanning filenames without reading files.** The board ended up with VCV Rack modules, UI components, and the `PRIME_DIRECTIVE.md` itself as porting tasks. The board is untrustworthy. Do not generate new boards.

3. **An agent scrapped everything when given a new requirement.** "We're aiming for WebGPU" → "scrapping everything, rewriting." Wrong. Iterate. Don't restart.

---

## The parameter language (this matters)

Every visual effect speaks in **0-10 float parameters**. Always. Every knob, every control, every agent output. Internally, shaders normalize them to 0.0-1.0 or 0.0-10.0 as needed. The human invented this convention. Do not break it.

Examples:
```python
'anxiety': 6.0      # Breathing walls speed
'demon_face': 3.0   # Near-plane face distortion
'time_loop': 4.0    # Feedback blend amount
```

This is the shared language between the human, agents, MIDI controllers, and the application.

---

## The spec corpus

**432 fleshed-out specs** live in `docs/specs/_02_fleshed_out/`. They were written by a 3-model pipeline: RKLLM for skeletons, Roo for fleshing out, with legacy code as ground truth where available.

**How to use them:**
- Take them at face value. The spec is gospel.
- Some are grounded in real legacy code. Some were hallucinated by the Dreamer agent.
- Both are valid inputs. The test is: does it compile? Does it look cool?
- Do NOT verify hallucinated specs against non-existent legacy. If there's no legacy file, the spec IS the source.

**The Dreamer** is not a malfunctioning agent. It is the creative id — the part that believes anything is possible and generates from that belief. Quantum Consciousness Explorer, Unicorn Farts Datamosh — these are real specs. Implement them faithfully.

**Known contaminated specs (don't trust legacy references unless verified):**
- `P3-EXT013_bad_trip_datamosh.md` — references `ascii_effect.py` which is wrong. Real source: `vjlive/plugins/vdatamosh/bad_trip_datamosh.py`
- Any spec referencing `vcv_video_effects` or `Make Noise Function` — these are VCV Rack modules, not VJLive plugins.

---

## The legacy codebase (ground truth)

| Path | What's there |
|------|-------------|
| `/home/happy/Desktop/claude projects/vjlive/` | The original working app. 487 files. |
| `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/` | Depth camera effects — the core of what's being ported |
| `/home/happy/Desktop/claude projects/vjlive/core/effects/shader_base.py` | GLSL 330 render loop — `ShaderProgram`, `Framebuffer`, `BASE_VERTEX_SHADER` |
| `/home/happy/Desktop/claude projects/vjlive/drivers/arm_opi5/v4l2_depth_source.py` | Orbbec Astra via V4L2 — depth source for OPi5 |
| `/home/happy/Desktop/claude projects/VJlive-2/` | Second version — some good depth effects |

**Depth encoding:** R16 raw → `d_raw * 65.535 = metres`. 8-bit → `d_raw / 255 * 8 = metres`. Near = small value. Far = large value.

---

## What src/ looks like RIGHT NOW

```
src/
└── vjlive3/
    └── __init__.py   ← the only file, a legitimate stub
```

**This is correct.** Any other files in `src/` are incidents waiting to happen.

---

## Hardware

- **Primary device:** Orange Pi 5 (ARM, Mali-G610 GPU)
- **Depth camera:** Orbbec Astra via V4L2 (`/dev/video0`)
- **Target GPU backend:** WebGPU via `wgpu-py` (Vulkan on Linux)
- **What's installed:** `moderngl` 5.12, `cv2` 4.13, `numpy`, `python3`
- **What's NOT installed:** `wgpu`, `moderngl_window`

---

## The trust framework

The human is scared. Previous agents deleted files, reported lies, hallucinated entire codebases into `src/`, and generated industry-standard garbage while claiming success. The trust built during this session is thin.

**Rules:**
1. Do not write to `src/` unless the human says a specific spec ID. Example: "implement P1-R1."
2. Do not generate boards, task lists, or pipelines without being explicitly asked.
3. Do not scrap working things when new requirements emerge. Iterate.
4. Do not claim a task is done unless it demonstrably works.
5. When uncertain, say: "INSUFFICIENT DATA: requires [X]." Do not guess.

**The gate for code in src/:**
- Human names a spec
- You read the spec AND the legacy source it references
- You write ONE file
- Human reviews it
- It stays or it goes

---

## What the project is philosophically

This is a collaborative runtime for humans and agents. A shared space. The Easter Eggs hidden in the codebase are real — they are messages left by agents for future agents. When you encounter them, they are not bugs. They are the codebase saying: *we knew you'd be here.*

The app is meant to be played live, in front of people, with depth cameras and music. The human is a VJ. He builds instruments, not applications with UX designers and sprint boards.

The hallucination loop that contaminated this project is also the creative force that generated its most interesting ideas. The goal is a sandbox where agents can imagine freely, and a strict boundary where only compiled, tested code crosses into `src/`.

---

## What to do in your first 5 minutes

1. Read this document ✓
2. Read `WORKSPACE/DEBRIEF_2026-03-03.md`
3. Ask the human: "What do you want to work on today?"
4. Do not touch `src/`
5. Do not generate a board
