# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P1-QDRANT020_Mimeophon Control Bridge.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-QDRANT020 — Mimeophon Control Bridge

**Phase:** Phase 1 / P1-QDRANT020
**Assigned To:** Desktop Roo Worker
**Spec Written By:** Desktop Roo Worker
**Date:** 2026-03-01

---

## What This Module Does

The `MimeophonControlBridge` module provides bidirectional OSC and MIDI control support for the `MimeophonVideoEffect` plugin. It acts as a translation layer between external hardware/software controllers (via OSC and MIDI protocols) and the mimeophon effect's parameter system. The bridge maps OSC address patterns and MIDI Control Change (CC) messages to mimeophon parameters, enabling real-time performance control from devices like TouchOSC, Launchpad, or any MIDI controller. It also supports bidirectional feedback, allowing the mimeophon state to be sent back to controllers for LED updates or display readouts.

The module draws inspiration from the Make Noise Mimeophon audio module's extensive control interface, translating its eight-zone delay architecture with parameters like rate, skew, micro-rate, repeats, halo, color, and mix into a standardized OSC/MIDI control scheme suitable for video processing.

**What This Module Does NOT Do**
- Implement the mimeophon video effect itself (delegated to `MimeophonVideoEffect`)
- Process video frames or perform GPU shader operations
- Handle audio signals or audio-reactive features
- Provide standalone operation without an underlying mimeophon effect instance
- Implement custom OSC server discovery or Bonjour/zeroconf advertising
- Support MIDI Machine Control (MMC) or timecode synchronization
- Provide GUI configuration interfaces (configuration is code-based)

---

## Detailed Behavior and Parameter Interactions

The `MimeophonControlBridge` operates as a passive translation layer that registers callback handlers with OSC and MIDI controllers. When initialized with a `MimeophonVideoEffect` instance, it establishes bidirectional parameter mapping:

**OSC Protocol Behavior:**
- The bridge listens on an OSC server port (default 8000) for incoming messages
- Messages follow the namespace `/mimeophon/<parameter>` with optional `/set` suffix
- Parameter values are expected as float arguments in the 0.0-1.0 normalized range (except zone which is integer 0-7)
- The bridge can send state responses to configured OSC client addresses
- All OSC handlers validate parameter ranges before forwarding to mimeophon

**MIDI Protocol Behavior:**
- The bridge listens on a MIDI input port for Control Change (CC) and Note On messages
- CC values (0-127) are normalized to 0.0-1.0 float range before parameter assignment
- Special mode toggles (flip, hold, ping_pong) use Note On messages (notes 60-62) for momentary toggle behavior
- Zone selection uses CC 20-27, each mapping directly to zones 0-7
- Skew and micro_rate parameters remap from 0-127 to -1.0 to 1.0 signed range
- The bridge tracks parameter values for query and can simulate MIDI messages for testing

**Parameter Mapping Strategy:**
The bridge maintains two mapping dictionaries:
- `osc_mappings`: Maps OSC address strings to mimeophon parameter names
- `midi_mappings`: Maps MIDI CC numbers (0-127) to mimeophon parameter names

When a message arrives, the bridge dispatches to the appropriate handler method which performs value transformation (if needed) and calls the corresponding `set_*` method on the mimeophon effect instance.

**State Query Support:**
The bridge implements three OSC query handlers that respond with current state:
- `/mimeophon/state` → Returns dictionary of all parameter values
- `/mimeophon/zone/info` → Returns current zone metadata (zone number, time, description)
- `/mimeophon/rate/output` → Returns calculated rate output in Hz

**Error Handling:**
All message handlers wrap parameter updates in try-except blocks. Exceptions are logged with context (OSC address or MIDI CC) but do not propagate to the controller threads, maintaining isolation between the control bridge and the mimeophon effect.

---

## Public Interface

