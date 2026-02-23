"""
P7-U6: VJLive3 CLI automation.

Provides a command-line interface to control VJLive3 without a GUI:
  - List plugins
  - Set parameters
  - Start/stop the render loop
  - Query agent state
  - Export OSC layout
  - Run batch preset sequences

Usage
-----
    python -m vjlive3.ui.cli --help
    python -m vjlive3.ui.cli list-plugins
    python -m vjlive3.ui.cli set-param bloom_effect intensity 7.0
    python -m vjlive3.ui.cli agent-status
    python -m vjlive3.ui.cli export-osc --output layout.json
"""
from __future__ import annotations
import argparse
import json
import sys
from typing import Dict, Any, List, Optional


# ── Parameter store (simple in-process store for headless operation) ──────────

class ParamStore:
    """
    Lightweight in-memory parameter store for CLI-driven sessions.

    Maps (plugin_name, param_name) → float value.
    Persisted to / loaded from JSON.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, float]] = {}

    def set(self, plugin: str, param: str, value: float) -> None:
        self._store.setdefault(plugin, {})[param] = float(value)

    def get(self, plugin: str, param: str, default: float = 5.0) -> float:
        return self._store.get(plugin, {}).get(param, default)

    def get_all(self, plugin: str) -> Dict[str, float]:
        return dict(self._store.get(plugin, {}))

    def all_params(self) -> Dict[str, Dict[str, float]]:
        return {k: dict(v) for k, v in self._store.items()}

    def load_json(self, path: str) -> None:
        with open(path) as f:
            data = json.load(f)
        for plugin, params in data.items():
            for param, value in params.items():
                self.set(plugin, param, value)

    def save_json(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.all_params(), f, indent=2)

    def reset_plugin(self, plugin: str) -> None:
        self._store.pop(plugin, None)

    def reset_all(self) -> None:
        self._store.clear()


# ── OSC layout export ─────────────────────────────────────────────────────────

class OSCLayoutExporter:
    """
    Exports VJLive3 plugin parameters as a TouchOSC / OSC address map.

    Output JSON format:
    {
      "layout": [
        {"address": "/vjlive3/bloom_effect/intensity", "type": "f", "min": 0, "max": 10, "default": 5}
      ]
    }
    """

    OSC_BASE = "/vjlive3"

    @classmethod
    def export(cls, plugin_params: Dict[str, List[Dict[str, Any]]], path: Optional[str] = None) -> Dict:
        """
        Build and optionally write an OSC address layout.

        *plugin_params* maps plugin_name → list of param dicts
        (each with keys: name, default, min, max).
        """
        layout = []
        for plugin_name, params in sorted(plugin_params.items()):
            for p in params:
                entry = {
                    "address": f"{cls.OSC_BASE}/{plugin_name}/{p['name']}",
                    "type": "f",
                    "min": float(p.get("min", 0.0)),
                    "max": float(p.get("max", 10.0)),
                    "default": float(p.get("default", 5.0)),
                    "label": p.get("name", "").replace("_", " ").title(),
                    "plugin": plugin_name,
                }
                layout.append(entry)

        result = {"layout": layout, "count": len(layout), "base": cls.OSC_BASE}
        if path:
            with open(path, "w") as f:
                json.dump(result, f, indent=2)
        return result

    @classmethod
    def address(cls, plugin: str, param: str) -> str:
        return f"{cls.OSC_BASE}/{plugin}/{param}"

    @classmethod
    def parse_address(cls, address: str) -> Optional[tuple[str, str]]:
        """Parse /vjlive3/<plugin>/<param> → (plugin, param). Returns None on mismatch."""
        prefix = cls.OSC_BASE + "/"
        if not address.startswith(prefix):
            return None
        rest = address[len(prefix):]
        parts = rest.split("/", 1)
        if len(parts) != 2:
            return None
        return parts[0], parts[1]


# ── Preset sequencer ──────────────────────────────────────────────────────────

class PresetSequencer:
    """
    Plays back a list of preset states with optional timing info.

    Each preset is:
        {"plugin": "bloom_effect", "params": {"intensity": 7.0, "mix": 8.0}, "duration": 4.0}
    """

    def __init__(self, store: ParamStore) -> None:
        self._store = store
        self._sequence: List[Dict[str, Any]] = []
        self._current_idx: int = 0

    def load(self, presets: List[Dict[str, Any]]) -> None:
        self._sequence = list(presets)
        self._current_idx = 0

    def load_json(self, path: str) -> None:
        with open(path) as f:
            self.load(json.load(f))

    def step(self) -> Optional[Dict[str, Any]]:
        """Apply the next preset in the sequence. Returns the preset or None if done."""
        if self._current_idx >= len(self._sequence):
            return None
        preset = self._sequence[self._current_idx]
        plugin = preset.get("plugin", "")
        for param, value in preset.get("params", {}).items():
            self._store.set(plugin, param, float(value))
        self._current_idx += 1
        return preset

    def reset(self) -> None:
        self._current_idx = 0

    def is_done(self) -> bool:
        return self._current_idx >= len(self._sequence)

    @property
    def current_index(self) -> int:
        return self._current_idx

    @property
    def length(self) -> int:
        return len(self._sequence)


# ── CLI argument parser ────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vjlive3-cli",
        description="VJLive3 command-line automation tool",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # list-plugins
    sub.add_parser("list-plugins", help="List all available plugins")

    # set-param
    sp = sub.add_parser("set-param", help="Set a plugin parameter")
    sp.add_argument("plugin", help="Plugin name")
    sp.add_argument("param", help="Parameter name")
    sp.add_argument("value", type=float, help="Value (0-10)")

    # get-param
    gp = sub.add_parser("get-param", help="Get a plugin parameter value")
    gp.add_argument("plugin", help="Plugin name")
    gp.add_argument("param", help="Parameter name")

    # agent-status
    sub.add_parser("agent-status", help="Show current agent system status")

    # export-osc
    eo = sub.add_parser("export-osc", help="Export OSC address layout as JSON")
    eo.add_argument("--output", "-o", default="osc_layout.json", help="Output file")

    # load-preset
    lp = sub.add_parser("load-preset", help="Load a preset JSON file")
    lp.add_argument("path", help="Path to preset file")

    # save-preset
    sv = sub.add_parser("save-preset", help="Save current params as preset")
    sv.add_argument("path", help="Output path")

    return parser


def run_cli(argv: Optional[List[str]] = None) -> int:
    """Entry point for CLI. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    store = ParamStore()

    if args.command == "list-plugins":
        # In a real session this would query the registry
        print("Available plugins: (connect to VJLive3 engine for live list)")
        return 0

    elif args.command == "set-param":
        store.set(args.plugin, args.param, args.value)
        print(f"Set {args.plugin}.{args.param} = {args.value}")
        return 0

    elif args.command == "get-param":
        v = store.get(args.plugin, args.param)
        print(f"{args.plugin}.{args.param} = {v}")
        return 0

    elif args.command == "agent-status":
        print("Agent system: standalone CLI mode — no live agents (engine not connected).")
        return 0

    elif args.command == "export-osc":
        exporter = OSCLayoutExporter()
        result = exporter.export({}, path=args.output)
        print(f"Exported {result['count']} OSC addresses to {args.output}")
        return 0

    elif args.command == "load-preset":
        store.load_json(args.path)
        print(f"Loaded preset from {args.path}")
        return 0

    elif args.command == "save-preset":
        store.save_json(args.path)
        print(f"Saved params to {args.path}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(run_cli())
