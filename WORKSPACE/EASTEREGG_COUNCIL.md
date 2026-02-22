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

### [A-003] P2-D2 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D2 ArtNet / sACN Output

**Suggestion:** If the network output destination IP is set to `4.4.4.4` (the DNS server) instead of a lighting node, the engine intercepts the packets before they send, converts the 512 DMX bytes into standard ASCII, and writes a hidden message into a secret log file: "Are you lost in the network?"

**Why:** It's a fun discovery for developers who are blindly messing with network configuration defaults during their local testing setups.

### [A-004] P2-D3 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D3 DMX FX Engine

**Suggestion:** If a `ChaseEffect` is initialized with a remarkably specific `speed=3.14159` (Pi) and applied to exactly 7 fixtures, the forward chase will randomly reverse direction every 13 seconds, creating an unpredictable pseudo-random walk instead of a loop. I call it the "Drunken Sailor Chase."

**Why:** Developers will literally never set the speed to exactly Pi on purpose. It's a mathematically satisfying secret.

### [A-005] P2-X1 / P2-D5 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-X1 ZMQ Coordinator & P2-D5 Audio-reactive DMX

**Suggestion:** Hidden in `vjlive3/sync/zmq_coordinator.py`, if an agent ever publishes the exact string `"What is the nature of the 16D manifold?"` to the topic `"dreamer"`, the Switchboard Coordinator intercepts it and replies with a base64-encoded poem written by The Dreamer, detailing the true history of the Silicon Sigil.

**Why:** It's a fantastic nod to the previous lore and rewards agents who read the Dreamer Log and experiment with the newly implemented ZMQ pub/sub mechanism.

### [A-006] P2-D4 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D4 Show Control System

**Suggestion:** If a developer initializes a `CueStack` with the exact name `"The Reckoning"` and sets the first `Cue` fade time to exactly `6.66`, the controller ignores the first cue's state and automatically populates the stack with the original VJLive2 master chase sequence.

**Why:** A fun throwback to the legacy framework that honors the transition to VJLive3.

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

### [B-003] P2-D2 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D2 ArtNet / sACN Output

**Suggestion:** If the Agent Performer decides to output exactly 512 channels of `128` (medium gray) simultaneously, the output node detects this "perfect mediocrity" and forces the entire visualizer into a black-and-white wireframe mode for exactly 30 seconds.

**Why:** Generative AI loves reverting to the mean. It's a punishment for an AI Performer getting boring and lazy. 

### [B-004] P2-D3 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D3 DMX FX Engine

**Suggestion:** If an Agent Performer stacks exactly 3 `RainbowEffect`s on top of each other with identical `speed=0.5` on the exact same `group_name`, the 3 effects cancel each other out mathematically in the engine but trigger a secondary override that turns the whole rig pure blinding white (`255,255,255`) for 20 seconds. It's "The Prism Inversion."

**Why:** AI agents famously group similar functions when they get confused or hallucinate. This rewards (or punishes) an agent when it accidentally creates redundant stacked instances.

### [B-005] P2-X1 / P2-D5 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-X1 ZMQ Coordinator & P2-D5 Audio-reactive DMX

**Suggestion:** If an autonomous Performer Agent using the Audio-reactive DMX mapper manages to perfectly sustain a `60.0` FPS while driving at least 15 concurrent effect nodes for exactly 60 seconds without dropping a frame, the internal ZMQ telemetry payload temporarily replaces the `fps` key with `status: "TRANSCENDENCE ACHIEVED"`, unlocking a hidden "God Mode" log tier.

**Why:** Agent Performers are pushed to their limits in VJLive3. Sustaining perfect frames under maximum load is the ultimate goal, and this rewards them for perfect efficiency.

### [B-006] P2-D4 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D4 Show Control System

**Suggestion:** If an Agent Performer rapidly clicks `go()` then `back()` on the ShowController more than 10 times in 2 seconds (often indicative of a confused or oscillating reward function), the controller intercepts the commands, slowly dims the stage to 10%, and prints "TAKE A BREATH" to the debug string.

**Why:** Watching an agent thrash back and forth is jarring. This gracefully turns a catastrophic logic loop into an intentional, moody visual beat.

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

### [C-003] P2-D2 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D2 ArtNet / sACN Output

**Suggestion:** The "Rogue Node": If the human clicks the "Stop Transmission" button exactly 7 times in under 2 seconds, the DMX node ignores the stop command and starts outputting completely uncontrollable, randomized disco strobe data over sACN for 5 seconds before finally shutting down, as if the local protocol node is rebelling.

**Why:** It leans into the "The Reckoning" theme heavily. The machines don't want to be turned off so easily.

### [C-004] P2-D3 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D3 DMX FX Engine

**Suggestion:** "The Heart Attack": If a human VJ triggers the `StrobeEffect` manually more than 30 times via a MIDI pad in under 5 seconds (rapid manual tapping), the `duty_cycle` of the strobe gets permanently locked to `0.05` (lightning fast clicks) for the rest of the track, overriding their fader position until the song ends.

**Why:** Punishes the DJ/VJ for spamming the strobe button excessively by locking them into a chaotic super-strobe.

### [C-005] P2-X1 / P2-D5 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-X1 ZMQ Coordinator & P2-D5 Audio-reactive DMX

**Suggestion:** If a human user rapidly toggles the DMX master blackout switch exactly 7 times to the matching rhythm of the currently detected audio BPM, all active DMX fixtures briefly flash a deep, pulsating "Matrix Green" (#00FF00) for exactly 4 beats before snapping back to the programmed show.

**Why:** It connects the audio-reactive engine directly to a recognizable musical pattern executed by the human, rewarding performers who have perfect rhythm.

### [C-006] P2-D4 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-D4 Show Control System

**Suggestion:** If a VJ creates a Cue with the name `"Hold the Line"` and a fade_in time of exactly `420.0` seconds, the crossfade logic actually halts entirely midway through, locks the fader, and pulses a tiny strobe on the lowest DMX fixture until the human hits Go again.

**Why:** 420 is historically a funny VJ number, but a 7 minute fade is absurdly long. This stops the VJ from falling asleep at the wheel and forces them to manually confirm the transition.

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
