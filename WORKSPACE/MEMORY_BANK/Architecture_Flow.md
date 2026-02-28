# VJLive3 Global Architecture Map (Phase 3 Approval)

This document represents the consolidated, global analysis of the 109 fleshed-out specs in `docs/specs/_02_fleshed_out/`. No code will be written in Phase 4 until this diagram is approved.

## Subsystem Breakdown
- **Audio System (54 Specs)**: Beats, spectrum analysis, Reactivity Bus.
- **Depth System (58 Specs)**: Point clouds, meshes, subtraction, temporal echo.
- **Datamosh System (22 Specs)**: Video distortion, i-frame deletion, contour moshing.
- **Quantum/Consciousness (21 Specs)**: State trackers, neural network layers, parallel universe depth.
- **Lighting & Output (4 Specs)**: ArtNet, DMX, Show Control, Projection Mapping.

```mermaid
graph TD;
    %% Data Sources
    Camera["🎬 Depth/Color Camera"] --> DepthCore["👁️ Depth System Core (P3)"]
    Mic["🎤 Audio Sources (P1-A4)"] --> AudioCore["🎵 Audio Analyzer & Beat Detector (P1-A1/A2)"]

    %% Core Processors
    AudioCore --> ReactivityBus["⚡ Reactivity Bus (P1-A3)"]
    DepthCore --> ReactivityBus

    %% Render Layers
    ReactivityBus --> Quantum["✨ Quantum Consciousness System (21 Specs)"]
    ReactivityBus --> Datamosh["📺 Datamosh Renderer (22 Specs)"]
    ReactivityBus --> DepthFX["🌫️ Depth FX (58 Specs)"]

    %% Output
    Quantum --> OutputMixer["🎛️ Final Composition"]
    Datamosh --> OutputMixer
    DepthFX --> OutputMixer
    OutputMixer --> Syphon["Syphon/Spout Texture Output"]
    
    ReactivityBus --> Lighting["💡 ArtNet/DMX Out (P2-D2/D5)"]
    Lighting --> RealWorld["Physical Lights"]
```

## Approval Gate
If the macro groupings (Audio -> Reactivity -> FX -> Output) and subsystem relationships are accurate, this architecture will be locked in as the source of truth for Phase 4 Execution.
