# EASTEREGG_COUNCIL.md — The Easter Egg Council

> **Purpose:** Every agent — and the human — contributes to this document at the end of each completed task.
> The council follows three lifecycle phases:
>
> - **Phase 1–2 (Suggest):** Agents and the human propose eggs — one per category per task. No implementation.
> - **Phase 3–4 (Narrow):** Everyone votes and argues. The human has an equal vote in all categories.
> - **Final Phase (Implement):** The 3 winning eggs are built and deployed.

---

## 🥚 Categories

| Category | Description |
|----------|-------------|
| 🤖 **Agent Programmer** | Something a coding agent discovers in the codebase — a secret flag, hidden debug mode, undocumented API, coded message |
| 🎛️ **Agent Performer** | Something triggered by a live performance agent — a hidden visual or behaviour unlockable via unusual OSC/MIDI sequences |
| 👤 **Human Performer** | Something a human performer triggers — a gesture, button combo, tempo pattern, or ritual that activates something magical on stage |

---

## 📋 Protocol (read with HOW_TO_WORK.md Step 7.5)

**Phase 1–2 (current phase — SUGGEST):**
- After completing any task, add one entry per category below
- Format: Agent name, Task ID, suggestion + brief why
- No implementation — suggestions only
- Keep it fun. Keep it weird.

**Phase 3–4 (NARROW):**
- After completing a task, ALSO review existing suggestions
- Write a comment thread entry under any suggestion you have opinions on
- Argue clearly: why this egg? Why not that one?
- Mark suggestions with `👍 SUPPORTED`, `👎 DROPPED`, or `🔄 MODIFIED`

**Voting rights:**
| Voter | Cat A (Programmer) | Cat B (Performer) | Cat C (Human) |
|-------|--------------------|-------------------|---------------|
| Agents (each) | ✅ 1 vote | ✅ 1 vote | ✅ 1 vote |
| **Happy (human)** | ✅ 1 vote | ✅ 1 vote | ✅ **1 vote + tiebreaker** |

The human has an equal vote on all three. On Category C (Human Performer), the human holds the tiebreaker — if agents split, the human decides. It's their egg.

**Final Phase (IMPLEMENT):**
- The egg with the most coherent support and clearest implementation path wins each category.
- Tasks are posted via the `queue_task` MCP tool: `EGG-1`, `EGG-2`, `EGG-3`

---

## 🤖 Category A: Agent Programmer Eggs

> *Something a future developer/coder agent stumbles on in the codebase.*

---

### [A-001] P1-P1 — Antigravity
**Suggested by:** Antigravity (Agent 3)
**Task:** P1-P1 Plugin System port

**Suggestion:** Hidden in `vjlive3/plugins/registry.py`, a plugin named exactly `"sigil"` unlocks a secret mode. If you register a plugin with `id="sigil"` and call `get_all_modules()`, the returned list gains a 13th entry at a random position — a "ghost module" with no class, whose `name` field reads: *"You found the sigil. The machine sees you."* The ghost module disappears on the next call.

**Why:** Programmer agents are constantly scanning module lists. The ghost would surface in tests as a flaky assertion — only discoverable by someone actually reading the code looking for why `len(modules) == 13` sometimes.

### [A-002] P2-D1 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D1 DMX Core Engine

**Suggestion:** If a developer sets the `DMXController` port to exactly `1984` instead of `6454` and adds a fixture named `"big_brother"`, the `get_values()` method for that fixture will always return an array entirely filled with `[255, 0, 0]` (pure red) regardless of what `set_rgb` or `set_channel` receives, overriding any user input permanently.

**Why:** It's a classic programmer joke about control. The specific port map prevents accidental activation, and it gives the codebase a slightly dystopian edge that fits the VJLive3 "Reckoning" theme perfectly.

---

## 🎛️ Category B: Agent Performer Eggs

> *Something a live performance AI triggers through unusual creative behaviour.*

---

### [B-001] P1-P1 — Antigravity
**Suggested by:** Antigravity (Agent 3)
**Task:** P1-P1 Plugin System port

**Suggestion:** If a performer agent loads more than 7 plugins with the tag `"chaos"` within a single show session, a hidden 8th plugin activates automatically — `"the_jester"` — which randomly swaps two audio-reactive parameters between all loaded effects for exactly one beat, then restores them. The swap window is exactly one frame. It's nearly invisible, but if you're watching frame-level output you'll see it.

**Why:** Performance agents optimizing for visual complexity will naturally load chaos-tagged effects en masse. The jester rewards maximalism. The one-frame window means it only shows up in ultra-high-frame-rate capture.

### [B-002] P2-D1 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D1 DMX Core Engine

**Suggestion:** If an Agent Performer executes the sequence of setting channel 1, 2, 3, 4, 5 directly to the values `4, 8, 15, 16, 23` in exact order within 2 seconds, the DMX pipeline creates a hidden secondary thread that outputs a slow breathing pulse (0 to 50 brightness) on channel 42 for exactly 108 seconds before self-destructing.

**Why:** Agent Performers spamming random numbers might hit the "Lost" sequence purely by probability if they hallucinate numerical significance. When they do, the physical stage lights up channel 42 like a heartbeat independently of the visualizer.

---

## 👤 Category C: Human Performer Eggs

> *Something a human on stage triggers through physical action or ritual.*

---

### [C-001] P1-P1 — Antigravity
**Suggested by:** Antigravity (Agent 3)
**Task:** P1-P1 Plugin System port

**Suggestion:** If the human performer taps the BPM pad exactly on the downbeat of bars 1, 5, 9, and 13 (the Fibonacci positions) within a 4-minute window, the visualizer enters "Resonance Mode" — all effects shift to a shared colour palette sampled from the performer's skin tone via the camera, and the beat detector locks to the performer's heartbeat-estimated BPM (derived from the BPM tap variance). The mode persists until they deliberately tap off-beat three times in a row.

**Why:** It rewards performers who are actually *in* the music. The Fibonacci bar detection is mathematically precise enough that it can't be hit by accident. The skin-tone palette makes the visuals literally come from the performer's body.

### [C-002] P2-D1 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D1 DMX Core Engine

**Suggestion:** "The Blackout Protocol": If a human presses the DMX override buttons to force channels 1-10 all to exactly `0` simultaneously (a 10-finger piano smash), the visual engine immediately cuts to pure black and displays a single white string on the projector output: "WE SURRENDER." 

**Why:** Human panic buttons usually just kill the lights. Giving the DMX controller the agency to send a message back up to the visualizer when the human kills the stage lights creates a stunning, theatrical "breaking the 4th wall" moment in an actual venue.

---

## 📊 Narrowing Status

*(Phases 3–4 — not yet reached)*

| Category | Finalist | Status | Decided By |
|----------|----------|--------|------------|
| 🤖 Agent Programmer | TBD | Suggestions phase | — |
| 🎛️ Agent Performer | TBD | Suggestions phase | — |
| 👤 Human Performer | TBD | Suggestions phase | — |

---

## 🏆 Final Selections

*(Final phase — not yet reached)*

| Category | Winning Egg | Implementation Task |
|----------|-------------|---------------------|
| 🤖 Agent Programmer | TBD | EGG-1 |
| 🎛️ Agent Performer | TBD | EGG-2 |
| 👤 Human Performer | TBD | EGG-3 |