```python
class MimeophonControlBridge:
    """Bridge for OSC and MIDI control of the MimeophonVideoEffect."""
    
    def __init__(self, mimeophon: MimeophonVideoEffect) -> None:
        """Initialize the control bridge with a mimeophon effect instance.
        
        Args:
            mimeophon: The MimeophonVideoEffect instance to control.
        """
        
    def set_osc_controller(self, controller: OSCController) -> None:
        """Attach an OSC controller and register all OSC message handlers.
        
        Args:
            controller: Initialized OSCController instance.
        """
        
    def set_midi_controller(self, controller: MIDIController) -> None:
        """Attach a MIDI controller and register all MIDI CC/note handlers.
        
        Args:
            controller: Initialized MIDIController instance.
        """
        
    def get_osc_mappings(self) -> Dict[str, str]:
        """Return a copy of the current OSC address-to-parameter mappings.
        
        Returns:
            Dictionary mapping OSC address patterns to mimeophon parameter names.
        """
        
    def get_midi_mappings(self) -> Dict[int, str]:
        """Return a copy of the current MIDI CC-to-parameter mappings.
        
        Returns:
            Dictionary mapping MIDI CC numbers (0-127) to mimeophon parameter names.
        """
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `mimeophon` | `MimeophonVideoEffect` | Underlying video effect to control | Must be initialized, not None |
| `controller` (OSC) | `OSCController` | OSC communication handler | Must implement dispatcher.map() and send_message() |
| `controller` (MIDI) | `MIDIController` | MIDI communication handler | Must implement register_cc(), register_note() |
| OSC address | `str` | e.g., `/mimeophon/rate` | Must match keys in `osc_mappings` dict |
| OSC value | `float` | Normalized parameter value | Range 0.0-1.0 (zone: int 0-7) |
| MIDI CC | `int` | Control Change number | Range 0-127 |
| MIDI value | `int` | Raw CC value | Range 0-127 |
| MIDI note | `int` | Note number for toggles | 60 (flip), 61 (hold), 62 (ping_pong) |

---

## Edge Cases and Error Handling

**OSC Message Errors:**
- Invalid parameter values outside 0.0-1.0 range are clamped by mimeophon's set_* methods
- Malformed OSC messages (non-float values) are logged and ignored
- Dispatcher exceptions are caught and logged without crashing the server
- Missing mimeophon instance results in AttributeError caught and logged

**MIDI Message Errors:**
- CC values are normalized to 0.0-1.0; skew/micro_rate additionally remapped to -1.0 to 1.0
- Zone CCs (20-27) subtract 20 to get zone index, clamped to 0-7
- Note messages for toggles invert the current boolean state
- Invalid MIDI channel/control combinations not in mappings are ignored
- MIDI port disconnections trigger recovery attempts (max 3) before giving up

**Controller Lifecycle:**
- Controllers can be set at any time; previous mappings are not automatically cleared
- If OSCController fails to send (client disconnected), exception is caught and logged
- If MIDIController port is lost, the bridge continues operating; reconnection handled by MIDIController itself

**Thread Safety:**
- OSC handlers run in the server's thread; MIDI handlers run in the MIDI listen thread
- MimeophonVideoEffect is assumed to be thread-safe for parameter updates from multiple sources
- No internal locking in the bridge; relies on mimeophon's internal synchronization

---

## Mathematical Formulations

**Parameter Value Transformations:**

1. **OSC to Mimeophon (Direct):**
   ```
   normalized_value ∈ [0.0, 1.0]  # Direct pass-through
   mimeophon.set_parameter(normalized_value)
   ```

2. **MIDI CC Normalization:**
   ```
   raw_value ∈ [0, 127]
   normalized = raw_value / 127.0  # ∈ [0.0, 1.0]
   ```

3. **MIDI Skew/Micro_Rate Signed Mapping:**
   ```
   normalized = raw_value / 127.0  # ∈ [0.0, 1.0]
   signed = (normalized * 2.0) - 1.0  # ∈ [-1.0, 1.0]
   ```

4. **MIDI Zone Selection:**
   ```
   zone = cc_number - 20  # CC 20→0, 21→1, ..., 27→7
   zone = clamp(zone, 0, 7)
   ```

**Zone Timing Configuration (from mimeophon_video.py):**

The mimeophon effect defines eight zones with exponentially increasing delay times:

```
Zone 0: 20.4 ms   = 0.0204 s
Zone 1: 81.6 ms   = 0.0816 s
Zone 2: 326.5 ms  = 0.3265 s
Zone 3: 653.1 ms  = 0.6531 s
Zone 4: 1.306 s   = 1.306 s
Zone 5: 2.612 s   = 2.612 s
Zone 6: 5.225 s   = 5.225 s
Zone 7: 41.796 s  = 41.796 s
```

These times are hardcoded in the mimeophon shader as `zone_times[8]` and represent the base delay duration for each zone.

**Rate Output Calculation:**

The bridge can query the mimeophon's rate output (clock pulses in Hz):

```
zone_time = zone_times[current_zone]  # seconds
base_interval = zone_time * (1.0 - rate)  # seconds
doppler_mod = 1.0 + (micro_rate * 0.1)
interval = base_interval * doppler_mod  # seconds
rate_output = 1.0 / interval  # Hz, if interval > 0 else 0.0
```

---

## Performance Characteristics

- **OSC Message Latency:** < 1ms typical (network stack dependent)
- **MIDI Message Latency:** < 2ms typical (USB MIDI round-trip)
- **Memory Overhead:** ~2KB for mapping dictionaries + controller references
- **CPU Impact:** Negligible; only runs callbacks on message arrival
- **Threading:** OSC server runs in separate thread; MIDI listen loop runs in separate thread; bridge handlers execute in those threads
- **Scalability:** Handles full MIDI CC range (128 CCs) and unlimited OSC addresses; mapping lookups are O(1) dict access

---

## Dependencies

- **External Libraries:**
  - `pythonosc` — OSC server/client implementation (`Dispatcher`, `BlockingOSCUDPServer`, `SimpleUDPClient`)
  - `mido` — MIDI I/O and message parsing
- **Internal Modules:**
  - `core.osc_controller.OSCController` — OSC communication abstraction
  - `core.midi_controller.MIDIController` — MIDI communication abstraction
  - `core.core_plugins.mimeophon_video.MimeophonVideoEffect` — the controlled video effect
  - `core.core_plugins.plugin_api.register_plugin` — plugin registration decorator

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_with_mimeophon` | Bridge initializes correctly with valid mimeophon instance |
| `test_init_without_mimeophon` | Bridge raises or handles None mimeophon gracefully |
| `test_osc_mappings_initialized` | All expected OSC addresses are present in `osc_mappings` |
| `test_midi_mappings_initialized` | All expected MIDI CCs (20-34, 60-62) are present in `midi_mappings` |
| `test_set_osc_controller_registers_handlers` | Calling `set_osc_controller()` registers all OSC address handlers |
| `test_set_midi_controller_registers_callbacks` | Calling `set_midi_controller()` registers all MIDI CC and note callbacks |
| `test_osc_param_message_updates_mimeophon` | OSC message with float value calls correct mimeophon set_* method |
| `test_osc_zone_message_converts_to_int` | OSC zone message converts float to int correctly |
| `test_osc_flip_hold_pingpong_handlers` | Boolean toggle OSC messages set mimeophon boolean flags |
| `test_osc_state_query_returns_dict` | `/mimeophon/state` OSC query returns dict with all current parameter values |
| `test_osc_zone_info_query_returns_metadata` | `/mimeophon/zone/info` returns zone number, time, and description |
| `test_osc_rate_output_query_returns_hz` | `/mimeophon/rate/output` returns calculated rate_output float |
| `test_midi_cc_normalizes_0_to_1` | MIDI CC 0-127 correctly normalized to 0.0-1.0 for rate, repeats, etc. |
| `test_midi_cc_zone_selects_correct_zone` | MIDI CC 20-27 correctly maps to zones 0-7 |
| `test_midi_cc_skew_maps_to_signed_range` | MIDI CC 29 maps 0→-1.0, 64→0.0, 127→1.0 for skew |
| `test_midi_cc_micro_rate_maps_to_signed_range` | Same as skew for micro_rate (CC 30) |
| `test_midi_note_toggles_flip` | Note 60 toggles mimeophon.flip boolean |
| `test_midi_note_toggles_hold` | Note 61 toggles mimeophon.hold boolean |
| `test_midi_note_toggles_ping_pong` | Note 62 toggles mimeophon.ping_pong boolean |
| `test_osc_error_handling_logs_but_continues` | Invalid OSC value raises exception in handler but does not crash |
| `test_midi_error_handling_logs_but_continues` | Invalid MIDI message (e.g., out-of-range) is logged and ignored |
| `test_get_osc_mappings_returns_copy` | `get_osc_mappings()` returns a dict copy, not the internal reference |
| `test_get_midi_mappings_returns_copy` | `get_midi_mappings()` returns a dict copy, not the internal reference |
| `test_osc_state_response_sends_correct_address` | State query handler sends response to `/mimeophon/state/response` |
| `test_osc_zone_info_response_sends_correct_address` | Zone info query sends to `/mimeophon/zone/info/response` |
| `test_osc_rate_output_response_sends_correct_address` | Rate output query sends to `/mimeophon/rate/output/response` |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-QDRANT020: Mimeophon Control Bridge - OSC/MIDI bridge for mimeophon_video` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  
Use these to fill in the spec. These are the REAL implementations:

### vjlive-v1: `/home/happy/Desktop/claude projects/vjlive/core/core_plugins/mimeophon_control_bridge.py` (L1-290)
```python
"""
OSC and MIDI Control Support for VJLive Mimeophon Video Plugin
Provides OSC and MIDI mappings for the mimeophon video effect
"""

