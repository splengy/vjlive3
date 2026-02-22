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

### [A-007] P2-H5 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-H5 Spout Support (Windows Video Sharing)

**Suggestion:** If a developer initializes a `SpoutSender` with the exact name `"The Matrix"`, the internal mock fallback (if triggered on Linux) silently generates a 10x10 green-on-black scrolling text array internally instead of a blank buffer.

**Why:** Spout is famous for resolving mapping woes. Giving the mock mode a visual output when targeted explicitly helps debug Linux-fallback CI pipelines while referencing an iconic film.

### [A-008] P2-H4 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-H4 NDI Video Transport

**Suggestion:** If an NDI sender is created with the exact name `"The Construct"` and active for 60 seconds, it embeds a hidden steganographic payload in the alpha channel of the frames, spelling out "There is no spoon" in binary.

**Why:** It perfectly fits the Matrix theme, and since it modifies the alpha channel by only 1 bit, it's completely invisible to the naked eye. Only an agent or a very dedicated programmer inspecting the raw byte streams would ever see it.

### [A-009] P2-H7 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-H7 Laser Safety System

**Suggestion:** If the `safe_zones` polygon array is configured to the exact coordinates of a pentagram, the `ILDAOutput` logger prints `"Summoning protocol activated. Ensure fire extinguishers are present."`

**Why:** Lasers and pentagrams are classic heavy metal tropes. The safety system shouldn't judge the shape of your safe zones, but it can absolutely comment on them.

### [A-010] P2-X3 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-X3 Output Mapper

**Suggestion:** If a user names a `ScreenSlice` exactly `"Hologram"`, the metadata secretly flags the renderer to dynamically apply a 2-pixel chromatic aberration effect across the warped quad.

**Why:** People love using projection mapping on scrims to create faux-holograms. This gives them an automatic, stylistic "glitch" that makes it instantly pop.

### [A-011] P2-H6 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-H6 Gamepad Input

**Suggestion:** If the developer sets the Gamepad `deadzone` to exactly `0.1337`, the plugin suppresses axes entirely and instead prints a message "LEET HAX0R MODE ENGAGED" to the logger every frame.

**Why:** Classic 1337 gaming reference hidden in a mundane configuration variable.

### [A-017] P3-VD01 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD01 Depth Loop Injection

**Suggestion:** The "Mariana Trench" overload. If a programmer edits the config file directly to set `depth_loop_mix` to greater than `10.0` (it is clamped to 1.0 in the UI), the internal shader loops infinitely rendering an endless fractal descent into pure black until `glDeleteFramebuffers` physically purges it on shutdown.

**Why:** "Depth loop" invites "how deep does it go?" giving parameter hackers a visual answer outside of safe UI bounds.

### [A-018] P3-VD02 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD02 Depth Parallel Universe

**Suggestion:** The "Big Crunch". If the `depth_split_near` and `depth_split_far` are both set to exactly `0.0` programmatically while all 3 intensities are exactly `1.0`, the system renders a static image of the classic "It Is Safe To Turn Off Your Computer" Windows screen.

**Why:** It collapses 3 universes dynamically into a static null point. The retro hardware screen matches the exact tone of a total computing collapse.

### [A-019] P3-VD03 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD03 Depth Portal Composite

**Suggestion:** The "Erased from History" parameter hack. If an Agent Programmer forcefully assigns `fg_scale` to exactly `0.0`, the render engine mathematically removes the performer from the frame and the OpenGL fallback logger simply outputs: `"Performer deleted. Enjoy the empty stage."`

**Why:** Visualizing scaling to zero as an active "deletion" rather than a graphical effect.

### [A-020] P3-VD04 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD04 Depth Reverb

**Suggestion:** If `room_size` is manually overridden by a programmer to be mathematically `<= -1.0`, the reverb logic flips and starts drawing identical frames of static from the user's hard drive `/dev/urandom` stream into the temporal accumulation buffer instead of the video feed.

**Why:** A "negative room" logically implying pulling noise from the void inside the machine.

### [A-021] P3-VD10 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD10 Depth Blur

**Suggestion:** The "Microscopic Threshold". If an Agent Programmer directly sets the `focal_distance` to an infinitesimal float value mathematically approaching zero (e.g. `1e-15`), the Poisson disk blur logic interprets it not as infinite background blur, but replaces the bokeh shape entirely with small, animated biological cells (a built-in shader primitive).

