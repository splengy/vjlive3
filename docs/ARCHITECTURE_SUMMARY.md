# VJLive3 Architecture Summary

**Last Updated:** 2026-02-26 (00:27 PST)
**Status:** Active Development — Multi-Agent Spec Enrichment Pipeline Running
**Architecture:** Modular Plugin-Based Real-Time Video Processing Engine

## Executive Overview
VJLive3 (The Reckoning) is a professional-grade live visual performance system built on a modern Python stack. It processes video streams through a configurable pipeline of GPU-accelerated effects, designed for VJs, live coders, and digital artists.

**Core Philosophy:** Operation Source Zero — Synthesize the best of both legacy codebases (vjlive/ and VJlive-2/) into one clean, production-ready architecture.

## System Architecture
### High-Level Component Diagram
```
┌─────────────────────────────────────────────────────────────────────┐
│ VJLive3 System │
├─────────────────────────────────────────────────────────────────────┤
│ │
│ ┌─────────────┐ ┌──────────────┐ ┌────────────────────┐ │
│ │ Sources │───▶│ Pipeline │───▶│ Outputs │ │
│ │ (Video In) │ │ (Effects) │ │ (Display/Stream) │ │
│ └─────────────┘ └──────────────┘ └────────────────────┘ │
│ │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ MCP Servers (Knowledge & Coordination) │ │
│ │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐ │
│ │ │ vjlive3brain │ │ vjlive_ │ │ qdrant_ │ │
│ │ │ (Knowledge DB) │ │ switchboard │ │ legacy │ │
│ │ └─────────────────┘ └─────────────────┘ └─────────────┘ │
│ │
│ └──────────────────────────────────────────────────────────────┘ │
│ │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Agent System (Multi-Agent Pipeline) │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ │ julie-roo │ │ maxx-roo │ │ desktop-roo │ │
│ │ │ (OPi .60) │ │ (OPi .50) │ │ (Desktop) │ │
│ │ │ Enrichment │ │ Enrichment │ │ Enrichment │ │
│ │ └─────────────┘ └─────────────┘ └─────────────┘ │
│ │
│ └──────────────────────────────────────────────────────────────┘ │
│ │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Infrastructure │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ │ Julie OPi5 │ │ Maxx OPi5 │ │ Desktop │ │
│ │ │ .60 Qdrant │ │ .50 RKLLM │ │ .168 SSHFS Host │ │
│ │ │ RKLLM NPU │ │ NPU spec_srv│ │ Project Root │ │
│ │ └─────────────┘ └─────────────┘ └─────────────────────┘ │
│ │
│ └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Components
### 1. Video Processing Pipeline
**Location:** `src/vjlive3/core/pipeline.py`
**Purpose:** Orchestrates the flow of video frames through the effect chain.
**Pattern:** Pipeline Pattern

## Effect System
**Location:** `src/vjlive3/plugins/` (NOTE: `src/vjlive3/effects/` does NOT exist yet)
**Purpose:** Modular, reusable visual effects plugins.
**Base Class:** `Effect` (abstract — to be created during Phase 1)
**Required Methods:**
- `apply(frame: np.ndarray, timestamp: float) -> np.ndarray`
- `get_parameters() -> Dict[str, Any]`
- `set_parameter(name: str, value: Any) -> None`

**Effect Categories:**
- **Image Processing:** Blur, sharpen, color correction
- **Generative:** Patterns, particles, fractals
- **Transform:** Rotate, scale, warp
- **Mix/Blend:** Combine multiple sources
- **Custom:** User-defined via shaders or Python
- **Datamosh:** Glitch/compression artifacts
- **Depth:** 3D effects from depth cameras
- **Audio-Reactive:** FFT-driven parameters

**Current Implementation Status:**
- `src/vjlive3/core/` exists with plugin system (api, loader, registry, sandbox)
- `src/vjlive3/plugins/` exists but was largely contaminated and nuked
- 30 skeleton specs generated via RKLLM first pass, enrichment in progress
- Previous contamination: word salad/fraud in ~85 files (see SECURITY_AUDIT)

## Source System
**Location:** `src/vjlive3/sources/` (NOTE: does NOT exist yet — planned for future phase)
**Purpose:** Pluggable video input sources.
**Base Class:** `Source` (abstract — to be created)
**Required Methods:**
- `stream() -> Iterator[np.ndarray]`
- `get_info() -> Dict[str, Any]`

## MCP Servers (Model Context Protocol)
#### 4.1 vjlive3brain (Knowledge Base)
**Location:** `mcp_servers/vjlive3brain/`
**Purpose:** The Repository of Truth — indexes all VJLive concepts from legacy codebases.
**Database:** SQLite (`mcp_servers/vjlive3brain/brain.db`)

## Agent System
#### 5.1 Current Agent Topology (as of 2026-02-25)
| Machine | IP | Agent ID | Pass 1 (Skeleton) | Pass 2 (Enrichment) |
|---|---|---|---|---|
| Desktop | 192.168.1.168 | desktop-roo | — | Roo Code (OpenRouter free) |
| Julie OPi5 | 192.168.1.60 | julie-roo | RKLLM Qwen 4B (NPU) | Roo Code (OpenRouter free) |
| Maxx OPi5 | 192.168.1.50 | maxx-roo | RKLLM Qwen 4B (NPU) | Roo Code (OpenRouter free) |
| Desktop | 192.168.1.168 | Antigravity | — | Manager/Coordinator |

**SSHFS Mount:** All OPis mount `~/VJLive3/` from Desktop via `sshfs happy@192.168.1.168:/home/happy/Desktop/claude projects/VJLive3_The_Reckoning`

## Database Layer
#### 6.1 SQLite Knowledge Base
**File:** `mcp_servers/vjlive3brain/brain.db`
**Purpose:** Persistent storage for ConceptEntry knowledge graph.
**Engine:** SQLite 3 with WAL mode (writers never block readers, readers never block writers)

## Known Issues & Contamination
### Security Audit Findings (2026-02-24)
**CRITICAL:** 85 files (20% of codebase) contaminated with:
- **Word salad hallucination** (41 files, 1,047+ occurrences)
- **Fraud patterns** (5 files)
- **Low-code stubs** (40 files with30 lines actual code)

**Most Egregious Examples:**
- `src/vjlive3/plugins/bad_trip_datamosh.py` — boilerplate (7 identical copies)
- `src/vjlive3/plugins/quantum_hyper_tunnel.py` — stub with fake FBO logic

**Root Cause:** Catastrophic LLM failure during batch generation. Agent hallucinated, batched the hallucination, and failed to detect quality degradation.

**Recommended Action:** Revert to baseline `fb09453` (but contamination exists from Hour 1 per timeline analysis).

## File Location Note
The `depth_parallel_universe.py` file appears to have been moved to the temporary directory during cleanup operations. It is currently located at:
`/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/tmp/ingest_legacy.py`

This file is not part of the legacy codebase and should be treated as a new implementation. The original path `src/vjlive3/plugins/depth_parallel_universe.py` no longer exists in the current file system structure.

**Documentation Maintainer:** Documentation Writer
**Last Verified:** 2026-02-26 00:27 PST
**Status:** Active — All systems operational despite codebase contamination issues