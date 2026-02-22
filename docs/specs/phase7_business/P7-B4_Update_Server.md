# Spec: P7-B4 — Update Server (Delta Patches)

**File naming:** `docs/specs/phase7_business/P7-B4_Update_Server.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P7-B4 — Update Server

**Phase:** Phase 7 / P7-B4
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Update Server provides secure, efficient software updates for VJLive3 installations. It serves delta patches to minimize download size, verifies update integrity, and coordinates update deployment across platforms, ensuring users always have the latest version with minimal bandwidth usage.

---

## What It Does NOT Do

- Does not handle user authentication (delegates to P7-B1)
- Does not provide CDN hosting (delegates to external service)
- Does not manage plugin updates (delegates to P7-B2)
- Does not force updates (user opt-in only)

---

## Public Interface

```python
class UpdateServer:
    def __init__(self, server_url: str, api_key: str) -> None: ...
    
    def check_for_updates(self, current_version: str, platform: str, arch: str) -> UpdateInfo: ...
    def get_update_package(self, update_id: str) -> UpdatePackage: ...
    
    def calculate_delta(self, from_version: str, to_version: str, platform: str) -> DeltaInfo: ...
    def apply_delta(self, delta: DeltaInfo, target_path: str) -> bool: ...
    
    def verify_signature(self, package: UpdatePackage, signature: bytes) -> bool: ...
    def verify_checksum(self, package: UpdatePackage, checksum: str) -> bool: ...
    
    def get_channel(self) -> str: ...
    def set_channel(self, channel: str) -> None: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `server_url` | `str` | Update server URL | Valid URL |
| `api_key` | `str` | Server API key | Non-empty, secure |
| `current_version` | `str` | Current app version | Semantic version |
| `platform` | `str` | Target platform | 'windows', 'linux', 'macos' |
| `arch` | `str` | Target architecture | 'x64', 'arm64' |
| `update_id` | `str` | Update identifier | Valid ID |
| `from_version` | `str` | Source version | Valid version |
| `to_version` | `str` | Target version | Valid version |
| `delta` | `DeltaInfo` | Delta patch info | Valid delta |
| `target_path` | `str` | Installation path | Valid path |
| `package` | `UpdatePackage` | Update package | Valid package |
| `signature` | `bytes` | Digital signature | Valid signature |
| `checksum` | `str` | Expected checksum | Valid hash |
| `channel` | `str` | Update channel | 'stable', 'beta', 'dev' |

**Output:** `UpdateInfo`, `UpdatePackage`, `DeltaInfo`, `bool` — Various update operations

---

## Edge Cases and Error Handling

- What happens if no updates available? → Return None, log info
- What happens if delta patch fails? → Fallback to full package
- What happens if signature invalid? → Reject, log security event
- What happens if disk space insufficient? → Abort, show error
- What happens on cleanup? → Close connections, clear temp files

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `requests` — for HTTP downloads — fallback: raise ImportError
  - `cryptography` — for signature verification — fallback: raise ImportError
- Internal modules this depends on:
  - None (standalone service)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_update_check` | Checks for updates correctly |
| `test_package_download` | Downloads update packages |
| `test_delta_calculation` | Calculates delta patches |
| `test_delta_application` | Applies delta patches |
| `test_signature_verification` | Verifies signatures correctly |
| `test_checksum_verification` | Verifies checksums correctly |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-7] P7-B4: Update server (delta patches)` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Checkpoint

- [ ] Spec reviewed and approved
- [ ] Implementation ready to begin
- [ ] All dependencies verified
- [ ] Test plan complete
- [ ] Definition of Done clear

---

*Specification based on VJlive-2 update server module.*