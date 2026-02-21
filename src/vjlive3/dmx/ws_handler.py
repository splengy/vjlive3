"""WebSocket command handler for DMX control.

Provides a simple synchronous interface for handling DMX commands.
Used by both the WebSocket server and direct API calls.
"""

from typing import Dict, Any, List, Optional
from vjlive3.dmx.engine import DMXEngine
from vjlive3.dmx.fixture import FixtureProfile


class DMXWebSocketHandler:
    """Handles DMX commands via a simple request/response interface."""

    def __init__(self, engine: DMXEngine):
        self.engine = engine
        self._audio_mappings: Dict[int, Dict[str, Any]] = {}
        self._next_mapping_id = 0

    def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a DMX command.

        Args:
            request: Command dictionary with 'cmd' key and parameters

        Returns:
            Response dictionary with 'ok' (bool) and optional 'error' or data
        """
        cmd = request.get("cmd")

        if not cmd:
            return {"ok": False, "error": "Missing 'cmd' field"}

        handlers = {
            "set_channel":   self._cmd_set_channel,
            "set_range":     self._cmd_set_range,
            "set_rgb":       self._cmd_set_rgb,
            "set_dim":       self._cmd_set_dim,
            "blackout":      self._cmd_blackout,
            "list_fixtures": self._cmd_list_fixtures,
            "add_fixture":   self._cmd_add_fixture,
            "fx_chase":      self._cmd_fx_chase,
            "fx_strobe":     self._cmd_fx_strobe,
            "fx_rainbow":    self._cmd_fx_rainbow,
            "fx_fade":       self._cmd_fx_fade,
            "fx_clear":      self._cmd_fx_clear,
            "audio_map":     self._cmd_audio_map,
            "audio_unmap":   self._cmd_audio_unmap,
            "status":        self._cmd_status,
        }

        handler = handlers.get(cmd)
        if not handler:
            return {"ok": False, "error": f"Unknown command: {cmd}"}

        try:
            result = handler(request)
            return {"ok": True, **(result or {})}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ---- Command handlers ------------------------------------------------- #

    def _cmd_set_channel(self, req: Dict[str, Any]) -> Dict[str, Any]:
        universe_id = req.get("universe")
        channel     = req.get("channel")
        value       = req.get("value")
        if universe_id is None or channel is None or value is None:
            raise ValueError("Missing required fields: universe, channel, value")
        if universe_id not in self.engine._universes:
            self.engine.add_universe(universe_id)
        u = self.engine.get_universe(universe_id)
        u.set(channel, int(value))
        return {}

    def _cmd_set_range(self, req: Dict[str, Any]) -> Dict[str, Any]:
        universe_id   = req.get("universe")
        start_channel = req.get("start_channel")
        values        = req.get("values", [])
        if universe_id is None or start_channel is None:
            raise ValueError("Missing required fields: universe, start_channel")
        if universe_id not in self.engine._universes:
            self.engine.add_universe(universe_id)
        u = self.engine.get_universe(universe_id)
        u.set_range(start_channel, [int(v) for v in values])
        return {}

    def _cmd_set_rgb(self, req: Dict[str, Any]) -> Dict[str, Any]:
        name = req.get("fixture")
        r, g, b = req.get("r"), req.get("g"), req.get("b")
        if not name or r is None or g is None or b is None:
            raise ValueError("Missing required fields: fixture, r, g, b")
        fix = self.engine.get_fixture(name)
        if not fix:
            raise ValueError(f"Fixture '{name}' not found")
        fix.set_rgb(int(r), int(g), int(b))
        return {}

    def _cmd_set_dim(self, req: Dict[str, Any]) -> Dict[str, Any]:
        name  = req.get("fixture")
        value = req.get("value")
        if not name or value is None:
            raise ValueError("Missing required fields: fixture, value")
        fix = self.engine.get_fixture(name)
        if not fix:
            raise ValueError(f"Fixture '{name}' not found")
        fix.set_dim(int(value))
        return {}

    def _cmd_blackout(self, req: Dict[str, Any]) -> Dict[str, Any]:
        self.engine.blackout_all()
        return {}

    def _cmd_list_fixtures(self, req: Dict[str, Any]) -> Dict[str, Any]:
        fixtures = []
        for name, fix in self.engine._fixtures.items():
            fixtures.append({
                "name":          name,
                "profile":       fix.profile.value,
                "start_channel": fix.start_channel,
                "universe_id":   fix.universe.universe_id,
                "channel_count": fix.channel_count,
                "values":        fix.get_values(),
            })
        return {"fixtures": fixtures}

    def _cmd_add_fixture(self, req: Dict[str, Any]) -> Dict[str, Any]:
        name          = req.get("name")
        start_channel = req.get("start_channel")
        profile_str   = req.get("profile")
        universe      = req.get("universe", 0)
        if not name or start_channel is None or not profile_str:
            raise ValueError("Missing required fields: name, start_channel, profile")
        try:
            profile_enum = FixtureProfile(profile_str)
        except ValueError:
            raise ValueError(f"Invalid profile: {profile_str}. Valid: {[p.value for p in FixtureProfile]}")
        self.engine.add_fixture(name, universe, start_channel, profile_enum)
        return {}

    def _cmd_fx_chase(self, req: Dict[str, Any]) -> Dict[str, Any]:
        from vjlive3.dmx.fx import ChaseEffect
        fixtures = self._resolve(req.get("fixtures", []))
        if not fixtures:
            raise ValueError("No valid fixtures specified")
        effect = ChaseEffect(fixtures, speed=float(req.get("speed", 1.0)),
                             colour=tuple(req.get("colour", [255, 255, 255]))[:3])
        self.engine.add_effect(effect)
        return {"effect_id": id(effect)}

    def _cmd_fx_strobe(self, req: Dict[str, Any]) -> Dict[str, Any]:
        from vjlive3.dmx.fx import StrobeEffect
        fixtures = self._resolve(req.get("fixtures", []))
        if not fixtures:
            raise ValueError("No valid fixtures specified")
        effect = StrobeEffect(fixtures, rate_hz=float(req.get("rate_hz", 10.0)))
        self.engine.add_effect(effect)
        return {"effect_id": id(effect)}

    def _cmd_fx_rainbow(self, req: Dict[str, Any]) -> Dict[str, Any]:
        from vjlive3.dmx.fx import RainbowEffect
        fixtures = self._resolve(req.get("fixtures", []))
        if not fixtures:
            raise ValueError("No valid fixtures specified")
        effect = RainbowEffect(fixtures, speed=float(req.get("speed", 1.0)))
        self.engine.add_effect(effect)
        return {"effect_id": id(effect)}

    def _cmd_fx_fade(self, req: Dict[str, Any]) -> Dict[str, Any]:
        from vjlive3.dmx.fx import FadeEffect
        fixtures = self._resolve(req.get("fixtures", []))
        target   = req.get("target")
        if target is None:
            raise ValueError("Missing required field: target")
        if not fixtures:
            raise ValueError("No valid fixtures specified")
        effect = FadeEffect(fixtures, int(target),
                            float(req.get("duration", 1.0)),
                            int(req.get("start", 0)))
        self.engine.add_effect(effect)
        return {"effect_id": id(effect)}

    def _cmd_fx_clear(self, req: Dict[str, Any]) -> Dict[str, Any]:
        self.engine.clear_effects()
        return {}

    def _cmd_audio_map(self, req: Dict[str, Any]) -> Dict[str, Any]:
        feature      = req.get("feature")
        fixture_name = req.get("fixture")
        mode         = req.get("mode", "dim")
        scale        = float(req.get("scale", 255.0))
        offset       = float(req.get("offset", 0.0))
        if not feature or not fixture_name:
            raise ValueError("Missing required fields: feature, fixture")
        # Validate via bridge (raises ValueError on unknown feature/mode)
        mapping_id_str = self.engine.audio_bridge.map(
            feature, fixture_name, mode=mode, scale=scale, offset=offset
        )
        # Also track with integer ID for WS clients
        int_id = self._next_mapping_id
        self._next_mapping_id += 1
        self._audio_mappings[int_id] = {
            "feature": feature, "fixture": fixture_name,
            "mode": mode, "bridge_id": mapping_id_str,
        }
        return {"mapping_id": int_id}

    def _cmd_audio_unmap(self, req: Dict[str, Any]) -> Dict[str, Any]:
        mapping_id = req.get("mapping_id")
        if mapping_id is None:
            raise ValueError("Missing required field: mapping_id")
        entry = self._audio_mappings.pop(mapping_id, None)
        if entry is None:
            raise ValueError(f"Mapping ID {mapping_id} not found")
        self.engine.audio_bridge.unmap(entry["bridge_id"])
        return {}

    def _cmd_status(self, req: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "fixtures":       len(self.engine._fixtures),
            "universes":      len(self.engine._universes),
            "effects":        len(self.engine._effects),
            "audio_mappings": len(self._audio_mappings),
            "running":        self.engine._running,
        }

    def _resolve(self, names: list) -> list:
        return [f for f in (self.engine.get_fixture(n) for n in names) if f]