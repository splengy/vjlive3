"""Tests for vjlive3.ui.cli — ParamStore, OSCLayoutExporter, PresetSequencer, CLI."""
import pytest
import json
import os
import tempfile
from vjlive3.ui.cli import (
    ParamStore, OSCLayoutExporter, PresetSequencer,
    build_parser, run_cli
)


# ── ParamStore ────────────────────────────────────────────────────────────────

def test_param_store_set_get():
    s = ParamStore()
    s.set("bloom", "intensity", 7.0)
    assert s.get("bloom", "intensity") == pytest.approx(7.0)


def test_param_store_default():
    s = ParamStore()
    assert s.get("missing", "param") == pytest.approx(5.0)


def test_param_store_get_all():
    s = ParamStore()
    s.set("bloom", "intensity", 3.0)
    s.set("bloom", "mix", 8.0)
    all_p = s.get_all("bloom")
    assert all_p == {"intensity": 3.0, "mix": 8.0}


def test_param_store_all_params():
    s = ParamStore()
    s.set("a", "x", 1.0)
    s.set("b", "y", 2.0)
    total = s.all_params()
    assert "a" in total and "b" in total


def test_param_store_reset_plugin():
    s = ParamStore()
    s.set("bloom", "intensity", 5.0)
    s.reset_plugin("bloom")
    assert s.get_all("bloom") == {}


def test_param_store_reset_all():
    s = ParamStore()
    s.set("a", "x", 1.0)
    s.reset_all()
    assert s.all_params() == {}


def test_param_store_json_roundtrip(tmp_path):
    s = ParamStore()
    s.set("bloom", "intensity", 7.5)
    p = str(tmp_path / "params.json")
    s.save_json(p)
    s2 = ParamStore()
    s2.load_json(p)
    assert s2.get("bloom", "intensity") == pytest.approx(7.5)


# ── OSCLayoutExporter ─────────────────────────────────────────────────────────

def test_osc_export_address_format():
    params = {"bloom": [{"name": "intensity", "default": 5.0, "min": 0.0, "max": 10.0}]}
    result = OSCLayoutExporter.export(params)
    assert result["layout"][0]["address"] == "/vjlive3/bloom/intensity"


def test_osc_export_empty():
    result = OSCLayoutExporter.export({})
    assert result["count"] == 0
    assert result["layout"] == []


def test_osc_export_writes_file(tmp_path):
    p = str(tmp_path / "layout.json")
    OSCLayoutExporter.export(
        {"bloom": [{"name": "mix", "default": 5.0, "min": 0.0, "max": 10.0}]},
        path=p
    )
    with open(p) as f:
        data = json.load(f)
    assert data["count"] == 1


def test_osc_address_helper():
    addr = OSCLayoutExporter.address("bloom", "intensity")
    assert addr == "/vjlive3/bloom/intensity"


def test_osc_parse_address():
    result = OSCLayoutExporter.parse_address("/vjlive3/bloom/intensity")
    assert result == ("bloom", "intensity")


def test_osc_parse_address_invalid():
    assert OSCLayoutExporter.parse_address("/other/addr") is None


# ── PresetSequencer ───────────────────────────────────────────────────────────

def test_preset_sequencer_step():
    s = ParamStore()
    seq = PresetSequencer(s)
    presets = [{"plugin": "bloom", "params": {"intensity": 7.0}, "duration": 4.0}]
    seq.load(presets)
    out = seq.step()
    assert out is not None
    assert s.get("bloom", "intensity") == pytest.approx(7.0)


def test_preset_sequencer_done():
    s = ParamStore()
    seq = PresetSequencer(s)
    seq.load([{"plugin": "bloom", "params": {}, "duration": 1.0}])
    seq.step()
    assert seq.is_done()
    assert seq.step() is None


def test_preset_sequencer_reset():
    s = ParamStore()
    seq = PresetSequencer(s)
    seq.load([{"plugin": "a", "params": {}, "duration": 1.0}])
    seq.step()
    seq.reset()
    assert seq.current_index == 0
    assert not seq.is_done()


def test_preset_sequencer_length():
    s = ParamStore()
    seq = PresetSequencer(s)
    seq.load([{}, {}, {}])
    assert seq.length == 3


# ── CLI ───────────────────────────────────────────────────────────────────────

def test_cli_no_args():
    assert run_cli([]) == 0


def test_cli_set_param():
    assert run_cli(["set-param", "bloom", "intensity", "7.0"]) == 0


def test_cli_get_param():
    assert run_cli(["get-param", "bloom", "intensity"]) == 0


def test_cli_list_plugins():
    assert run_cli(["list-plugins"]) == 0


def test_cli_agent_status():
    assert run_cli(["agent-status"]) == 0


def test_cli_export_osc(tmp_path):
    out = str(tmp_path / "layout.json")
    code = run_cli(["export-osc", "--output", out])
    assert code == 0
    assert os.path.exists(out)


def test_cli_save_load_preset(tmp_path):
    p = str(tmp_path / "preset.json")
    # write an empty preset
    with open(p, "w") as f:
        json.dump({}, f)
    assert run_cli(["load-preset", p]) == 0


def test_parser_has_all_commands():
    parser = build_parser()
    # Parser should recognise all 7 commands
    for cmd in ("list-plugins", "set-param", "get-param", "agent-status",
                 "export-osc", "load-preset", "save-preset"):
        args = parser.parse_args([cmd] + (["bloom", "intensity", "5.0"]
                                           if cmd == "set-param" else
                                           ["bloom", "intensity"] if cmd == "get-param" else
                                           ["dummy.json"] if cmd in ("load-preset","save-preset") else []))
        assert args.command == cmd