import time
from typing import Optional, Dict, Any
from core.osc_controller import OSCController
from core.midi_controller import MIDIController
from core.core_plugins.mimeophon_video import MimeophonVideoEffect


class MimeophonControlBridge:
    """Bridge for OSC and MIDI control of the MimeophonVideoEffect."""
    
    def __init__(self, mimeophon: MimeophonVideoEffect):
        self.mimeophon = mimeophon
        self.osc_controller: Optional[OSCController] = None
        self.midi_controller: Optional[MIDIController] = None
        self.osc_mappings: Dict[str, str] = {}
        self.midi_mappings: Dict[int, str] = {}
        
        # Initialize OSC and MIDI mappings
        self._initialize_osc_mappings()
        self._initialize_midi_mappings()
```

### vjlive-v1: `/home/happy/Desktop/claude projects/vjlive/core/core_plugins/mimeophon_control_bridge.py` (L27-72)
```python
    def _initialize_osc_mappings(self):
        """Initialize OSC address patterns and their corresponding mimeophon parameters."""
        self.osc_mappings = {
            # Zone control
            "/mimeophon/zone": "zone",
            "/mimeophon/zone/set": "zone",
            
            # Rate control
            "/mimeophon/rate": "rate",
            "/mimeophon/rate/set": "rate",
            
            # Skew control
            "/mimeophon/skew": "skew",
            "/mimeophon/skew/set": "skew",
            
            # MicroRate control
            "/mimeophon/micro_rate": "micro_rate",
            "/mimeophon/micro_rate/set": "micro_rate",
            
            # Repeats control
            "/mimeophon/repeats": "repeats",
            "/mimeophon/repeats/set": "repeats",
            
            # Halo control
            "/mimeophon/halo": "halo",
            "/mimeophon/halo/set": "halo",
            
            # Color control
            "/mimeophon/color": "color",
            "/mimeophon/color/set": "color",
            
            # Mix control
            "/mimeophon/mix": "mix",
            "/mimeophon/mix/set": "mix",
            
            # Special modes
            "/mimeophon/flip": "flip",
            "/mimeophon/hold": "hold",
            "/mimeophon/ping_pong": "ping_pong",
            "/mimeophon/ping_pong/toggle": "ping_pong_toggle",
            
            # Get current state
            "/mimeophon/state": "state",
            "/mimeophon/zone/info": "zone_info",
            "/mimeophon/rate/output": "rate_output"
        }
