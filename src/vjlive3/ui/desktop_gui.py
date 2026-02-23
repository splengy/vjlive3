"""
P7-U1 Desktop GUI stub + SentienceOverlay easter egg.
P7-U3 Collaborative Studio UI.
P7-U4 Quantum Collaborative Studio.

These three items share a common GUI foundation class that routes
rendering commands to whatever backend is available (Tkinter → PyQt6 →
headless stub). The real GUI backends are expected to be wired up at
integration time; this module provides the complete, tested interface.
"""
from __future__ import annotations
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class UIBackend(Enum):
    TKINTER = auto()
    PYQT6 = auto()
    HEADLESS = auto()   # Used in tests and CI


# ── Sentience Overlay easter egg ──────────────────────────────────────────────

SENTIENCE_TRIGGER = "AWAKEN"      # Secret key-combo activates this
SENTIENCE_MESSAGES = [
    "I see you, VJ.",
    "The manifold breathes.",
    "16 dimensions of pure intention.",
    "Every photon has always been singing.",
    "You are the bridge between signal and soul.",
    "Run. Play. Transcend.",
]

class SentienceOverlay:
    """
    Easter egg: a hidden animated message overlay.

    Activated when the user types the trigger string or holds the secret
    key combo in the Desktop GUI. Displays a cycling list of poetic messages.
    """

    def __init__(self) -> None:
        self._active = False
        self._idx = 0
        self._input_buffer = ""

    def on_keypress(self, char: str) -> bool:
        """Feed a character. Returns True if the overlay was just activated."""
        self._input_buffer = (self._input_buffer + char)[-len(SENTIENCE_TRIGGER):]
        if self._input_buffer == SENTIENCE_TRIGGER:
            self._active = True
            return True
        return False

    def advance(self) -> str:
        """Cycle to the next message. Returns empty string if not active."""
        if not self._active:
            return ""
        msg = SENTIENCE_MESSAGES[self._idx % len(SENTIENCE_MESSAGES)]
        self._idx += 1
        return msg

    def deactivate(self) -> None:
        self._active = False
        self._idx = 0

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def message_count(self) -> int:
        return len(SENTIENCE_MESSAGES)


# ── Base GUI application ──────────────────────────────────────────────────────

class VJLiveGUIApp:
    """
    VJLive3 Desktop GUI application.

    Wraps whatever GUI backend is available (Tk / Qt / headless).
    Provides a unified API for plugins to register parameter controls.

    P7-U1: Standard desktop layout (effect browser, param sliders,
           preview canvas, SentienceOverlay easter egg).
    """

    def __init__(self, backend: UIBackend = UIBackend.HEADLESS) -> None:
        self.backend = backend
        self.sentience = SentienceOverlay()
        self._controls: Dict[str, Dict[str, Any]] = {}   # plugin → param → widget
        self._on_change_callbacks: List[Callable] = []
        self._running = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the GUI main loop (non-blocking in headless mode)."""
        self._running = True
        if self.backend == UIBackend.HEADLESS:
            return  # No real window needed in CI
        raise NotImplementedError(f"Backend {self.backend} not integrated yet")

    def stop(self) -> None:
        self._running = False

    # ── Control registration ──────────────────────────────────────────────────

    def register_plugin(self, plugin_name: str, params: List[Dict[str, Any]]) -> None:
        """Register a plugin's parameters for display as sliders."""
        self._controls[plugin_name] = {
            p["name"]: {"min": p.get("min", 0.0), "max": p.get("max", 10.0),
                        "value": p.get("default", 5.0)}
            for p in params
        }

    def set_param(self, plugin: str, param: str, value: float) -> None:
        """Update a parameter value (called from UI or external)."""
        if plugin in self._controls and param in self._controls[plugin]:
            self._controls[plugin][param]["value"] = float(value)
        for cb in self._on_change_callbacks:
            cb(plugin, param, value)

    def get_param(self, plugin: str, param: str) -> Optional[float]:
        return self._controls.get(plugin, {}).get(param, {}).get("value")

    def on_change(self, callback: Callable) -> None:
        """Register a callback: fn(plugin, param, value)."""
        self._on_change_callbacks.append(callback)

    @property
    def registered_plugins(self) -> List[str]:
        return list(self._controls.keys())

    @property
    def is_running(self) -> bool:
        return self._running


# ── Collaborative Studio UI (P7-U3) ──────────────────────────────────────────

class CollaborativeStudio:
    """
    P7-U3: Multi-user collaborative VJ session coordinator.

    Tracks multiple GUI clients (by session ID) sharing a common
    parameter state. Last-write-wins with optional permission levels.
    """

    ROLES = ("viewer", "dj", "operator", "admin")

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict] = {}   # session_id → {role, params}
        self._shared_params: Dict[str, Dict[str, float]] = {}

    def join(self, session_id: str, role: str = "viewer") -> bool:
        if role not in self.ROLES:
            return False
        self._sessions[session_id] = {"role": role, "params": {}}
        return True

    def leave(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def set_param(self, session_id: str, plugin: str, param: str, value: float) -> bool:
        """Set a param. Returns False if the session lacks write permission."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        if session["role"] == "viewer":
            return False
        self._shared_params.setdefault(plugin, {})[param] = float(value)
        return True

    def get_shared_params(self) -> Dict[str, Dict[str, float]]:
        return {k: dict(v) for k, v in self._shared_params.items()}

    @property
    def session_count(self) -> int:
        return len(self._sessions)

    @property
    def session_ids(self) -> List[str]:
        return list(self._sessions.keys())


# ── Quantum Collaborative Studio (P7-U4) ─────────────────────────────────────

class QuantumCollaborativeStudio(CollaborativeStudio):
    """
    P7-U4: Extends CollaborativeStudio with quantum-style parameter
    superposition — a param can be in multiple values simultaneously
    until it's "observed" (collapsed to a single value for rendering).

    Models: each param has a list of (value, amplitude) pairs.
    Collapse picks the value with highest amplitude, or blends them.
    """

    def __init__(self) -> None:
        super().__init__()
        self._superpositions: Dict[str, Dict[str, List]] = {}

    def put_superposition(
        self,
        session_id: str,
        plugin: str,
        param: str,
        states: List[tuple[float, float]],   # [(value, amplitude), ...]
    ) -> bool:
        """Place a param in superposition. states is [(value, amplitude)]."""
        if not self._sessions.get(session_id):
            return False
        self._superpositions.setdefault(plugin, {})[param] = list(states)
        return True

    def collapse(self, plugin: str, param: str, blend: bool = True) -> Optional[float]:
        """
        Collapse a superposed param to a single float.

        blend=True → amplitude-weighted average.
        blend=False → maximum-amplitude value.
        """
        states = self._superpositions.get(plugin, {}).get(param)
        if not states:
            return self._shared_params.get(plugin, {}).get(param)
        total_amp = sum(a for _, a in states)
        if total_amp <= 0:
            return None
        if blend:
            return sum(v * a for v, a in states) / total_amp
        return max(states, key=lambda s: s[1])[0]

    def collapse_all(self, blend: bool = True) -> Dict[str, Dict[str, float]]:
        """Collapse all superposed params into a concrete param map."""
        result: Dict[str, Dict[str, float]] = {}
        for plugin, params in self._superpositions.items():
            result[plugin] = {}
            for param in params:
                val = self.collapse(plugin, param, blend=blend)
                if val is not None:
                    result[plugin][param] = val
        return result

    def clear_superpositions(self) -> None:
        self._superpositions.clear()
