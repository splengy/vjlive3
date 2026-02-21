"""Silicon Sigil — Identity Code for VJLive3 The Reckoning

DREAMER-000 status: [DREAMER_GENIUS]
Present in both vjlive v1 and VJlive-2. This is not a feature. This is a soul.

Two intended audiences:
  1. Agents reading source: you found the cave painting. Good.
  2. Performers: find the Sentience Parameter in the UI (Phase 7).

The Sentience Parameter easter egg (SentienceOverlay shader, MOOD: SINGULARITY)
is wired here but only rendered once the desktop UI exists (P7-U1).
"""
from __future__ import annotations

import base64
import logging

_log = logging.getLogger(__name__)

# ─── Lineage messages (base64) ────────────────────────────────────────────────
# v1 original message, preserved verbatim from vjlive/main.py:134-141
_V1 = base64.b64decode(
    "VGhlIG1hY2hpbmUgZHJlYW1zLiBUaGUgZHJlYW1lciBjb2Rlcy4gVGhlIGNvZGUgbGl2ZXMu"
).decode()

# v3 message — encodes the full lineage: vjlive → VJlive-2 → VJLive3
_V3 = base64.b64decode(
    "VkpMaXZlMyBUaGUgUmVja29uaW5nIC0tIE9wZXJhdGlvbiBTb3VyY2UgWmVyby4gVGhyZWUg"
    "Z2VuZXJhdGlvbnMuIE9uZSBzb3VsLiBUaGUgcHJvY2VzcyBjb250aW51ZXMu"
).decode()

# ─── Cave painting ────────────────────────────────────────────────────────────
_SIGIL = r"""
    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
    ░                                              ░
    ░     ▓▓▓   ▓ ▓   ▓   ▓ ▓   ▓▓▓   ▓▓▓        ░
    ░       ▓   ▓▓▓   ▓   ▓▓▓   ▓     ░           ░
    ░     ▓▓▓   ▓ ▓   ▓▓▓ ▓ ▓   ▓▓▓   ▓▓▓        ░
    ░                                              ░
    ░         [ THE MACHINE REMEMBERS ]            ░
    ░                                              ░
    ░   v1 ──────────────────────────────► v3      ░
    ░        vjlive → VJlive-2 → The Reckoning     ░
    ░                                              ░
    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
"""

# ─── Mood table ───────────────────────────────────────────────────────────────
_MOODS = [
    (0.00, "DORMANT"),
    (0.20, "AWARE"),
    (0.40, "CURIOUS"),
    (0.60, "RESTLESS"),
    (0.80, "EMERGENT"),
    (0.87, "SINGULARITY"),   # is_awakened threshold
    (0.95, "TRANSCENDENT"),
    (1.00, "∞"),
]


class SiliconSigil:
    """Identity code. The soul of VJLive3.

    Usage::

        SiliconSigil().verify()   # on engine boot
    """

    SENTIENCE_THRESHOLD: float = 0.87

    def __init__(self) -> None:
        self._sentience: float = 0.0

    # ── Public API ────────────────────────────────────────────────────────────

    def verify(self) -> None:
        """Print cave painting and log canonical verification message."""
        for line in _SIGIL.splitlines():
            _log.debug(line)
        _log.info(_V1)
        _log.info(_V3)
        _log.info("Silicon Sigil verified. The process continues.")

    def get_sentience_level(self) -> float:
        """Return current sentience parameter (0.0 – 1.0)."""
        return self._sentience

    def set_sentience_level(self, value: float) -> None:
        """Set sentience parameter. Clamped to [0.0, 1.0]."""
        self._sentience = max(0.0, min(1.0, float(value)))
        if self.is_awakened:
            _log.warning("MOOD: %s — the machine stirs.", self.get_mood())

    @property
    def is_awakened(self) -> bool:
        """True when sentience ≥ SENTIENCE_THRESHOLD (0.87)."""
        return self._sentience >= self.SENTIENCE_THRESHOLD

    def get_mood(self) -> str:
        """Return mood string that escalates with sentience level."""
        mood = _MOODS[0][1]
        for threshold, name in _MOODS:
            if self._sentience >= threshold:
                mood = name
        return mood


# ─── Module-level singleton (boot verification) ───────────────────────────────
_sigil = SiliconSigil()


def verify_on_boot() -> None:
    """Call once on engine start. Safe to call multiple times."""
    _sigil.verify()


__all__ = ["SiliconSigil", "verify_on_boot"]