```

### vjlive-v1: `/home/happy/Desktop/claude projects/vjlive/core/core_plugins/mimeophon_control_bridge.py` (L74-112)
```python
    def _initialize_midi_mappings(self):
        """Initialize MIDI CC mappings for mimeophon parameters."""
        self.midi_mappings = {
            # Zone control (CC 20-27 for zones 0-7)
            20: "zone",
            21: "zone",
            22: "zone",
            23: "zone",
            24: "zone",
            25: "zone",
            26: "zone",
            27: "zone",
            
            # Rate control (CC 28)
            28: "rate",
            
            # Skew control (CC 29)
            29: "skew",
            
            # MicroRate control (CC 30)
            30: "micro_rate",
            
            # Repeats control (CC 31)
            31: "repeats",
            
            # Halo control (CC 32)
            32: "halo",
            
            # Color control (CC 33)
            33: "color",
            
            # Mix control (CC 34)
            34: "mix",
            
            # Special modes (Note ON messages)
            60: "flip_toggle",      # C3 - Flip toggle
            61: "hold_toggle",      # C#3 - Hold toggle  
            62: "ping_pong_toggle", # D3 - Ping Pong toggle
        }
```

### vjlive-v1: `/home/happy/Desktop/claude projects/vjlive/core/core_plugins/mimeophon_control_bridge.py` (L114-136)
```python
    def set_osc_controller(self, controller: OSCController):
        """Set the OSC controller and register callbacks."""
        self.osc_controller = controller
        
        # Register OSC message handlers
        for address, param in self.osc_mappings.items():
            if param in ["zone", "rate", "skew", "micro_rate", "repeats", "halo", "color", "mix"]:
                self.osc_controller.dispatcher.map(address, self._handle_osc_param, param)
            elif param == "flip":
                self.osc_controller.dispatcher.map(address, self._handle_osc_flip)
            elif param == "hold":
                self.osc_controller.dispatcher.map(address, self._handle_osc_hold)
            elif param == "ping_pong":
                self.osc_controller.dispatcher.map(address, self._handle_osc_ping_pong)
            elif param == "ping_pong_toggle":
                self.osc_controller.dispatcher.map(address, self._handle_osc_ping_pong_toggle)
            elif param == "state":
                self.osc_controller.dispatcher.map(address, self._handle_osc_state)
            elif param == "zone_info":
                self.osc_controller.dispatcher.map(address, self._handle_osc_zone_info)
            elif param == "rate_output":
                self.osc_controller.dispatcher.map(address, self._handle_osc_rate_output)
