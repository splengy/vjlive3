"""DMX WebSocket message handler for VJLive3.

Receives JSON commands over WebSocket and dispatches to DMXEngine.

Message format (JSON)::

    # Set a single channel
    {"cmd": "set_channel", "universe": 0, "channel": 1, "value": 200}

    # Set fixture RGB
    {"cmd": "set_rgb", "fixture": "front_wash", "r": 255, "g": 0, "b": 0}

    # Blackout all
    {"cmd": "blackout"}

    # Get fixture list
    {"cmd": "list_fixtures"}

    # Add a named effect
    {"cmd": "fx_chase", "fixtures": ["spot_1", "spot_2"], "speed": 2.0}

    # Set audio mapping
    {"cmd": "audio_map", "feature": "rms", "fixture": "wash", "mode": "dim"}

All responses are dicts (caller serialises to JSON as appropriate).
"""
from __future__ import annotations

from typing import Any

from vjlive3.dmx.engine import DMXEngine
from vjlive3.dmx.fixture import FixtureProfile
from vjlive3.dmx.fx import ChaseEffect, StrobeEffect, RainbowEffect, FadeEffect
from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)

_PROFILE_MAP: dict[str, FixtureProfile] = {
    p.value: p for p in FixtureProfile
}


class DMXWebSocketHandler:
    """Translates WebSocket JSON messages to DMXEngine calls.

    Designed to be framework-agnostic — call ``handle(msg_dict)`` from
    any WebSocket library (aiohttp, websockets, FastAPI, etc.).

    Args:
        engine: A running or idle DMXEngine instance.
    """

    def __init__(self, engine: DMXEngine) -> None:
        self._engine = engine

    def handle(self, msg: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a parsed JSON message to the DMX engine.

        Args:
            msg: Parsed message dict (``{"cmd": "...", ...}``)

        Returns:
            Response dict with at least ``{"ok": bool}``.
            On error includes ``{"ok": false, "error": "..."}``
        """
        cmd = msg.get("cmd", "")
        try:
            handler = _DISPATCH.get(cmd)
            if handler is None:
                return {"ok": False, "error": f"Unknown command: '{cmd}'"}
            return handler(self._engine, msg)
        except Exception as exc:
            logger.warning("DMX WS handler error (cmd=%s): %s", cmd, exc)
            return {"ok": False, "error": str(exc)}


# ---- Command implementations ------------------------------------------- #

def _cmd_set_channel(engine: DMXEngine, msg: dict) -> dict:
    uid     = int(msg.get("universe", 0))
    channel = int(msg["channel"])
    value   = int(msg["value"])
    u = engine.get_universe(uid)
    if u is None:
        u = engine.add_universe(uid)
    u.set(channel, value)
    return {"ok": True}


def _cmd_set_range(engine: DMXEngine, msg: dict) -> dict:
    uid   = int(msg.get("universe", 0))
    start = int(msg["start_channel"])
    values = [int(v) for v in msg["values"]]
    u = engine.get_universe(uid)
    if u is None:
        u = engine.add_universe(uid)
    u.set_range(start, values)
    return {"ok": True}


def _cmd_set_rgb(engine: DMXEngine, msg: dict) -> dict:
    name = msg["fixture"]
    fix  = engine.get_fixture(name)
    if fix is None:
        return {"ok": False, "error": f"Fixture not found: '{name}'"}
    fix.set_rgb(int(msg.get("r", 0)), int(msg.get("g", 0)), int(msg.get("b", 0)))
    return {"ok": True}


def _cmd_set_dim(engine: DMXEngine, msg: dict) -> dict:
    name = msg["fixture"]
    fix  = engine.get_fixture(name)
    if fix is None:
        return {"ok": False, "error": f"Fixture not found: '{name}'"}
    fix.set_dim(int(msg.get("value", 0)))
    return {"ok": True}


def _cmd_blackout(engine: DMXEngine, msg: dict) -> dict:
    engine.blackout_all()
    return {"ok": True}


def _cmd_list_fixtures(engine: DMXEngine, msg: dict) -> dict:
    fixtures = []
    for name in engine.list_fixtures():
        fix = engine.get_fixture(name)
        fixtures.append({
            "name":          name,
            "profile":       fix.profile.value,
            "start_channel": fix.start_channel,
            "universe":      fix.universe.universe_id,
            "channel_count": fix.channel_count,
            "values":        fix.get_values(),
        })
    return {"ok": True, "fixtures": fixtures}


def _cmd_add_fixture(engine: DMXEngine, msg: dict) -> dict:
    profile_str = str(msg.get("profile", "rgb")).lower()
    profile     = _PROFILE_MAP.get(profile_str)
    if profile is None:
        return {"ok": False, "error": f"Unknown profile: '{profile_str}'"}
    fix = engine.add_fixture(
        name          = str(msg["name"]),
        universe_id   = int(msg.get("universe", 0)),
        start_channel = int(msg["start_channel"]),
        profile       = profile,
    )
    return {"ok": True, "fixture": fix.name}


def _cmd_fx_chase(engine: DMXEngine, msg: dict) -> dict:
    fixtures = _resolve_fixtures(engine, msg.get("fixtures", []))
    colour   = tuple(msg.get("colour", [255, 255, 255]))[:3]
    effect   = ChaseEffect(fixtures, speed=float(msg.get("speed", 2.0)),
                           colour=colour)
    engine.add_effect(effect)
    return {"ok": True, "effect": "chase"}


def _cmd_fx_strobe(engine: DMXEngine, msg: dict) -> dict:
    fixtures = _resolve_fixtures(engine, msg.get("fixtures", []))
    effect   = StrobeEffect(fixtures, rate_hz=float(msg.get("rate_hz", 10.0)))
    engine.add_effect(effect)
    return {"ok": True, "effect": "strobe"}


def _cmd_fx_rainbow(engine: DMXEngine, msg: dict) -> dict:
    fixtures = _resolve_fixtures(engine, msg.get("fixtures", []))
    effect   = RainbowEffect(fixtures, speed=float(msg.get("speed", 0.2)))
    engine.add_effect(effect)
    return {"ok": True, "effect": "rainbow"}


def _cmd_fx_fade(engine: DMXEngine, msg: dict) -> dict:
    fixtures = _resolve_fixtures(engine, msg.get("fixtures", []))
    effect   = FadeEffect(
        fixtures,
        target   = int(msg.get("target", 255)),
        duration = float(msg.get("duration", 1.0)),
        start    = int(msg.get("start", 0)),
    )
    engine.add_effect(effect)
    return {"ok": True, "effect": "fade"}


def _cmd_fx_clear(engine: DMXEngine, msg: dict) -> dict:
    engine.clear_effects()
    return {"ok": True}


def _cmd_audio_map(engine: DMXEngine, msg: dict) -> dict:
    mapping_id = engine.audio_bridge.map(
        feature      = str(msg["feature"]),
        fixture_name = str(msg["fixture"]),
        mode         = str(msg.get("mode", "dim")),
        scale        = float(msg.get("scale", 255.0)),
        offset       = float(msg.get("offset", 0.0)),
    )
    return {"ok": True, "mapping_id": mapping_id}


def _cmd_audio_unmap(engine: DMXEngine, msg: dict) -> dict:
    ok = engine.audio_bridge.unmap(str(msg["mapping_id"]))
    return {"ok": ok}


def _cmd_status(engine: DMXEngine, msg: dict) -> dict:
    return {
        "ok": True,
        "universes": len(engine._universes),
        "fixtures":  len(engine._fixtures),
        "effects":   len(engine._effects),
        "running":   engine._running,
    }


def _resolve_fixtures(engine: DMXEngine, names: list[str]):
    """Resolve fixture names to Fixture objects, silently skipping unknowns."""
    return [engine.get_fixture(n) for n in names if engine.get_fixture(n)]


_DISPATCH = {
    "set_channel":  _cmd_set_channel,
    "set_range":    _cmd_set_range,
    "set_rgb":      _cmd_set_rgb,
    "set_dim":      _cmd_set_dim,
    "blackout":     _cmd_blackout,
    "list_fixtures": _cmd_list_fixtures,
    "add_fixture":  _cmd_add_fixture,
    "fx_chase":     _cmd_fx_chase,
    "fx_strobe":    _cmd_fx_strobe,
    "fx_rainbow":   _cmd_fx_rainbow,
    "fx_fade":      _cmd_fx_fade,
    "fx_clear":     _cmd_fx_clear,
    "audio_map":    _cmd_audio_map,
    "audio_unmap":  _cmd_audio_unmap,
    "status":       _cmd_status,
}
