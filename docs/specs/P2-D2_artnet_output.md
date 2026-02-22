# Spec Template — P2-D2 ArtNet + sACN Output

**File naming:** `docs/specs/P2-D2_artnet_output.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-D2 — ArtNet + sACN Output

**Phase:** Phase 2
**Assigned To:** Worker Beta
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module handles transmitting DMX data over the network via standard lighting protocols (Art-Net and sACN/E1.31). It builds on the core DMX512 engine (P2-D1) to format DMX universes into proper UDP packets and manages continuous transmission at 44Hz (standard DMX refresh rate). It supports unicast and multicast delivery, handling network discovery where applicable.

---

## What It Does NOT Do

- It does not generate the DMX data itself (the effects engine or P2-D1 controller does this).
- It does not handle incoming DMX/ArtNet/sACN (input is a separate module).
- It does not map fixture parameters to channels.

---

## Public Interface

```python
from enum import Enum
from typing import Optional, List

class DmxProtocol(Enum):
    ARTNET = "artnet"
    SACN = "sacn"

class NetworkOutputNode:
    def __init__(self, ip_address: str, protocol: DmxProtocol = DmxProtocol.ARTNET, universe: int = 0) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def update_universe(self, data: bytearray) -> None: ...
    def get_status(self) -> dict: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `ip_address` | `str` | Destination IP address | Valid IPv4 or multicast |
| `protocol` | `DmxProtocol` | Output protocol selection | ARTNET or SACN |
| `universe` | `int` | Universe ID | 0-32767 (protocol dependent) |
| `data` | `bytearray` | 512 bytes of DMX values | Exact size 512 |

---

## Edge Cases and Error Handling

- What happens if the network interface is down? → The module attempts to rebind periodically without throwing a fatal exception (NullDevice pattern).
- What happens if `data` is < 512 bytes? → It is padded with zeros up to 512. If > 512 bytes, it is truncated.
- What happens on shutdown? → `stop()` sends a final "blackout" packet (all zeros) to cleanly turn off fixtures, then closes sockets.

---

## Dependencies

- External libraries needed:
  - `pyartnet` — used for Art-Net
  - `sacn` (sacn-python) — used for sACN (E1.31)
  - `asyncio` — for async background transmission loop

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_artnet_initialization` | Node starts successfully with ArtNet config |
| `test_sacn_initialization` | Node starts successfully with sACN config |
| `test_data_padding` | Providing <512 bytes correctly pads the payload |
| `test_network_fallback` | Initialization with invalid IP falls back safely without crashing |
| `test_clean_shutdown` | Calling stop() releases sockets |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-D2: ArtNet + sACN output` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