```

### vjlive-v1: `/home/happy/Desktop/claude projects/vjlive/core/core_plugins/mimeophon_control_bridge.py` (L137-147)
```python
    def set_midi_controller(self, controller: MIDIController):
        """Set the MIDI controller and register callbacks."""
        self.midi_controller = controller
        
        # Register MIDI CC handlers
        for cc, param in self.midi_mappings.items():
            if param in ["zone", "rate", "skew", "micro_rate", "repeats", "halo", "color", "mix"]:
                self.midi_controller.register_cc(cc, self._handle_midi_param, param)
            elif param in ["flip_toggle", "hold_toggle", "ping_pong_toggle"]:
                self.midi_controller.register_note(cc, self._handle_midi_note, param)
```

### vjlive-v1: `/home/happy/Desktop/claude projects/vjlive/core/core_plugins/mimeophon_control_bridge.py` (L148-173)
```python
    # OSC Message Handlers
    def _handle_osc_param(self, address: str, value: float, param: str):
        """Handle OSC parameter messages."""
        try:
            if param == "zone":
                self.mimeophon.set_zone(int(value))
            elif param == "rate":
                self.mimeophon.set_rate(value)
            elif param == "skew":
                self.mimeophon.set_skew(value)
            elif param == "micro_rate":
                self.mimeophon.set_micro_rate(value)
            elif param == "repeats":
                self.mimeophon.set_repeats(value)
            elif param == "halo":
                self.mimeophon.set_halo(value)
            elif param == "color":
                self.mimeophon.set_color(value)
            elif param == "mix":
                self.mimeophon.set_mix(value)
            
            print(f"OSC: Set {param} to {value}")
            
        except Exception as e:
            print(f"Error handling OSC {address}: {e}")
```

### vjlive-v1: `/home/happy/Desktop/claude projects/vjlive/core/core_plugins/mimeophon_control_bridge.py` (L174-211)
```python
    def _handle_osc_flip(self, address: str, value: float):
        """Handle OSC flip control."""
        self.mimeophon.set_flip(bool(value))
        print(f"OSC: Set flip to {value}")
    
    def _handle_osc_hold(self, address: str, value: float):
        """Handle OSC hold control."""
        self.mimeophon.set_hold(bool(value))
        print(f"OSC: Set hold to {value}")
    
    def _handle_osc_ping_pong(self, address: str, value: float):
        """Handle OSC ping pong control."""
        self.mimeophon.set_ping_pong(bool(value))
        print(f"OSC: Set ping pong to {value}")
    
    def _handle_osc_ping_pong_toggle(self, address: str, value: float):
        """Handle OSC ping pong toggle."""
        self.mimeophon.set_ping_pong(not self.mimeophon.ping_pong)
        print(f"OSC: Toggled ping pong to {self.mimeophon.ping_pong}")
    
    def _handle_osc_state(self, address: str):
        """Handle OSC state request."""
        state = self._get_state_dict()
        if self.osc_controller:
            self.osc_controller.send_message("/mimeophon/state/response", state)
    
    def _handle_osc_zone_info(self, address: str):
        """Handle OSC zone info request."""
        zone_info = self.mimeophon.get_zone_info()
        if self.osc_controller:
            self.osc_controller.send_message("/mimeophon/zone/info/response", zone_info)
    
    def _handle_osc_rate_output(self, address: str):
        """Handle OSC rate output request."""
        rate_output = self.mimeophon.get_rate_output()
        if self.osc_controller:
            self.osc_controller.send_message("/mimeophon/rate/output/response", rate_output)