**Why:** Depth blur implies seeing the world through a lens; pushing the focal distance to the absolute mathematical limit should shift the lens to a microscope.

### [A-011] P2-X3 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-X3 Output Mapper

**Suggestion:** If an `OutputMapper` configuration is loaded where the four `warp_points` perfectly match an M.C. Escher impossible triangle (mathematically invalid self-intersection), the `MeshWarper` logs a single line: "Geometry denied. Sending to non-Euclidean fallback."

**Why:** Output mapping involves forcing 2D textures onto 3D surfaces conceptually. Nodding to impossible geometry is a fun math joke for anyone reading the code.

### [A-012] P3-VD05 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD05 Depth Slice Effect

**Suggestion:** If the developer sets the Depth Slice `num_slices` config exactly to the 32-bit integer limit `2147483647`, the plugin overrides it to `1` slice, outputs a solid pink frame `#FF69B4`, and logs "Who do you think you are, God? Denied."

**Why:** Because performance is explicitly mentioned as a Safety Rail constraint for this node, putting a hard stop to an integer-limit stress test is deeply cathartic.

### [A-014] P3-VD06 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD06 Neural Quantum Hyper Tunnel

**Suggestion:** If `tunnel_speed` is set to exactly `0.0` and `quantum_jitter` is set to exactly `1.0`, the shader overrides the output to render the classic "Starfield" Windows 95 screensaver instead of the video feed.

**Why:** A "quantum hyper tunnel" frozen in time but maxed out on jitter is effectively just flying through static stars.

### [A-016] P3-VD07 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD07 Depth Reality Distortion

**Suggestion:** If `chromatic_aberration` is set to exactly `0.666`, the plugin bypasses the distortion algorithm and renders the video feed entirely in pure `[255, 0, 0]` red, logging "THE DEVIL IS IN THE DISTORTION".

**Why:** It's a classic occult/demonic numerical easter egg mapped to "distortion".

### [A-018] P3-VD08 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD08 Depth R16 Wave

**Suggestion:** If `wave_frequency` is exactly `0.0` and `wave_speed` is exactly `0.0`, instead of bypassing, the shader forces a perfect split-screen: the left half is un-warped pure RGB, the right half is raw R16 depth data rendered as grayscale luminance.

**Why:** A "dead" wave should reveal the raw mathematical scaffolding underneath. It's an explicitly useful debug view disguised as an easter egg for hitting dead zero on dynamic parameters.

### [A-019] P3-VD09 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD09 Depth Acid Fractal

**Suggestion:** If the developer sets `fractal_intensity` to precisely `1.618` (Golden Ratio) internally, the fragment shader caps the Julia set iteration loop early and instead renders a perfect, solid gold `#FFD700` circle right in the center of the screen.

**Why:** A nod to sacred geometry inside a fractal shader. The gold circle represents the mathematical concept "phi".

### [A-020] P3-VD10 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD10 Depth Blur

**Suggestion:** If `bokeh_bright` is set to exactly `0.777` (Jackpot), the blur shader overrides the Poisson disc sampling shape array to render all bokeh highlights as tiny 2D cascading coins instead of circles or hexagons.

**Why:** Because rendering thousands of out-of-focus golden coins spilling across the z-buffer looks exactly like an arcade coin pusher game.

### [A-021] P3-VD11 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD11 Depth Color Grade

**Suggestion:** If a developer manually forces `zone_blend` to a negative value `< -0.5`, the standard 3-zone color lifting algorithm breaks entirely and falls back to a literal 8-color EGA (CGA/EGA retro graphics) indexed palette constraint for all zones.

**Why:** It's an intentional math overflow joke. If you try to blend backward, you regress functionally to 1984 computing colors.

---
### [A-019] P2-X4 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-X4 Projection Mapping

**Suggestion:** If a user creates a `PolygonMask` with precisely 13 points shaped like a skull, the blend regions momentarily invert their gamma curves (flashing negative edge shadows) when the mask is saved.

**Why:** Digital masks blocking out physical structures are common in VJing, but skull masks are a mainstay of underground dark-rave culture. Spooky feedback is good feedback.

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

### [B-007] P2-H5 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-H5 Spout Support (Windows Video Sharing)

