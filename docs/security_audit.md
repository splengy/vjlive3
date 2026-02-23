# VJLive3 Security Audit Report

> **Date**: 2026-02-23 | **Status**: PASSED — 0 P0 vulnerabilities

## Scope

Modules audited: `src/vjlive3/agents/`, `src/vjlive3/ui/`, `src/vjlive3/plugins/api.py`

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| P0 (Critical) | 0 | — |
| P1 (High) | 1 | ✅ Fixed |
| P2 (Medium) | 1 | ✅ Fixed |
| P3 (Low) | 1 | ✅ Fixed |
| Informational | 2 | Accepted |

---

## Findings

### ✅ FIXED — P1: Unbounded POST body in `web_remote.py`

**Risk**: An attacker on the LAN could send a request with a large `Content-Length` to exhaust memory.

**Fix** (`web_remote.py:75`):
```python
_MAX_BODY = 65536
length = min(int(self.headers.get("Content-Length", 0)), _MAX_BODY)
```

---

### ✅ FIXED — P2: Non-finite float acceptance in `web_remote.py`

**Risk**: `float("inf")` or `float("nan")` from a POST body could propagate to shader uniforms, causing undefined GL behaviour.

**Fix** (`web_remote.py:84`):
```python
import math
if not math.isfinite(fval):
    self.send_error(400, f"Non-finite value rejected for '{param}'")
    return
```

---

### ✅ FIXED — P3: Plugin path not sanitized in `web_remote.py`

**Risk**: `POST /api/params/../../../tmp/evil` could pass a traversal string as plugin name to `ParamStore.set()`. Since `ParamStore` is an in-memory dict (no filesystem access), actual exploit impact is nil, but defence-in-depth requires sanitization.

**Fix** (`web_remote.py:73`):
```python
plugin = plugin.replace("..", "").replace("/", "").replace("\\", "")
```

---

### ℹ️ ACCEPTED — No authentication on web remote

**Risk**: The web remote has no token/key. Any device on the local network can control parameters.

**Rationale**: VJLive3 is a live performance tool, typically run airgapped or on a trusted LAN. Authentication would add friction without meaningful security benefit in this use case. **Production deployments should add nginx basic-auth or run on localhost only.**

---

### ℹ️ ACCEPTED — CORS `Access-Control-Allow-Origin: *`

**Risk**: Cross-site requests can read API responses.

**Rationale**: The API returns only publicly visible parameter state (no secrets). `*` is standard for local control interfaces. No credentials are involved.

---

## DangerousCall Audit

| Pattern | Files scanned | Found |
|---------|--------------|-------|
| `eval()` | agents/, ui/ | ❌ None |
| `exec()` | agents/, ui/ | ❌ None |
| `pickle` | agents/, ui/ | ❌ None |
| `subprocess` | agents/, ui/ | ❌ None |
| `shell=True` | agents/, ui/ | ❌ None |
| `os.system` | agents/, ui/ | ❌ None |
| `__import__` | agents/, ui/ | ❌ None |

**All clear.**

---

## Dependencies

VJLive3 core uses only stdlib + NumPy. No third-party web framework or authentication library. No known CVEs in NumPy at this version.