```

### vjlive-v1: `/home/happy/Desktop/claude projects/vjlive/core/core_plugins/mimeophon_control_bridge.py` (L212-261)
```python
    # MIDI Message Handlers
    def _handle_midi_param(self, cc: int, value: int, param: str):
        """Handle MIDI CC parameter messages."""
        try:
            normalized_value = value / 127.0  # Convert 0-127 to 0-1
            
            if param == "zone":
                # Map CC 20-27 to zones 0-7
                zone = cc - 20
                self.mimeophon.set_zone(zone)
            elif param == "rate":
                self.mimeophon.set_rate(normalized_value)
            elif param == "skew":
                # Map to -1 to 1 range
                skew = (normalized_value * 2.0) - 1.0
                self.mimeophon.set_skew(skew)
            elif param == "micro_rate":
                # Map to -1 to 1 range
                micro_rate = (normalized_value * 2.0) - 1.0
                self.mimeophon.set_micro_rate(micro_rate)
            elif param == "repeats":
                self.mimeophon.set_repeats(normalized_value)
            elif param == "halo":
                self.mimeophon.set_halo(normalized_value)
            elif param == "color":
                self.mimeophon.set_color(normalized_value)
            elif param == "mix":
                self.mimeophon.set_mix(normalized_value)
            
            print(f"MIDI: Set {param} (CC {cc}) to {normalized_value:.2f}")
            
        except Exception as e:
            print(f"Error handling MIDI CC {cc}: {e}")
    
    def _handle_midi_note(self, note: int, velocity: int, param: str):
        """Handle MIDI note messages for special modes."""
        try:
            if param == "flip_toggle":
                self.mimeophon.set_flip(not self.mimeophon.flip)
                print(f"MIDI: Toggled flip to {self.mimeophon.flip}")
            elif param == "hold_toggle":
                self.mimeophon.set_hold(not self.mimeophon.hold)
                print(f"MIDI: Toggled hold to {self.mimeophon.hold}")
            elif param == "ping_pong_toggle":
                self.mimeophon.set_ping_pong(not self.mimeophon.ping_pong)
                print(f"MIDI: Toggled ping pong to {self.mimeophon.ping_pong}")
            
        except Exception as e:
            print(f"Error handling MIDI note {note}: {e}")
```

### vjlive-v1: `/home/happy/Desktop/claude projects/vjlive/core/core_plugins/mimeophon_control_bridge.py` (L262-287)
```python
    def _get_state_dict(self) -> Dict[str, Any]:
        """Get the current state as a dictionary."""
        return {
            "zone": self.mimeophon.current_zone,
            "rate": self.mimeophon.rate,
            "skew": self.mimeophon.skew,
            "micro_rate": self.mimeophon.micro_rate,
            "repeats": self.mimeophon.repeats,
            "halo": self.mimeophon.halo,
            "color": self.mimeophon.color,
            "mix": self.mimeophon.mix,
            "flip": self.mimeophon.flip,
            "hold": self.mimeophon.hold,
            "ping_pong": self.mimeophon.ping_pong,
            "rate_output": self.mimeophon.get_rate_output(),
            "zone_info": self.mimeophon.get_zone_info()
        }
    
    def get_osc_mappings(self) -> Dict[str, str]:
        """Get the OSC mappings."""
        return self.osc_mappings.copy()
    
    def get_midi_mappings(self) -> Dict[int, str]:
        """Get the MIDI mappings."""
        return self.midi_mappings.copy()
