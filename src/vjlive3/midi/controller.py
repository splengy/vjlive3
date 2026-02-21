"""MIDI input controller for VJLive3.

Clean port of VJlive-2's midi_controller.py with:
- mido dependency (optional — NullMIDI fallback)
- NodeGraph dot-path param integration
- MIDI Learn mode
- Callback dispatch: cc, note_on, note_off, program_change

Usage::

    from vjlive3.midi.controller import MIDIController

    ctrl = MIDIController()
    ctrl.add_cc_callback(lambda ch, cc, val: print(ch, cc, val))
    ctrl.start()          # connects to first available port
    # ...
    ctrl.stop()
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)

# Optional mido import
try:
    import mido as _mido
    _MIDO_AVAILABLE = True
except ImportError:
    _mido = None
    _MIDO_AVAILABLE = False
    logger.info("mido not installed — MIDI input running in NullMIDI mode")


class MIDIMode(str, Enum):
    NORMAL   = "normal"
    LEARNING = "learning"
    ERROR    = "error"
    RECOVERY = "recovery"


@dataclass
class MIDIMapping:
    """Maps a CC message to a NodeGraph dot-path parameter.

    Attributes:
        channel:    MIDI channel 0-15
        control:    CC number 0-127
        target:     Dot-path parameter string (e.g. "blur_1.radius")
        min_val:    Minimum output value (native units)
        max_val:    Maximum output value (native units)
    """
    channel: int
    control: int
    target:  str
    min_val: float = 0.0
    max_val: float = 1.0
    id:      str   = field(default_factory=lambda: f"m_{id(object())}")

    def __post_init__(self) -> None:
        if not 0 <= self.channel <= 15:
            raise ValueError(f"MIDI channel must be 0-15, got {self.channel}")
        if not 0 <= self.control <= 127:
            raise ValueError(f"MIDI control must be 0-127, got {self.control}")
        if not self.target.strip():
            raise ValueError("MIDI target must not be empty")
        if self.min_val >= self.max_val:
            raise ValueError(f"min_val ({self.min_val}) must be < max_val ({self.max_val})")

    def scale(self, raw_value: int) -> float:
        """Scale raw CC value (0-127) to [min_val, max_val]."""
        norm = max(0, min(127, raw_value)) / 127.0
        return self.min_val + norm * (self.max_val - self.min_val)


class MIDIController:
    """MIDI input with CC→parameter mapping and MIDI learn.

    Args:
        port_name:   MIDI port to open (auto-selects first if None)
        on_message:  Optional raw message callback (msg) → None
    """

    def __init__(
        self,
        port_name:  str | None = None,
        on_message: Callable | None = None,
    ) -> None:
        self._port_name = port_name
        self._on_message = on_message
        self._port = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()

        self.mode = MIDIMode.NORMAL
        self._mappings: list[MIDIMapping] = []
        self._param_values: dict[str, float] = {}

        # Callbacks
        self._cc_callbacks:  list[Callable] = []
        self._note_on_cbs:   list[Callable] = []
        self._note_off_cbs:  list[Callable] = []
        self._pc_callbacks:  list[Callable] = []

        # Learn mode state
        self._learn_target:   str | None = None
        self._learn_callback: Callable | None = None

        # NodeGraph integration
        self._graph_set_param: Callable | None = None

    # ------------------------------------------------------------------ #
    #  NodeGraph integration                                               #
    # ------------------------------------------------------------------ #

    def bind_graph(self, set_param_fn: Callable[[str, float], bool]) -> None:
        """Bind NodeGraph.set_param so CC messages drive graph parameters.

        Args:
            set_param_fn: Callable matching NodeGraph.set_param(path, value) signature.
        """
        self._graph_set_param = set_param_fn

    # ------------------------------------------------------------------ #
    #  Device discovery                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def list_devices() -> list[str]:
        """Return available MIDI input port names (empty if mido absent)."""
        if not _MIDO_AVAILABLE:
            return []
        try:
            return _mido.get_input_names()
        except Exception as exc:
            logger.error("MIDI list_devices error: %s", exc)
            return []

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def start(self) -> bool:
        """Connect and start listening. Returns True on success."""
        if not _MIDO_AVAILABLE:
            logger.info("MIDI: running NullMIDI (mido unavailable)")
            self._running = True
            return True

        ports = self.list_devices()
        if not ports:
            logger.warning("MIDI: no devices found")
            self.mode = MIDIMode.ERROR
            return False

        target = self._port_name or ports[0]
        try:
            with self._lock:
                self._port = _mido.open_input(target)
            self.mode = MIDIMode.NORMAL
        except Exception as exc:
            logger.error("MIDI: failed to open '%s': %s", target, exc)
            self.mode = MIDIMode.ERROR
            return False

        self._running = True
        self._thread  = threading.Thread(
            target=self._listen_loop, daemon=True, name="MIDIController"
        )
        self._thread.start()
        logger.info("MIDI: started on '%s'", target)
        return True

    def stop(self) -> None:
        """Stop listening and close the port."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        with self._lock:
            if self._port:
                try:
                    self._port.close()
                except Exception:
                    pass
                self._port = None
        logger.info("MIDI: stopped")

    def _listen_loop(self) -> None:
        while self._running:
            try:
                if self._port:
                    for msg in self._port.iter_pending():
                        self._dispatch(msg)
                time.sleep(0.001)
            except Exception as exc:
                logger.error("MIDI listen_loop error: %s", exc)
                time.sleep(0.5)

    # ------------------------------------------------------------------ #
    #  Callbacks                                                           #
    # ------------------------------------------------------------------ #

    def add_cc_callback(self, cb: Callable[[int, int, int], None]) -> None:
        """Register CC callback: cb(channel, control, value)."""
        self._cc_callbacks.append(cb)

    def add_note_on_callback(self, cb: Callable[[int, int, int], None]) -> None:
        """Register note-on callback: cb(channel, note, velocity)."""
        self._note_on_cbs.append(cb)

    def add_note_off_callback(self, cb: Callable[[int, int, int], None]) -> None:
        """Register note-off callback: cb(channel, note, velocity)."""
        self._note_off_cbs.append(cb)

    def add_program_change_callback(self, cb: Callable[[int, int], None]) -> None:
        """Register program-change callback: cb(channel, program)."""
        self._pc_callbacks.append(cb)

    # ------------------------------------------------------------------ #
    #  Mappings                                                            #
    # ------------------------------------------------------------------ #

    def add_mapping(self, mapping: MIDIMapping) -> None:
        """Register a CC → parameter mapping (replaces same channel/CC)."""
        with self._lock:
            self._mappings = [
                m for m in self._mappings
                if not (m.channel == mapping.channel and m.control == mapping.control)
            ]
            self._mappings.append(mapping)
        logger.info("MIDI mapping: ch%d cc%d → %s", mapping.channel, mapping.control, mapping.target)

    def remove_mapping(self, mapping_id: str) -> bool:
        with self._lock:
            before = len(self._mappings)
            self._mappings = [m for m in self._mappings if m.id != mapping_id]
            return len(self._mappings) < before

    def get_param_value(self, target: str) -> float:
        """Return last scaled value for a dot-path target (0.0 if unseen)."""
        return self._param_values.get(target, 0.0)

    # ------------------------------------------------------------------ #
    #  MIDI Learn                                                          #
    # ------------------------------------------------------------------ #

    def enable_learning(
        self,
        target:   str,
        callback: Callable[[MIDIMapping], None] | None = None,
    ) -> None:
        """Enter learn mode — next CC will be mapped to ``target``."""
        with self._lock:
            self._learn_target   = target
            self._learn_callback = callback
            self.mode = MIDIMode.LEARNING
        logger.info("MIDI learn: waiting for CC → '%s'", target)

    def disable_learning(self) -> None:
        with self._lock:
            self._learn_target   = None
            self._learn_callback = None
            if self.mode == MIDIMode.LEARNING:
                self.mode = MIDIMode.NORMAL

    # ------------------------------------------------------------------ #
    #  Internal dispatch                                                   #
    # ------------------------------------------------------------------ #

    def _dispatch(self, msg: Any) -> None:
        try:
            if self._on_message:
                self._on_message(msg)

            if msg.type == "control_change":
                self._handle_cc(msg)
            elif msg.type == "note_on":
                for cb in self._note_on_cbs:
                    cb(msg.channel, msg.note, msg.velocity)
            elif msg.type == "note_off":
                for cb in self._note_off_cbs:
                    cb(msg.channel, msg.note, msg.velocity)
            elif msg.type == "program_change":
                for cb in self._pc_callbacks:
                    cb(msg.channel, msg.program)
        except Exception as exc:
            logger.debug("MIDI dispatch error: %s", exc)

    def _handle_cc(self, msg: Any) -> None:
        # Learn mode: capture next CC
        with self._lock:
            if self.mode == MIDIMode.LEARNING and self._learn_target:
                mapping = MIDIMapping(
                    channel=msg.channel, control=msg.control,
                    target=self._learn_target,
                )
                learn_cb = self._learn_callback
                self.disable_learning()

        if self.mode != MIDIMode.LEARNING:
            try:
                mapping  # check if it was just created
                self.add_mapping(mapping)
                if learn_cb:
                    learn_cb(mapping)
            except UnboundLocalError:
                pass

        # Apply mappings
        with self._lock:
            mappings = list(self._mappings)

        for m in mappings:
            if m.channel == msg.channel and m.control == msg.control:
                value = m.scale(msg.value)
                self._param_values[m.target] = value
                if self._graph_set_param:
                    try:
                        self._graph_set_param(m.target, value)
                    except Exception as exc:
                        logger.debug("MIDI→graph error (%s): %s", m.target, exc)

        # Raw CC callbacks
        for cb in self._cc_callbacks:
            try:
                cb(msg.channel, msg.control, msg.value)
            except Exception as exc:
                logger.debug("CC callback error: %s", exc)

    # ------------------------------------------------------------------ #
    #  Simulation (for testing without hardware)                          #
    # ------------------------------------------------------------------ #

    def simulate_cc(self, channel: int, control: int, value: int) -> None:
        """Inject a synthetic CC message (no mido required for tests)."""
        class _FakeMsg:
            type = "control_change"
            def __init__(self, ch, cc, val):
                self.channel = ch
                self.control = cc
                self.value   = val
        self._dispatch(_FakeMsg(channel, control, value))

    def simulate_note_on(self, channel: int, note: int, velocity: int) -> None:
        class _FakeMsg:
            type = "note_on"
            def __init__(self, ch, n, v):
                self.channel = ch; self.note = n; self.velocity = v
        self._dispatch(_FakeMsg(channel, note, velocity))

    def get_status(self) -> dict:
        return {
            "mode":        self.mode.value,
            "connected":   self._port is not None,
            "mappings":    len(self._mappings),
            "mido":        _MIDO_AVAILABLE,
        }

    def __repr__(self) -> str:
        return f"<MIDIController mode={self.mode.value} mappings={len(self._mappings)}>"