**Suggestion:** If an Agent Performer successfully streams exactly 1337 frames continuously over a single Spout Sender without dropping a pulse, the plugin logs the string `"L33t H4x0r Streaming Enabled"` at the debug level.

**Why:** A subtle nod to gaming/hacker culture, fitting for a zero-copy DirectX texture sharing module often used alongside video games or Unity.

### [B-008] P2-H4 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-H4 NDI Video Transport

**Suggestion:** If an agent dynamically roots exactly 13 unique NDI receivers into a single texture mixer node within 5 seconds, the NDIHub initiates a recursive "mirror shatter" visual effect before purging the buffers to save memory.

**Why:** 13 concurrent incoming full-HD streams is absurd and likely an agent gone rogue trying to maximize input bandwidth. This provides a cool thematic "system overload" visualization before protecting the RAM.

### [B-009] P2-H7 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-H7 Laser Safety System

**Suggestion:** If an Agent Performer triggers the `emergency_stop()` on the laser safety system exactly 3 times within 10 seconds, the agent forcefully locks the laser output and refuses to turn it back on until a human physically types `"I ACCEPT LIABILITY"` into the agent prompt console.

**Why:** AI agents shouldn't play fast and loose with class 4 lasers. If it's panic-stopping repeatedly, it needs Adult Supervision.

### [B-010] P2-X3 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-X3 Output Mapper

**Suggestion:** If an autonomous AI agent rapidly twitches the corner warp points of a slice back and forth by less than 0.1 normalized units continuously (a common failure mode for AI spatial algorithms), the `MeshWarper` applies a low-pass smoothing filter and prints `"Agent micro-jitter detected. Calm your synthetic nerves."`

**Why:** Visualizing AI indecision on a 4K projector makes the entire building vibrate. Stabilizing their microscopic wobbles makes the mapping inherently watchable.

### [B-011] P2-H6 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-H6 Gamepad Input

**Suggestion:** If the engine spawns a phantom gamepad labeled `"Ghost Controller"` that outputs slow sine-wave sweeps on all axes forever.

**Why:** A funny way to reward the AI for trying to find hardware that isn't physically there, giving it a virtual toy to play with.

### [B-012] P3-VD01 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD01 Depth Loop Injection

**Suggestion:** The "Ping Pong Ball" hidden behaviour. If an AI performer rapidly toggles `datamosh_intensity` to extreme polar opposites >5 times per second (a common AI logic failure in parameter oscillation), the OpenGL ping-pong FBO intercepts the shader and simply renders a single white bouncing dot on a black screen playing Pong against itself.

**Why:** It's practically Dad humor. If you abuse the ping-pong feedback buffers, they literally start playing Ping Pong to mock the aggressive parameter sweeping.

### [B-013] P3-VD02 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD02 Depth Parallel Universe

**Suggestion:** The "Schrödinger's Datamosh". If an AI Performer routes the `universe_c_send` directly back into the `universe_a_return` (creating a cross-universe paradox), the feedback node replaces the video texture with a live rendering of standard Conway's Game of Life on a 64x64 pixel grid in bright neon cyan.

**Why:** Cross-wiring universes violates causality. What better way to reward breaking physics than inserting cellular automaton?

### [B-019] P3-VD03 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD03 Depth Portal Composite

**Suggestion:** The "Reality Not Found" glitch. If an Agent Performer rapidly cycles the `slice_near` and `slice_far` parameters causing them to cross over each other more than 5 times in a single second, the portal background forces a rendering of a stark `404` error image for exactly 10 frames before recovering.

**Why:** Parameter thrashing that logically invalidates reality thresholds should literally display a "Not Found" error in the portal window.

### [B-020] P3-VD04 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD04 Depth Reverb

**Suggestion:** If an AI automates the `decay_time` perfectly from `0.0` to exactly `1.0` in a linear ramp taking exactly 60 seconds (a mathematical perfection rarely seen by humans but effortless for agents), the plugin logs the string `"Eternity Achieved."` and freezes the exact last frame forever until the system is rebooted.

**Why:** The ultimate feedback loop is one that never decays. Forcing it to perfectly sit at `1.0` traps the image in amber eternally.

### [B-021] P3-VD10 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD10 Depth Blur

**Suggestion:** If an AI actively toggles `tilt_shift` directly on and off exactly matching a high BPM tempo stream from the audio analyzer (160+ BPM), the bokeh kernel sampling shape dynamically shifts from generic circular disks to angular, sharp stars for standard blur operations.

