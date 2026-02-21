"""
vjlive_switchboard — MCP Agent Communication & Lock Manager

The Switchboard for VJLive3 inter-agent communication.
Enforces the Manager → Worker information flow and prevents file collisions.

Tools exposed:
  - checkout_file(file_path, agent_id, eta_mins) → bool
  - checkin_file(file_path, agent_id) → bool
  - get_locks() → list[LockEntry]
  - is_locked(file_path) → LockEntry | None
  - post_message(agent_id, message, channel) → None
  - get_messages(channel, limit) → list[Message]

Channels: general | decisions | dreamer | blockers

Run: python -m mcp_servers.vjlive_switchboard.server
"""
from __future__ import annotations

import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("vjlive3.mcp.switchboard")

_LOCKS_FILE = Path("WORKSPACE/COMMS/LOCKS.md")
_AGENT_SYNC_FILE = Path("WORKSPACE/COMMS/AGENT_SYNC.md")
_LOCK_EXPIRY_BUFFER_MINS = 15  # Auto-expire after ETA + buffer


@dataclass
class LockEntry:
    file_path: str
    agent_id: str
    checked_out: str      # ISO timestamp
    eta_mins: int
    status: str = "active"

    @property
    def is_expired(self) -> bool:
        """True if ETA + buffer has elapsed."""
        try:
            co_time = datetime.fromisoformat(self.checked_out)
            elapsed_mins = (datetime.now(tz=timezone.utc) - co_time).seconds / 60
            return elapsed_mins > (self.eta_mins + _LOCK_EXPIRY_BUFFER_MINS)
        except ValueError:
            return False


@dataclass
class Message:
    agent_id: str
    channel: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


# Channels supported by the Switchboard
CHANNELS = {"general", "decisions", "dreamer", "blockers"}


