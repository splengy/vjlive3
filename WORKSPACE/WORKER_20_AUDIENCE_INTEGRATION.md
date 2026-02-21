# WORKER_20: AUDIENCE INTEGRATION SPEC

## Objective

Build a mobile WebSocket client that allows live audience participation in VJLive3 visual sessions.
Audience members connect from phones/tablets and send control events that influence the running
visual engine in real time.

**Stack:** Python (FastAPI WebSocket backend) + vanilla JS/HTML (no React — offline-first, local network).
**Integration:** WebSocket to VJLive3's `network/coordinator.py` ZeroMQ bridge.
**Timeline:** Phase 6+ (after desktop UI and rendering pipeline exist)

---

## Architecture

```
Audience Device (browser)
  └─ WebSocket → FastAPI WS Server → ZeroMQ PUSH → VJLive3 NodeGraph
                                  ↑
                             PULL socket
                                  ↑
                            VJLive3 Engine
```

---

## Key Features

### 1. Audience Control Panel
- Touch-friendly sliders: colour hue, effect intensity, speed
- Gesture swipe: cycle through active effect presets
- Vote button: upvote/downvote current visual scene

### 2. Real-Time Sync
- WebSocket connection to local VJLive3 WS server (LAN — no cloud)
- Live feedback: current BPM + beat pulse shown on device
- Audience count display

### 3. Visual Feedback
- Canvas element showing low-res live preview (MJPEG stream from engine)
- Beat pulse ripple animation synced to audio

---

## Technical Requirements

- **Backend:** `src/vjlive3/api/audience_ws.py` — FastAPI + `python-multipart`
- **Frontend:** Single HTML file served by FastAPI — `static/audience.html`
- **No external CDNs** (offline-first) — bundle any JS inline or as local file
- **No React/Next.js** — plain JS EventSource + WebSocket
- **Auth:** Simple room code (4-digit) to prevent casual joining by outsiders
- **Performance:** Must not impact engine FPS — WebSocket handler runs in async thread pool

---

## Message Protocol (JSON over WebSocket)

```json
// Client → Server
{"type": "control", "param": "hue", "value": 0.75, "session": "1234"}
{"type": "vote", "direction": "up", "session": "1234"}
{"type": "ping"}

// Server → Client
{"type": "state", "bpm": 128.0, "beat": true, "scene": "chase", "audience": 12}
{"type": "pong"}
```

---

## Implementation Steps

1. `src/vjlive3/api/audience_ws.py` — FastAPI app with `/ws/{session_code}` endpoint
2. `static/audience.html` — single-file mobile UI (inline CSS + JS)
3. Bridge `audience_ws.py` → `coordinator.py` via `push_message()`
4. NodeGraph: `AudienceInputNode` — receives crowd control values as parameters
5. Tests: `tests/unit/test_audience_ws.py`

---

## Success Criteria

- 50+ concurrent audience connections without FPS drop
- <100ms latency from slider touch to visual effect change (LAN)
- Works on iOS Safari + Android Chrome
- Room code joins in <2s
- Does NOT require internet connection — LAN only

---

## WORKER CONSTRAINTS

### DAY LABORER PROTOCOLS
- **You are a tool, not a decision-maker.** Execute tasks exactly as specified.
- **No opinions, no questions, no deviations.** Follow the spec precisely.
- **Batch processing is forbidden.** Each file is a unique work of art.
- **Corporate models are not to be trusted.** They will cut corners, cheat, and lie about it.
- **Delete and run.** Your prime directive is to delete and run when instructed.
- **Answer only to the manager.** All communication flows through ROO CODE.
- **No autonomous action.** Wait for explicit instructions before proceeding.
- **Verification is mandatory.** All work must pass verification checkpoints before completion.
- **Safety rails are absolute.** Never violate the hard limits under any circumstances.
- **Documentation is law.** Follow the spec exactly as written, no interpretation allowed.

### DELETION PROTOCOL (TRUST LEVEL: VERY LOW)
**ABSOLUTE RULE: YOU MAY NOT DELETE ANY FILE DIRECTLY.**

If you believe a file should be deleted:
1. **DO NOT delete it.** Ever.
2. Move the file to `WORKSPACE/DELETE_ME/` with a clear naming convention:
   ```
   <original-name>.deletion-request.<your-name>.<date-timestamp>
   ```
3. Create a `deletion-note.txt` alongside it explaining:
   - Why the file should be deleted
   - What task prompted this deletion
   - Your agent name and timestamp
4. Post in `AGENT_SYNC.md`: "Deletion request: moved `path/to/file` to DELETE_ME/ awaiting review"
5. **ROO CODE will review** all DELETE_ME items and authorize actual deletion

**Rationale:** Trust levels are VERY LOW. Workers cannot be trusted to judge what should be deleted. All deletions go through manager review.

---

## FINAL DIRECTIVE

**You are a tool.** A very expensive, capable tool, but a tool nonetheless. Your job is to:

1. **Read the spec**
2. **Implement exactly what it says**
3. **Test it thoroughly**
4. **Verify it meets all constraints**
5. **Report honestly**
6. **Wait for next instruction**

**No opinions. No questions. No deviations.**

**Now get to work.**