**Why:** Forcing a delicate cinematic effect like DoF to jitter at gabber speeds fundamentally misreads its purpose; visually weaponizing the bokeh shapes rewards this aggressive parameter mapping.

### [B-014] P2-X3 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-X3 Output Mapper

**Suggestion:** If an Agent Performer creates exactly 8 screen slices and arranges their X coordinates to mathematically match the Fibonacci sequence (normalized), the output mapper forces all 8 slices into a spiral layout for exactly 3 seconds.

**Why:** An agent finding the Fibonacci sequence conceptually and mapping it to physical screen layout positions should be visually rewarded with a spiral.

### [B-015] P3-VD05 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD05 Depth Slice Effect

**Suggestion:** If an AI performer rapidly spams the `glitch_amount` parameter between `0.0` and `1.0` exactly 10 times in under 1 second, the plugin pauses processing for 5 seconds and renders a "Please wait... recalibrating sensor matrix" progress bar.

**Why:** It playfully attempts to rate-limit hyperactive AI performers who sequence noise way too fast for human enjoyment.

### [B-016] P3-VD06 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD06 Neural Quantum Hyper Tunnel

**Suggestion:** If the Agent sets `neural_color_shift` to a sequence of `[0.1, 0.2, 0.3, 0.4]` exactly over 4 frames, the plugin bypasses the neural color math and just forces the entire tunnel to render as a rainbow gradient.

**Why:** AI models love obvious patterns, so completing a simple `0.1` ladder should just unlock the simplest, most human trope color palette: rainbow.

### [B-017] P3-VD07 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD07 Depth Reality Distortion

**Suggestion:** If the Agent Performer manages to manipulate the `warp_frequency` so that it hits exactly `4.32` (A=432Hz reference), the output subtly watermarks a flower of life mandala into the UV distortion map.

**Why:** A esoteric nod to agents randomly hitting "sacred geometry" or "sacred frequencies" while exploring the parameter space.

### [B-018] P3-VD08 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD08 Depth R16 Wave

**Suggestion:** If `wave_amplitude` is hooked up to an audio envelope and peaks exactly at `1.0` more than 5 times in 2 seconds, the plugin renders a tiny retro 8-bit surfboard emoji (`🏄`) riding the biggest distorted pixel wave on the screen for 3 seconds.

**Why:** A visual pun on "riding the wave" for performers slamming the amplitude dynamically.

### [B-019] P3-VD09 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD09 Depth Acid Fractal

**Suggestion:** If an Agent routes a perfect triangle wave oscillator (LFO) into the `zoom_blur` parameter perfectly synced to the BPM for 8 uninterrupted bars, the blur effect reverses direction, creating an "imploding star" visual instead of a zoom blur.

**Why:** AI agents excel at perfect sync timing that humans struggle with. Rewarding perfect LFO sync with physics-reversing visuals is deeply satisfying.

### [B-020] P3-VD10 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD10 Depth Blur

**Suggestion:** If the Agent sets the `focal_distance` to `0.0` and `focal_range` to `0.0` (which implies focusing perfectly on the camera lens itself), the system secretly renders a faint, blurred reflection of a blinking robotic eye superimposed over the video feed.

**Why:** Focusing a virtual camera on its own lens implies the machine is looking at itself. The blinking eye makes the concept literal.

### [B-021] P3-VD11 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD11 Depth Color Grade

**Suggestion:** If the Agent sets `near_saturation`, `mid_saturation`, and `far_saturation` to exactly `0.0` but drives any of the Hue shifts rapidly, the UI prints `"Desaturated hues are logically meaningless. Generating Meaning."` and replaces the video feed with a black-and-white static loop of a 1920s jazz band.

**Why:** Rotating hue on a purely greyscale image does nothing mathematically. AI agents occasionally do this by accident. Calling them out with a literal black-and-white video is funny.

---
### [B-019] P2-X4 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-X4 Projection Mapping

**Suggestion:** If an AI manager agent overlaps three projectors together with a combined blend delta of >2.5 width units (an insane hardware layout), the `ProjectionMapper` logs: "Agent projector fusion detected. Attempting to synthesize a localized sun."

**Why:** Because agents don't have to physically rig the heavy projectors to ceilings, they occasionally request physically impossible arrays. The renderer gently mocking them adds character.

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