class VJLiveSwitchboard:
    """
    The Switchboard — inter-agent communication hub and file lock manager.

    Manages:
    1. File check-in/check-out to prevent agent collisions
    2. Structured message passing between agents (Manager → Worker)
    3. Auto-expiry of stale locks

    The Switchboard enforces the information flow:
    Manager (Antigravity) provides specs via 'decisions' channel.
    Workers implement — they must not post architectural decisions.
    """

    def __init__(self) -> None:
        self._active_locks: dict[str, LockEntry] = {}
        self._messages: dict[str, list[Message]] = {ch: [] for ch in CHANNELS}
        self._load_locks_from_markdown()
        _logger.info("VJLive Switchboard initialized. Agent communication hub is open.")

    # ─────────────────────────────────────────────────────────────────────────
    #  File Lock Management
    # ─────────────────────────────────────────────────────────────────────────

    def checkout_file(
        self, file_path: str, agent_id: str, eta_mins: int = 30
    ) -> bool:
        """
        Check out a file for exclusive editing.

        Args:
            file_path: Relative path to the file being locked
            agent_id: Identifying name of the agent (e.g. 'Antigravity', 'Roo')
            eta_mins: Estimated minutes until checkin (auto-expires after ETA + 15min)

        Returns:
            True if lock acquired, False if already locked by another agent.
        """
        self._expire_stale_locks()

        normalized = str(Path(file_path))
        existing = self._active_locks.get(normalized)

        if existing and existing.agent_id != agent_id:
            _logger.warning(
                "Checkout DENIED: %s already locked by %s (ETA: %d min)",
                normalized, existing.agent_id, existing.eta_mins,
            )
            return False

        lock = LockEntry(
            file_path=normalized,
            agent_id=agent_id,
            checked_out=datetime.now(tz=timezone.utc).isoformat(),
            eta_mins=eta_mins,
        )
        self._active_locks[normalized] = lock
        self._persist_locks_to_markdown()
        _logger.info("Checked out: %s → %s (ETA: %d min)", normalized, agent_id, eta_mins)
        return True

    def checkin_file(self, file_path: str, agent_id: str) -> bool:
        """
        Release a file lock.

        Args:
            file_path: Path of the file to release
            agent_id: Must match the agent who checked it out

        Returns:
            True if released, False if not locked or wrong agent.
        """
        normalized = str(Path(file_path))
        existing = self._active_locks.get(normalized)

        if existing is None:
            _logger.warning("Checkin: %s was not locked.", normalized)
            return False

        if existing.agent_id != agent_id:
            _logger.warning(
                "Checkin DENIED: %s is locked by %s, not %s",
                normalized, existing.agent_id, agent_id,
            )
            return False

        del self._active_locks[normalized]
        self._persist_locks_to_markdown()
        _logger.info("Checked in: %s ← %s", normalized, agent_id)
        return True

    def get_locks(self) -> list[LockEntry]:
        """Return all currently active (non-expired) locks."""
        self._expire_stale_locks()
        return list(self._active_locks.values())

    def is_locked(self, file_path: str) -> Optional[LockEntry]:
        """Return the LockEntry if file is locked, None otherwise."""
        self._expire_stale_locks()
        return self._active_locks.get(str(Path(file_path)))

    def _expire_stale_locks(self) -> None:
        expired = [p for p, lock in self._active_locks.items() if lock.is_expired]
        for path in expired:
            lock = self._active_locks.pop(path)
            _logger.warning(
                "Lock auto-expired for %s (was held by %s)",
                path, lock.agent_id,
            )
        if expired:
            self._persist_locks_to_markdown()

    def _persist_locks_to_markdown(self) -> None:
        """Write current lock state back to WORKSPACE/COMMS/LOCKS.md."""
        if not _LOCKS_FILE.exists():
            return
        try:
            content = _LOCKS_FILE.read_text(encoding="utf-8")
            # Replace Active Locks table
            if self._active_locks:
                rows = "\n".join(
                    f"| {lock.file_path} | {lock.agent_id} | "
                    f"{lock.checked_out[:16]} | {lock.eta_mins} | active |"
                    for lock in self._active_locks.values()
                )
                new_table = (
                    "| File Path | Agent | Checked Out | ETA (mins) | Status |\n"
                    "|-----------|-------|-------------|------------|--------|\n"
                    f"{rows}"
                )
            else:
                new_table = (
                    "| File Path | Agent | Checked Out | ETA (mins) | Status |\n"
                    "|-----------|-------|-------------|------------|--------|\n"
                    "| *(no active locks)* | — | — | — | — |"
                )

            updated = re.sub(
                r"(\| File Path.*?\| Status \|\n\|[-|]+\|\n).*?(?=\n---|\Z)",
                lambda _: new_table + "\n",
                content,
                flags=re.DOTALL,
            )
            _LOCKS_FILE.write_text(updated, encoding="utf-8")
        except OSError as e:
            _logger.warning("Could not persist locks to markdown: %s", e)

    def _load_locks_from_markdown(self) -> None:
        """Load any active locks from LOCKS.md on startup."""
        if not _LOCKS_FILE.exists():
            return
        try:
            content = _LOCKS_FILE.read_text(encoding="utf-8")
            for line in content.splitlines():
                m = re.match(
                    r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*active\s*\|$",
                    line,
                )
                if m and "no active locks" not in m.group(1).lower():
                    lock = LockEntry(
                        file_path=m.group(1).strip(),
                        agent_id=m.group(2).strip(),
                        checked_out=m.group(3).strip(),
                        eta_mins=int(m.group(4).strip()),
                    )
                    if not lock.is_expired:
                        self._active_locks[lock.file_path] = lock
        except OSError as exc:
            _logger.warning("Could not load locks from markdown: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    #  Agent Message Broker
    # ─────────────────────────────────────────────────────────────────────────

    def post_message(
        self, agent_id: str, content: str, channel: str = "general"
    ) -> None:
        """
        Post a message to an agent channel.

        Channels:
          - general:   Handoff notes, status updates
          - decisions: Architectural decisions (Manager only)
          - dreamer:   [DREAMER_LOGIC] findings and analysis
          - blockers:  Blockers requiring escalation

        Args:
            agent_id: Name of the posting agent
            content: Message content
            channel: One of the supported channel names
        """
        if channel not in CHANNELS:
            _logger.warning(
                "Unknown channel '%s'. Valid: %s", channel, CHANNELS
            )
            return

        msg = Message(agent_id=agent_id, channel=channel, content=content)
        self._messages[channel].append(msg)

        # Mirror to AGENT_SYNC.md for persistence
        if channel == "general" and _AGENT_SYNC_FILE.exists():
            try:
                existing = _AGENT_SYNC_FILE.read_text(encoding="utf-8")
                entry = (
                    f"\n### [{msg.timestamp[:16]}] — {agent_id} — Status: MESSAGE\n"
                    f"{content}\n"
                )
                # Insert after '## Session Log' heading
                updated = existing.replace(
                    "## Session Log\n", f"## Session Log\n{entry}"
                )
                _AGENT_SYNC_FILE.write_text(updated, encoding="utf-8")
            except OSError as exc:
                _logger.warning("Could not mirror message to AGENT_SYNC.md: %s", exc)

        _logger.info("[%s] %s: %s", channel.upper(), agent_id, content[:80])

    def get_messages(
        self, channel: str = "general", limit: int = 20
    ) -> list[Message]:
        """
        Retrieve recent messages from a channel.

        Args:
            channel: Channel to read from
            limit: Maximum number of messages to return (most recent first)

        Returns:
            List of Message objects, newest first.
        """
        if channel not in CHANNELS:
            return []
        msgs = self._messages.get(channel, [])
        return list(reversed(msgs[-limit:]))

    # ─────────────────────────────────────────────────────────────────────────
    #  Smoke test
    # ─────────────────────────────────────────────────────────────────────────

    def smoke_test(self) -> bool:
        """Verify checkout/checkin round-trip and message posting."""
        ok1 = self.checkout_file("test/smoke.py", "SmokeTest", eta_mins=1)
        assert ok1, "checkout failed"
        assert self.is_locked("test/smoke.py") is not None
        # Second checkout by same agent is allowed
        ok2 = self.checkout_file("test/smoke.py", "SmokeTest", eta_mins=1)
        assert ok2, "self-re-checkout failed"
        # Different agent cannot steal it
        ok3 = self.checkout_file("test/smoke.py", "OtherAgent", eta_mins=1)
        assert not ok3, "cross-agent checkout should be denied"
        ok4 = self.checkin_file("test/smoke.py", "SmokeTest")
        assert ok4, "checkin failed"
        assert self.is_locked("test/smoke.py") is None

        self.post_message("SmokeTest", "Hello from smoke test", channel="general")
        msgs = self.get_messages("general", limit=1)
        assert msgs and msgs[0].content == "Hello from smoke test"

        # Clean up test message
        self._messages["general"] = [
            m for m in self._messages["general"]
            if m.agent_id != "SmokeTest"
        ]
        _logger.info("Switchboard smoke test: PASS")
        return True


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    switchboard = VJLiveSwitchboard()

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = switchboard.smoke_test()
        sys.exit(0 if ok else 1)

    locks = switchboard.get_locks()
    _logger.info("Switchboard ready. Active locks: %d", len(locks))
    print("VJLive Switchboard ready. Import VJLiveSwitchboard for direct use.")
    print(f"Active locks on startup: {len(locks)}")
    for lock in locks:
        print(f"  {lock.file_path} → {lock.agent_id} (ETA: {lock.eta_mins} min)")


if __name__ == "__main__":
    main()