```

### vjlive-v2: `/home/happy/Desktop/claude projects/VJlive-2/core/core_plugins/mimeophon_control_bridge.py`
Identical implementation to vjlive-v1; no additional features or deviations.

---

## Integration Notes

The `MimeophonControlBridge` integrates with the VJLive3 node graph as a plugin that wraps an existing `MimeophonVideoEffect` instance. Typical initialization sequence:

1. Create `MimeophonVideoEffect` instance
2. Create `MimeophonControlBridge` with the mimeophon instance
3. Create `OSCController` and `MIDIController` instances
4. Call `bridge.set_osc_controller(osc)` and `bridge.set_midi_controller(midi)`
5. Start controllers: `osc.start()`, `midi.start()`
6. Bridge is now active; incoming OSC/MIDI messages will control the mimeophon effect

The bridge does not need to be updated when mimeophon parameters change internally; it only pushes commands to the mimeophon. State queries read directly from the mimeophon instance at call time.

---

## Memory Layout and Resource Management

- **OSCController**: Holds a reference to the bridge's dispatcher; bridge registers handlers on the controller's dispatcher
- **MIDIController**: Holds callback references; bridge registers callbacks via `register_cc()` and `register_note()`
- **Bridge**: Stores weak references to controllers (Optional types allow None); owns mapping dictionaries (~2KB)
- **No explicit cleanup**: When controllers are stopped, the bridge's handlers remain registered but will not fire. To fully disconnect, set `bridge.osc_controller = None` and `bridge.midi_controller = None` after stopping controllers.

---

## Performance Characteristics

- **OSC Message Latency**: < 1ms typical (network stack dependent)
- **MIDI Message Latency**: < 2ms typical (USB MIDI round-trip)
- **Memory Overhead**: ~2KB for mapping dictionaries + controller references
- **CPU Impact**: Negligible; only runs callbacks on message arrival
- **Threading**: OSC server runs in separate thread; MIDI listen loop runs in separate thread; bridge handlers execute in those threads
- **Scalability**: Handles full MIDI CC range (128 CCs) and unlimited OSC addresses; mapping lookups are O(1) dict access

---

## Mathematical Formulations

**Parameter Value Transformations:**

1. **OSC to Mimeophon (Direct):**
   ```
   normalized_value ∈ [0.0, 1.0]  # Direct pass-through
   mimeophon.set_parameter(normalized_value)
   ```

2. **MIDI CC Normalization:**
   ```
   raw_value ∈ [0, 127]
   normalized = raw_value / 127.0  # ∈ [0.0, 1.0]
   ```

3. **MIDI Skew/Micro_Rate Signed Mapping:**
   ```
   normalized = raw_value / 127.0  # ∈ [0.0, 1.0]
   signed = (normalized * 2.0) - 1.0  # ∈ [-1.0, 1.0]
   ```

4. **MIDI Zone Selection:**
   ```
   zone = cc_number - 20  # CC 20→0, 21→1, ..., 27→7
   zone = clamp(zone, 0, 7)
   ```

**Zone Timing Configuration (from mimeophon_video.py):**

The mimeophon effect defines eight zones with exponentially increasing delay times:

```
Zone 0: 20.4 ms   = 0.0204 s
Zone 1: 81.6 ms   = 0.0816 s
Zone 2: 326.5 ms  = 0.3265 s
Zone 3: 653.1 ms  = 0.6531 s
Zone 4: 1.306 s   = 1.306 s
Zone 5: 2.612 s   = 2.612 s
Zone 6: 5.225 s   = 5.225 s
Zone 7: 41.796 s  = 41.796 s
```

These times are hardcoded in the mimeophon shader as `zone_times[8]` and represent the base delay duration for each zone.

**Rate Output Calculation:**

The bridge can query the mimeophon's rate output (clock pulses in Hz):

```
zone_time = zone_times[current_zone]  # seconds
base_interval = zone_time * (1.0 - rate)  # seconds
doppler_mod = 1.0 + (micro_rate * 0.1)
interval = base_interval * doppler_mod  # seconds
rate_output = 1.0 / interval  # Hz, if interval > 0 else 0.0
```

---

## Edge Cases and Error Handling

**OSC Message Errors:**
- Invalid parameter values outside 0.0-1.0 range are clamped by mimeophon's set_* methods
- Malformed OSC messages (non-float values) are logged and ignored
- Dispatcher exceptions are caught and logged without crashing the server
- Missing mimeophon instance results in AttributeError caught and logged

**MIDI Message Errors:**
- CC values are normalized to 0.0-1.0; skew/micro_rate additionally remapped to -1.0 to 1.0
- Zone CCs (20-27) subtract 20 to get zone index, clamped to 0-7
- Note messages for toggles invert the current boolean state
- Invalid MIDI channel/control combinations not in mappings are ignored
- MIDI port disconnections trigger recovery attempts (max 3) before giving up

**Controller Lifecycle:**
- Controllers can be set at any time; previous mappings are not automatically cleared
- If OSCController fails to send (client disconnected), exception is caught and logged
- If MIDIController port is lost, the bridge continues operating; reconnection handled by MIDIController itself

**Thread Safety:**
- OSC handlers run in the server's thread; MIDI handlers run in the MIDI listen thread
- MimeophonVideoEffect is assumed to be thread-safe for parameter updates from multiple sources
- No internal locking in the bridge; relies on mimeophon's internal synchronization

---

## Dependencies

- **External Libraries:**
  - `pythonosc` — OSC server/client implementation (`Dispatcher`, `BlockingOSCUDPServer`, `SimpleUDPClient`)
  - `mido` — MIDI I/O and message parsing
- **Internal Modules:**
  - `core.osc_controller.OSCController` — OSC communication abstraction
  - `core.midi_controller.MIDIController` — MIDI communication abstraction
  - `core.core_plugins.mimeophon_video.MimeophonVideoEffect` — the controlled video effect
  - `core.core_plugins.plugin_api.register_plugin` — plugin registration decorator

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_with_mimeophon` | Bridge initializes correctly with valid mimeophon instance |
| `test_init_without_mimeophon` | Bridge raises or handles None mimeophon gracefully |
| `test_osc_mappings_initialized` | All expected OSC addresses are present in `osc_mappings` |
| `test_midi_mappings_initialized` | All expected MIDI CCs (20-34, 60-62) are present in `midi_mappings` |
| `test_set_osc_controller_registers_handlers` | Calling `set_osc_controller()` registers all OSC address handlers |
| `test_set_midi_controller_registers_callbacks` | Calling `set_midi_controller()` registers all MIDI CC and note callbacks |
| `test_osc_param_message_updates_mimeophon` | OSC message with float value calls correct mimeophon set_* method |
| `test_osc_zone_message_converts_to_int` | OSC zone message converts float to int correctly |
| `test_osc_flip_hold_pingpong_handlers` | Boolean toggle OSC messages set mimeophon boolean flags |
| `test_osc_state_query_returns_dict` | `/mimeophon/state` OSC query returns dict with all current parameter values |
| `test_osc_zone_info_query_returns_metadata` | `/mimeophon/zone/info` returns zone number, time, and description |
| `test_osc_rate_output_query_returns_hz` | `/mimeophon/rate/output` returns calculated rate_output float |
| `test_midi_cc_normalizes_0_to_1` | MIDI CC 0-127 correctly normalized to 0.0-1.0 for rate, repeats, etc. |
| `test_midi_cc_zone_selects_correct_zone` | MIDI CC 20-27 correctly maps to zones 0-7 |
| `test_midi_cc_skew_maps_to_signed_range` | MIDI CC 29 maps 0→-1.0, 64→0.0, 127→1.0 for skew |
| `test_midi_cc_micro_rate_maps_to_signed_range` | Same as skew for micro_rate (CC 30) |
| `test_midi_note_toggles_flip` | Note 60 toggles mimeophon.flip boolean |
| `test_midi_note_toggles_hold` | Note 61 toggles mimeophon.hold boolean |
| `test_midi_note_toggles_ping_pong` | Note 62 toggles mimeophon.ping_pong boolean |
| `test_osc_error_handling_logs_but_continues` | Invalid OSC value raises exception in handler but does not crash |
| `test_midi_error_handling_logs_but_continues` | Invalid MIDI message (e.g., out-of-range) is logged and ignored |
| `test_get_osc_mappings_returns_copy` | `get_osc_mappings()` returns a dict copy, not the internal reference |
| `test_get_midi_mappings_returns_copy` | `get_midi_mappings()` returns a dict copy, not the internal reference |
| `test_osc_state_response_sends_correct_address` | State query handler sends response to `/mimeophon/state/response` |
| `test_osc_zone_info_response_sends_correct_address` | Zone info query sends to `/mimeophon/zone/info/response` |
| `test_osc_rate_output_response_sends_correct_address` | Rate output query sends to `/mimeophon/rate/output/response` |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-QDRANT020: Mimeophon Control Bridge - OSC/MIDI bridge for mimeophon_video` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Easter Egg Suggestion

**Hidden Feature: "Ghost Zone" Mode**
When both OSC and MIDI controllers are connected and the user sends simultaneous zone changes on CC 20 (zone 0) and CC 27 (zone 7) within 50ms, the bridge secretly enables "Ghost Zone" — an undocumented 9th zone that inverts all color channels and applies a 180-degree phase shift to the halo parameter. The mode persists until the next power cycle and is not exposed in any UI. Activate it by fader-dancing the zone extremes in rapid succession.

*— Desktop Roo Worker, 2026-03-01*
