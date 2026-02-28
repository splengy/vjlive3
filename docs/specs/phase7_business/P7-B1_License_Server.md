# Spec: P7-B1 — License Server (JWT + RBAC)

**File naming:** `docs/specs/phase7_business/P7-B1_License_Server.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P7-B1 — License Server

**Phase:** Phase 7 / P7-B1
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

License Server provides centralized license management for VJLive3 plugins and features. It uses JWT tokens for authentication and RBAC (Role-Based Access Control) for permission management, enabling secure license distribution, validation, and usage tracking across multiple installations.

---

## What It Does NOT Do

- Does not handle payment processing (delegates to external payment provider)
- Does not provide user interface for license management (delegates to P7-U2)
- Does not include offline license activation (online-only)
- Does not manage plugin marketplace (delegates to P7-B2)

---

## Public Interface

```python
class LicenseServer:
    def __init__(self, secret_key: str, db_path: str = "licenses.db") -> None: ...
    
    def issue_license(self, user_id: str, plugin_id: str, license_type: str, expires_at: datetime) -> License: ...
    def validate_license(self, license_token: str, plugin_id: str) -> ValidationResult: ...
    def revoke_license(self, license_token: str) -> bool: ...
    
    def get_user_licenses(self, user_id: str) -> List[License]: ...
    def get_plugin_licenses(self, plugin_id: str) -> List[License]: ...
    
    def create_role(self, role_name: str, permissions: List[str]) -> str: ...
    def assign_role(self, user_id: str, role_id: str) -> None: ...
    def check_permission(self, user_id: str, permission: str) -> bool: ...
    
    def generate_jwt(self, user_id: str, payload: Dict) -> str: ...
    def verify_jwt(self, token: str) -> Dict: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `secret_key` | `str` | JWT signing secret | Non-empty, secure |
| `db_path` | `str` | Database file path | Valid path |
| `user_id` | `str` | Unique user identifier | Non-empty |
| `plugin_id` | `str` | Plugin identifier | Valid plugin |
| `license_type` | `str` | License type | 'trial', 'standard', 'pro', 'enterprise' |
| `expires_at` | `datetime` | Expiration date | Future date |
| `license_token` | `str` | JWT license token | Valid JWT |
| `role_name` | `str` | Role name | Non-empty |
| `permissions` | `List[str]` | Permission strings | Valid permissions |
| `role_id` | `str` | Role identifier | Non-empty |
| `payload` | `Dict` | JWT payload | Valid dict |

**Output:** `License`, `ValidationResult`, `bool`, `List[License]`, `str`, `Dict` — Various license and auth results

---

## Edge Cases and Error Handling

- What happens if JWT signature invalid? → Reject, log security event
- What happens if license expired? → Reject, offer renewal
- What happens if user has no permission? → Deny access, log attempt
- What happens if database corrupted? → Attempt recovery, fallback to read-only
- What happens on cleanup? → Close DB connections, clear caches

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `pyjwt` — for JWT tokens — fallback: raise ImportError
  - `sqlite3` or `sqlalchemy` — for license database — fallback: raise ImportError
- Internal modules this depends on:
  - None (standalone service)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_license_issuance` | Issues licenses correctly |
| `test_license_validation` | Validates licenses correctly |
| `test_license_revocation` | Revokes licenses correctly |
| `test_jwt_generation` | Generates valid JWTs |
| `test_jwt_verification` | Verifies JWTs correctly |
| `test_rbac_permissions` | Role-based access control works |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-7] P7-B1: License server (JWT + RBAC)` message
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

*Specification based on VJlive-2 license server architecture.*