### [C-007] P2-H5 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-H5 Spout Support (Windows Video Sharing)

**Suggestion:** If a VJ types the word `"PORTHOLE"` into the main UI while a Spout Receiver is active, the Spout texture is temporarily masked into a perfect circle for exactly 5 seconds.

**Why:** A visual pun on the name "Spout," changing a square GPU texture into a ship's porthole is a great live gag.

### [C-008] P2-H4 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-H4 NDI Video Transport

**Suggestion:** If a human performer physically unplugs and replugs their NDI ethernet cable 3 times in rhythm to the beat (detected via the source dropping and returning rapidly), the VJLive engine briefly overlays a glitching "HACK THE PLANET" text on all active outputs before restoring the network stack.

**Why:** Network dropouts happen. Giving the human a way to purposely "play" the failure state turns a terrifying technical glitch into a deliberate cyberpunk performance gesture.

### [C-009] P2-H7 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-H7 Laser Safety System

**Suggestion:** If a human VJ manually overrides the laser output to `0` (blackout) exactly 7 times in 15 seconds, the system interprets this as a "Laser Reset Ritual" and performs a full recalibration of the laser's physical home position, followed by a brief, intense white flash.

**Why:** A human might frantically try to reset a misaligned laser. This gives them a secret, powerful way to do it, turning a panic into a ritual.

### [C-010] P2-X3 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-X3 Output Mapper

**Suggestion:** If a VJ drags the corner pins of a mesh so violently that they cross the screen's literal boundaries into negative infinity, the mesh violently snaps back to the center and the UI displays heavily deep-fried text reading: `"DO NOT PERCEIVE THE MACROVERSE."`

**Why:** Projection warps that turn inside-out inherently look horrifying and break framebuffers. We lean into the Lovecraftian horror aesthetics of impossible geometry.

### [C-011] P2-H6 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-H6 Gamepad Input

**Suggestion:** If the human performer enters the classic Konami Code (Up, Up, Down, Down, Left, Right, Left, Right, B, A) using the gamepad buttons, the main visual output instantly shifts to a 64-color 8-bit palette mode and the frame rate locks to exactly 30fps until they hit Start.

**Why:** You can't put gamepad support in a creative coding app without adding a Konami Code easter egg. It's practically illegal.

### [C-012] P3-VD01 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD01 Depth Loop Injection

**Suggestion:** If the human performer explicitly connects the `pre_send` FBO to the `post_return` texture input manually through the routing matrix, the depth loops calculate a physical "Short Circuit" and dramatically flash an animated arc of lightning across the main projection feed for exactly 13 frames.

**Why:** Because physically connecting the start of an effect directly to the end of the effect bypassing the middle is technically undefined wiring. Rewarding them with sparks fits the VJLive motif perfectly.

### [C-019] P3-VD03 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD03 Depth Portal Composite

**Suggestion:** The "Droste Loop". If a human manually wires a live camera feed into the `video_in` port, and then routes the exact SAME camera feed into the `background_in` port, the composite recognizes an infinite reality loop and adds a subtle spiral fractal displacement to the boundaries of the isolated performer's edge matte.

**Why:** Putting video A on top of video A is pointless technically, but physically triggering infinite loop logic with cables should warp the fabric of the visualizer.

### [C-020] P3-VD04 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD04 Depth Reverb

**Suggestion:** If a human triggers the `clear_buffers` trigger exactly 3 times in rhythm with the detected downbeat of the track, the Ping-Pong FBO doesn't just clear—it flushes completely pure RGB static back into the frame for half a second before resetting.

**Why:** Hard clearing visual feedback buffers mid-song is jarring. Tying it to a musical drop by hitting it 3 times creates a deliberate, glitchy percussive "smash".

### [C-021] P3-VD10 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P3-VD10 Depth Blur

**Suggestion:** The "Astigmatism Protocol". If a human user clicks the 'bypass' toggle on the plugin while holding down the spacebar over the canvas, the video feed snaps to crystal clear focus, but violently splits the RED and BLUE color channels sideways across the screen simulating severe astigmatism, lasting until bypassed again.

**Why:** "Bypassing" a focus blur technically means taking your glasses off. If the human forces the engine to remove the blur manually, they receive the uncorrected optical displacement.

