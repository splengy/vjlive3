#!/usr/bin/env python3
"""Standalone switchboard smoke test — safe to run from any directory."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import mcp_servers.vjlive_switchboard.server as _sw_mod

_sw_mod._LOCKS_FILE = REPO / "WORKSPACE" / "COMMS" / "LOCKS.md"
_sw_mod._AGENT_SYNC_FILE = REPO / "WORKSPACE" / "COMMS" / "AGENT_SYNC.md"

from mcp_servers.vjlive_switchboard.server import VJLiveSwitchboard

print(f"[switchboard smoke-test] repo={REPO}")
board = VJLiveSwitchboard()
print("  ✓ Switchboard initialized")

ok = board.checkout_file("test/smoke.py", "SmokeTest", eta_mins=1)
assert ok, "checkout failed"
print("  ✓ checkout_file works")

lock = board.is_locked("test/smoke.py")
assert lock is not None
print("  ✓ is_locked works")

denied = board.checkout_file("test/smoke.py", "OtherAgent", eta_mins=1)
assert not denied, "cross-agent checkout should be denied"
print("  ✓ cross-agent lock protection works")

ok2 = board.checkin_file("test/smoke.py", "SmokeTest")
assert ok2, "checkin failed"
print("  ✓ checkin_file works")

board.post_message("SmokeTest", "Phase 0 gate check", channel="general")
msgs = board.get_messages("general", limit=1)
assert msgs and msgs[0].content == "Phase 0 gate check"
print("  ✓ post_message / get_messages works")

locks = board.get_locks()
print(f"  ✓ get_locks works ({len(locks)} active)")

print("\n  ✅ vjlive-switchboard smoke test: PASS")
