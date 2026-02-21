"""
vjlive3.hardware
================
Physical hardware integration layer for VJLive3.

Sub-modules (added as Phase 2 tasks complete):
    midi       — P2-H1: MIDI controller input (mido + python-rtmidi)
    osc        — P2-H2: OSCQuery — advanced OSC discovery (✅ done in vjlive3.osc)
    astra      — P2-H3: Astra depth camera (OpenNI2 → PyUSB → Null fallback)
    ndi        — P2-H4: NDI video transport (system SDK, conditional import)
    dmx        — P2-D1: DMX512 engine + ArtNet/sACN output

Hardware modules MUST fail gracefully (SAFETY_RAILS.md Rail 6):
    Always wrap device init in try/except.
    Always provide a null/simulation fallback.
    Always release resources on exit (use contextmanager or __del__).

Reference: vjlive-2/core/midi_controller.py, astra_linux.py, ndi_manager.py
"""