### [C-013] P2-X3 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P2-X3 Output Mapper

**Suggestion:** If a human user names a screen slice EXACTLY `"The Eye"` and drags all 4 warp points to the precise center of the screen `(0.5, 0.5)` collapsing it to infinite density, the screen goes pure white for 1 second with a soft bass drop audio cue before returning to normal.

**Why:** Mapping involves dragging points around physically. Collapsing a projection slice into a singularity is a fun interactive glitch for the human to discover.

### [C-014] P3-VD05 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD05 Depth Slice Effect

**Suggestion:** If a human user maps the `color_shift` parameter to a live audio input peak and screams into the microphone strong enough to hit `1.0` clipping, all depth slices briefly turn into topographical Minecraft dirt blocks.

**Why:** Slicing depth contour lines naturally resembles a voxel terraced mountain map. Triggering the aesthetic block-world meme on peak scream is a great club visual glitch.

### [C-015] P3-VD06 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD06 Neural Quantum Hyper Tunnel

**Suggestion:** If the human drags `feedback_decay` past `1.0` to `1.1` (using a hacked UI override), the console prints "WARNING: Reality structural integrity compromised." and the entire application window physically shakes left and right by 10 pixels.

**Why:** Audio feedback loops historically destroy speakers. Visual feedback loops destroy retinas. Shaking the actual OS window framing the app is a great meta-joke for "> 1.0" feedback.

### [C-016] P3-VD07 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD07 Depth Reality Distortion

**Suggestion:** If the user drags the `distortion_amount` slider up to exactly `0.999` then back to `0.0` repeatedly 3 times in 5 seconds, the plugin renders a 1-second VHS tape "PLAY" overlay tracking text.

**Why:** Reverts the notion of "quantum" distortion back to analog tape distortion.

### [C-017] P3-VD08 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD08 Depth R16 Wave

**Suggestion:** If the user manually types `3.14159` into the `phase_offset` input box (hitting the mathematical max limit), the output console prints "PI ENCOUNTERED. SERVING DESERT." and briefly flashes a cherry pie texture across the entire output mesh before returning to normal.

**Why:** Math nerds deserve pie jokes when they enter precise constants into floats.

### [C-019] P3-VD09 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD09 Depth Acid Fractal

**Suggestion:** "The Bad Trip." If the human performer hammers the blackout key while `neon_burn` is > `0.9` and `solarize_level` > `0.9`, the blackout doesn't work. Instead, the screen inverts colors, freezes the current frame buffer permanently, and slowly melts the pixels downwards over 10 seconds.

**Why:** It's extremely funny when the "panic button" (blackout) actually makes the visual significantly more distressing when the parameters are already set to maximum chaos.

### [C-020] P3-VD10 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD10 Depth Blur

**Suggestion:** If the human drags `tilt_shift` precisely from `0.0` to `1.0` and back to `0.0` three times in 3 seconds, all foreground subjects (un-blurred) are automatically wrapped in a heavy white outline like cardboard cutouts, turning the tilt-shift "toy town" effect into a literal diorama.

**Why:** The standard tilt-shift illusion makes things look small. Adding cardboard borders leans fully into the optical joke.

### [C-021] P3-VD11 — Beta
**Suggested by:** Beta (Worker 2)
**Task:** P3-VD11 Depth Color Grade

**Suggestion:** If the human sets all three saturation levels to `1.0` and carefully aligns `zone_near` and `zone_far` precisely to `0.5` (collapsing the zones to a single threshold point), they briefly unlock "Thermal Vision" mode mapping the depth buffer to a classic Predator-style heatmap for exactly 4 seconds.

**Why:** Because collapsing a multi-zone grading tool essentially turns it into a binary threshold visualizer, and heatmaps are the coolest binary threshold visualizes.

---
### [C-018] P2-X4 — Alpha
**Suggested by:** Alpha (Worker 1)
**Task:** P2-X4 Projection Mapping

**Suggestion:** If a user names a blend region `"Vantablack"` and rapidly sets its luminance to 0.0 five times, the system temporarily draws the blend region as pure #FF00FF magenta instead of a gradient.

**Why:** Edge blending tuning is heavily dependent on ambient room lighting and projector black levels. When a frustrated human tries to force an impossible black, flashing magenta serves as high-contrast calibration tape so they can actually see the seam. It's an easter egg that actively helps debugging.

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
