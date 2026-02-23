# VJLive3 Project Board
**Version:** 3.2 | **Last Updated:** 2026-02-21 | **Manager:** ROO CODE (Manager)

> [!IMPORTANT]
> **CODE WIPE — 2026-02-21 01:36**
> All `src/vjlive3/` and `tests/` deleted. Code was produced without documentation-first discipline.
> Process reset: **SPEC must exist before code. See `WORKSPACE/HOW_TO_WORK.md`.**
> Tasks are only active once the Manager assigns them to a specific Worker's `WORKSPACE/INBOXES/` file.

## Project Overview
**Mission:** Operation Source Zero — Synthesize the best of BOTH legacy codebases into one clean architecture.
**Active Codebase:** `VJLive3_The_Reckoning/` | References (READ-ONLY): `VJlive-2/`, `vjlive/`
**Architecture Foundation:** VJlive-2's clean architecture for ALL features. Port vjlive's unique features with quality standards applied.
**Scale:** Hundreds of features across both codebases | 20-24 weeks | 2-3 agents in parallel

> See `VJlive-2/FEATURE_MATRIX.md` for the authoritative feature synthesis decisions.

---

## Phase 0: Professional Environment Setup NOT COMPLETE

| Task ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| P0-G1 | WORKSPACE/PRIME_DIRECTIVE.md | P0 | ✅ Done | |
| P0-G2 | WORKSPACE/SAFETY_RAILS.md | P0 | ✅ Done | |
| P0-G3 | WORKSPACE/COMMS/AGENT_SYNC.md | P0 | ✅ Done | |
| P0-G4 | WORKSPACE/COMMS/LOCKS.md | P0 | ✅ Done | |
| P0-G5 | WORKSPACE/COMMS/DECISIONS.md | P0 | ✅ Done | 7 ADRs logged |
| P0-G6 | WORKSPACE/KNOWLEDGE/DREAMER_LOG.md | P0 | ✅ Done | Sigil + 3 entries |
| P0-G7 | WORKSPACE/KNOWLEDGE/TOOL_TIPS.md | P0 | ✅ Done | |
| P0-G8 | Root PRIME_DIRECTIVE.md | P0 | ✅ Done | |
| P0-W1 | .agent/workflows/manager-job.md | P0 | ✅ Done | |
| P0-W2 | .agent/workflows/no-stub-policy.md | P0 | ✅ Done | |
| P0-W3 | .agent/workflows/bespoke-plugin-migration.md | P0 | ✅ Done | |
| P0-W4 | .agent/workflows/phase-gate-check.md | P0 | ✅ Done | |
| P0-Q1 | scripts/check_stubs.py | P0 | ✅ Done | |
| P0-Q2 | scripts/check_file_size.py | P0 | ✅ Done | 750-line enforcer |
| P0-Q3 | scripts/check_file_lock.py | P0 | ✅ Done | |
| P0-Q4 | .pre-commit-config.yaml | P0 | ✅ Done | 3 custom hooks |
| P0-S1 | Silicon Sigil — src/vjlive3/core/sigil.py | P0 | ✅ Done | Cave painting v3 — 11/11 tests ✅ 2026-02-21 |
| P0-M1 | MCP server: vjlive3brain (knowledge base) | P0 | ✅ Done | FastMCP, 7 tools, 19k+ concepts seeded |
| P0-M2 | MCP server: vjlive-switchboard (locks + comms + queue) | P0 | ✅ Done | FastMCP, 9 tools, orchestrator active |
| P0-A1 | Phase 0 App Window (FPS · Memory · Agents) | P0 | ✅ Done | Implementation plan drafted |
| P0-V1 | Phase gate check | P0 | ✅ Done | MCP verified, FPS validation passed |

**Phase 0 Gate Requirements:**
- [x] MCP servers start without error (brain ✅, switchboard ✅)
- [x] Pre-commit hooks pass on clean codebase
- [x] Status window running (FPS ≥ 58, visible)
- [x] Silicon Sigil verified on boot
- [x] AGENT_SYNC.md phase completion note

### P0-INF2: Legacy Feature Parity Analysis & Implementation Plan

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P0-INF2 | Legacy Feature Parity - 218 missing plugins (comprehensive audit) | P0 | ⬜ Todo | Comprehensive audit of vjlive/ & VJlive-2/ |
| | **Spec:** `docs/specs/P0-INF2_legacy_feature_parity.md` | | | |
| | **Critical Collections:** | | | |
| | - Depth Collection: 50 missing depth plugins | | | |
| | - Audio Families: 7 missing audio plugins | | | |
| | - Datamosh Family: 36 missing effects | | | |
| | - Quantum/AI: 10 missing advanced systems | | | |
| | - V-Effects: 1 missing visual effect | | | |
| | - Modulators: 1 missing modulator | | | |
| | - Generators: 15 missing generators | | | |
| | - Particle/3D: 5 missing 3D/particle systems | | | |
| | - Other (Utilities/Effects): 93 missing plugins | | | |

**Implementation Strategy:**
- Phase 3: Depth Collection (50 plugins) — P3-VD26 through P3-VD75
- Phase 4: Audio Plugin Families (7 plugins) — P4-AU02 through P4-AU08
- Phase 5: Datamosh (36), V-Effects (1), Modulators (1) — P5-DM02 through P5-VE02
- Phase 6: Generators (15), Particle/3D (5), Quantum/AI (14) — P6-GE06 through P6-QC14
- Phase 7: Other Visual Effects & Utilities (93) — P7-VE01 through P7-VE82

**Verification:** All 218 plugins ported with 60 FPS, 80%+ test coverage, zero safety rail violations. Each plugin is unique and receives bespoke treatment.

### P0-INF3: Missing Legacy Effects Parity (423 Discovered)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P3-EXT001 | ascii_effect (ASCIIEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT002 | vcv_video_effects (AdaptiveContrastEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT003 | particles_3d (AdvancedParticle3DSystem) | P0 | ⬜ Todo | vjlive |
| P3-EXT004 | agent_avatar (AgentAvatarEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT005 | living_fractal_consciousness (AgentPersonality) | P0 | ⬜ Todo | vjlive |
| P3-EXT006 | analog_tv (AnalogTVEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT007 | arbhar_granular_engine (ArbharGranularEngine) | P0 | ⬜ Todo | vjlive |
| P3-EXT008 | arbhar_granularizer (ArbharGranularizer) | P0 | ⬜ Todo | vjlive |
| P3-EXT009 | raymarched_scenes (AudioReactiveRaymarchedScenes) | P0 | ⬜ Todo | vjlive |
| P3-EXT010 | audio_reactive_effects (AudioSpectrumTrails) | P0 | ⬜ Todo | vjlive |
| P3-EXT011 | background_subtraction (BackgroundSubtractionEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT012 | depth_effects (BackgroundSubtractionEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT013 | bad_trip_datamosh (BadTripDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT014 | bass_cannon_datamosh (BassCannonDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT015 | bass_cannon_2 (BassCanon2) | P0 | ⬜ Todo | vjlive |
| P3-EXT016 | bass_therapy_datamosh (BassTherapyDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT017 | pop_art_effects (BenDayDotsEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT018 | blend (BlendAddEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT019 | blend (BlendDiffEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT020 | blend (BlendMultEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT021 | blend (BloomEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT022 | blend (BloomShadertoyEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT023 | color (BrightnessEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT024 | bullet_time_datamosh (BulletTimeDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT025 | vcv_video_generators (ByteBeatGen) | P0 | ⬜ Todo | vjlive |
| P3-EXT026 | cellular_automata_datamosh (CellularAutomataDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT027 | chroma_key (ChromaKeyEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT028 | distortion (ChromaticDistortionEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT029 | color (ColorCorrectEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT030 | color (ColoramaEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT031 | quantum_consciousness_explorer (ConsciousnessLevel) | P0 | ⬜ Todo | vjlive |
| P3-EXT032 | tunnel_vision_3 (ConsciousnessNet) | P0 | ⬜ Todo | vjlive |
| P3-EXT033 | consciousness_neural_network (ConsciousnessNeuralNetwork) | P0 | ⬜ Todo | vjlive |
| P3-EXT034 | color (ContrastEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT035 | cosmic_tunnel_datamosh (CosmicTunnelDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT036 | cotton_candy_datamosh (CottonCandyDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT037 | cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT038 | datamosh_3d (Datamosh3DEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT039 | vcv_video_effects (DelayZoomEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT040 | depth_acid_fractal (DepthAcidFractalDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT041 | depth_camera_splitter (DepthCameraSplitterEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT042 | depth_data_mux (DepthDataMuxEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT043 | datamosh_3d (DepthDisplacementEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT044 | depth_distance_filter (DepthDistanceFilterEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT045 | depth_effects (DepthDistortionEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT046 | depth_dual (DepthDualEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT047 | datamosh_3d (DepthEchoEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT048 | depth_fx_loop (DepthFXLoopEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT049 | depth_feedback_matrix_datamosh (DepthFeedbackMatrixDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT050 | depth_effects (DepthFieldEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT051 | depth_fog (DepthFogEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT052 | depth_groovy_datamosh (DepthGroovyDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT053 | depth_holographic (DepthHolographicIridescenceEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT054 | depth_loop_injection_datamosh (DepthLoopInjectionDatamoshEffect) | P0 | ✅ Done | vjlive |
| P3-EXT055 | depth_effects (DepthMeshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT056 | depth_modular_datamosh (DepthModularDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT057 | depth_modulated_datamosh (DepthModulatedDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT058 | depth_mosh_nexus (DepthMoshNexus) | P0 | ⬜ Todo | vjlive |
| P3-EXT059 | depth_parallel_universe_datamosh (DepthParallelUniverseDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT060 | depth_effects (DepthParticle3DEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT061 | depth_effects (DepthPointCloud3DEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT062 | depth_effects (DepthPointCloudEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT063 | depth_raver_datamosh (DepthRaverDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT064 | depth_simulator (DepthSimulatorEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT065 | depth_slitscan_datamosh (DepthSlitScanDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT066 | depth_effects (DepthVisualizationMode) | P0 | ⬜ Todo | vjlive |
| P3-EXT067 | depth_void_datamosh (DepthVoidDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT068 | dimension_splice_datamosh (DimensionSpliceDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT069 | displacement_map (DisplacementMapEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT070 | dithering (DitheringEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT071 | dolly_zoom_datamosh (DollyZoomDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT072 | vtempi (DutyCycleMode) | P0 | ⬜ Todo | vjlive |
| P3-EXT073 | particles_3d (EmitterType) | P0 | ⬜ Todo | vjlive |
| P3-EXT074 | erbe_verb (ErbeVerb) | P0 | ⬜ Todo | vjlive |
| P3-EXT075 | example_glitch (ExampleGlitchEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT076 | vcv_video_generators (FMCoordinatesGen) | P0 | ⬜ Todo | vjlive |
| P3-EXT077 | face_melt_datamosh (FaceMeltDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT078 | shadertoy_particles (FireParticles) | P0 | ⬜ Todo | vjlive |
| P3-EXT079 | fluid_sim (FluidSimEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT080 | particles_3d (ForceType) | P0 | ⬜ Todo | vjlive |
| P3-EXT081 | fractal_generator (FractalGenerator) | P0 | ⬜ Todo | vjlive |
| P3-EXT082 | fracture_rave_datamosh (FractureRaveDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT083 | datamosh (FrameHoldEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT084 | vcv_video_effects (GaussianBlurEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT085 | generators (GradientEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT086 | vcv_video_generators (GranularVideoGen) | P0 | ⬜ Todo | vjlive |
| P3-EXT087 | vcv_video_effects (HDRToneMapEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT088 | vcv_video_generators (HarmonicPatternsGen) | P0 | ⬜ Todo | vjlive |
| P3-EXT089 | v_sws (HorizontalWaveEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT090 | vtempi (HumanResolution) | P0 | ⬜ Todo | vjlive |
| P3-EXT091 | neural_quantum_hyper_tunnel (HyperTunnelNet) | P0 | ⬜ Todo | vjlive |
| P3-EXT092 | hyperspace_quantum_tunnel (HyperspaceQuantumTunnel) | P0 | ⬜ Todo | vjlive |
| P3-EXT093 | blend (InfiniteFeedbackEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT094 | color (InvertEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT095 | vtempi (LEDColor) | P0 | ⬜ Todo | vjlive |
| P3-EXT096 | lut_grading (LUTGradingEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT097 | datamosh_3d (LayerSeparationEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT098 | liquid_lsd_datamosh (LiquidLSDDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT099 | luma_chroma_mask (LumaChromaMaskEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT100 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT101 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT102 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT103 | ml_gpu_effects (MLStyleGLEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT104 | vcv_video_generators (MacroShapeGen) | P0 | ⬜ Todo | vjlive |
| P3-EXT105 | generators (MandalaEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT106 | geometry (MandalascopeEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT107 | geometry (MirrorEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT108 | blend (MixerEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT109 | vtempi (ModBehavior) | P0 | ⬜ Todo | vjlive |
| P3-EXT110 | morphology (MorphologyEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT111 | mosh_pit_datamosh (MoshPitDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT112 | vcv_video_effects (MultibandColorEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT113 | shadertoy_particles (NebulaParticles) | P0 | ⬜ Todo | vjlive |
| P3-EXT114 | neural_rave_nexus (NeuralRaveNexus) | P0 | ⬜ Todo | vjlive |
| P3-EXT115 | neural_splice_datamosh (NeuralSpliceDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT116 | tunnel_vision_2 (NeuralTunnelNet) | P0 | ⬜ Todo | vjlive |
| P3-EXT117 | optical_flow (OpticalFlowEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT118 | depth_effects (OpticalFlowEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT119 | oscilloscope (OscilloscopeEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT120 | visualizer (OscilloscopeEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT121 | particles_3d (Particle3DSystem) | P0 | ⬜ Todo | vjlive |
| P3-EXT122 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT123 | particles_3d (ParticleState) | P0 | ⬜ Todo | vjlive |
| P3-EXT124 | distortion (PatternDistortionEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT125 | generators (PerlinEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT126 | datamosh (PixelBloomEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT127 | datamosh (PixelSortEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT128 | geometry (PixelateEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT129 | plasma_melt_datamosh (PlasmaMeltDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT130 | color (PosterizeEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT131 | prism_realm_datamosh (PrismRealmDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT132 | vtempi (ProgramPage) | P0 | ⬜ Todo | vjlive |
| P3-EXT133 | quantum_consciousness_datamosh (QuantumConsciousnessDatamosh) | P0 | ⬜ Todo | vjlive |
| P3-EXT134 | tunnel_vision_3 (QuantumConsciousnessSingularityEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT135 | quantum_depth_nexus (QuantumDepthNexus) | P0 | ⬜ Todo | vjlive |
| P3-EXT136 | quantum_entanglement_point_cloud (QuantumEntanglementPointCloud) | P0 | ⬜ Todo | vjlive |
| P3-EXT137 | quantum_consciousness_explorer (QuantumState) | P0 | ⬜ Todo | vjlive |
| P3-EXT138 | quantum_consciousness_explorer (QuantumState) | P0 | ⬜ Todo | vjlive |
| P3-EXT139 | r16_deep_mosh_studio (R16DeepMoshStudio) | P0 | ⬜ Todo | vjlive |
| P3-EXT140 | r16_depth_wave (R16DepthWave) | P0 | ⬜ Todo | vjlive |
| P3-EXT141 | r16_interstellar_mosh (R16InterstellarMosh) | P0 | ⬜ Todo | vjlive |
| P3-EXT142 | r16_simulated_depth (R16SimulatedDepth) | P0 | ⬜ Todo | vjlive |
| P3-EXT143 | r16_vortex (R16VortexEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT144 | color (RGBShiftEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT145 | vibrant_retro_styles (RadiantMeshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT146 | rainmaker_rhythmic_echo (RainmakerRhythmicEcho) | P0 | ⬜ Todo | vjlive |
| P3-EXT147 | reaction_diffusion (ReactionDiffusionEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT148 | reality_distortion_field (RealityDistortionField) | P0 | ⬜ Todo | vjlive |
| P3-EXT149 | particles_3d (RenderMode) | P0 | ⬜ Todo | vjlive |
| P3-EXT150 | geometry (RepeatEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT151 | resize_effect (ResizeEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT152 | vcv_video_effects (ResonantBlurEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT153 | vcv_video_generators (ResonantGeometryGen) | P0 | ⬜ Todo | vjlive |
| P3-EXT154 | vibrant_retro_styles (RioAestheticEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT155 | v_sws (RippleEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT156 | geometry (RotateEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT157 | vtempi (RunStopMode) | P0 | ⬜ Todo | vjlive |
| P3-EXT158 | rutt_etra_scanline (RuttEtraScanlineEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT159 | sacred_geometry_datamosh (SacredGeometryDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT160 | color (SaturateEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT161 | blend (ScanlinesEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT162 | scion_biometric_flux (ScionBiometricFlux) | P0 | ⬜ Todo | vjlive |
| P3-EXT163 | geometry (ScrollEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT164 | shadertoy_particles (ShadertoyParticles) | P0 | ⬜ Todo | vjlive |
| P3-EXT165 | datamosh_3d (ShatterEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT166 | vtempi (ShiftDirection) | P0 | ⬜ Todo | vjlive |
| P3-EXT167 | simulated_color_depth (SimulatedColorDepth) | P0 | ⬜ Todo | vjlive |
| P3-EXT168 | slit_scan (SlitScanEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT169 | vcv_video_effects (SolarizeEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT170 | vcv_video_effects (SpatialEchoEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT171 | visualizer (SpectrumAnalyzerEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT172 | v_sws (SpiralWaveEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT173 | spirit_aura_datamosh (SpiritAuraDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT174 | sync_eater (SyncEaterEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT175 | temporal_rift_datamosh (TemporalRiftDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT176 | test_bass_cannon_3 (TestBassCanon3) | P0 | ⬜ Todo | vjlive |
| P3-EXT177 | test_neural_quantum_hyper_tunnel (TestIntegrationWithVJLive) | P0 | ⬜ Todo | vjlive |
| P3-EXT178 | test_neural_quantum_hyper_tunnel (TestNeuralQuantumHyperTunnel) | P0 | ⬜ Todo | vjlive |
| P3-EXT179 | test_plugin (TestPluginPlugin) | P0 | ⬜ Todo | vjlive |
| P3-EXT180 | color (ThreshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT181 | time_remap (TimeRemapEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT182 | agent_avatar (TravelingAvatarEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT183 | tunnel_vision_datamosh (TunnelVisionDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT184 | unicorn_farts_datamosh (UnicornFartsDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT185 | vattractors (VHalvorsenPlugin) | P0 | ⬜ Todo | vjlive |
| P3-EXT186 | vattractors (VLorenzPlugin) | P0 | ⬜ Todo | vjlive |
| P3-EXT187 | v_rainmaker_rhythmic_echo (VRainmakerRhythmicEcho) | P0 | ⬜ Todo | vjlive |
| P3-EXT188 | vattractors (VSakaryaPlugin) | P0 | ⬜ Todo | vjlive |
| P3-EXT189 | vbefaco_extra (VScopeXL) | P0 | ⬜ Todo | vjlive |
| P3-EXT190 | v_sws (VSwsEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT191 | vattractors (VThomasPlugin) | P0 | ⬜ Todo | vjlive |
| P3-EXT192 | visualizer (VUMeterEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT193 | v_warps (VWarps) | P0 | ⬜ Todo | vjlive |
| P3-EXT194 | v_sws (VerticalWaveEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT195 | blend (VignetteEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT196 | visualizer (VisualizerEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT197 | void_swirl_datamosh (VoidSwirlDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT198 | volumetric_datamosh (VolumetricDatamoshEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT199 | volumetric_glitch (VolumetricGlitchEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT200 | generators (VoronoiEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT201 | pop_art_effects (WarholQuadEffect) | P0 | ⬜ Todo | vjlive |
| P3-EXT202 | blend_modes (_BlendMode) | P0 | ⬜ Todo | vjlive |
| P3-EXT203 | ml_gpu_effects (_WorkerThread) | P0 | ⬜ Todo | vjlive |
| P3-EXT204 | particles_3d (AdvancedParticle3DSystem) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT205 | particles_3d (AdvancedParticle3DSystem) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT206 | particles_3d (AdvancedParticle3DSystem) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT207 | silver_visions (AffineTransformEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT208 | agent_avatar (AgentAvatarEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT209 | agent_avatar (AgentAvatarEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT210 | astra_node (AstraNode) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT211 | raymarched_scenes (AudioReactiveRaymarchedScenes) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT212 | raymarched_scenes (AudioReactiveRaymarchedScenes) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT213 | audio_reactive (AudioSpectrumTrails) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT214 | depth_effects (BackgroundSubtractionEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT215 | bad_trip_datamosh (BadTripDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT216 | bass_cannon_datamosh (BassCannonDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT217 | bass_cannon_2 (BassCanon2) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT218 | bass_therapy_datamosh (BassTherapyDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT219 | pop_art_effects (BenDayDotsEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT220 | pop_art_effects (BenDayDotsEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT221 | bullet_time_datamosh (BulletTimeDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT222 | cellular_automata_datamosh (CellularAutomataDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT223 | colorama (ColoramaEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT224 | tunnel_vision_3 (ConsciousnessNet) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT225 | consciousness_neural_network (ConsciousnessNeuralNetwork) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT226 | consciousness_neural_network_effect (ConsciousnessNeuralNetwork) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT227 | silver_visions (CoordinateFolderEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT228 | cosmic_tunnel_datamosh (CosmicTunnelDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT229 | cotton_candy_datamosh (CottonCandyDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT230 | cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT231 | datamosh_3d (Datamosh3DEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT232 | depth_acid_fractal (DepthAcidFractalDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT233 | depth_camera_splitter (DepthCameraSplitterEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT234 | depth_data_mux (DepthDataMuxEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT235 | datamosh_3d (DepthDisplacementEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT236 | depth_distance_filter (DepthDistanceFilterEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT237 | depth_effects (DepthDistortionEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT238 | depth_dual (DepthDualEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT239 | datamosh_3d (DepthEchoEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT240 | depth_fx_loop (DepthFXLoopEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT241 | depth_feedback_matrix_datamosh (DepthFeedbackMatrixDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT242 | depth_effects (DepthFieldEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT243 | depth_fog (DepthFogEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT244 | depth_groovy_datamosh (DepthGroovyDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT245 | depth_holographic (DepthHolographicIridescenceEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT246 | depth_loop_injection_datamosh (DepthLoopInjectionDatamoshEffect) | P0 | ✅ Done | VJlive-2 |
| P3-EXT247 | depth_effects (DepthMeshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT248 | depth_modular_datamosh (DepthModularDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT249 | depth_modulated_datamosh (DepthModulatedDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT250 | depth_mosh_nexus (DepthMoshNexus) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT251 | depth_parallel_universe_datamosh (DepthParallelUniverseDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT252 | depth_effects (DepthParticle3DEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT253 | depth_effects (DepthPointCloud3DEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT254 | depth_effects (DepthPointCloudEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT255 | depth_raver_datamosh (DepthRaverDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT256 | depth_simulator (DepthSimulatorEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT257 | depth_slitscan_datamosh (DepthSlitScanDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT258 | depth_effects (DepthVisualizationMode) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT259 | depth_void_datamosh (DepthVoidDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT260 | dimension_splice_datamosh (DimensionSpliceDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT261 | dolly_zoom_datamosh (DollyZoomDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT262 | vtempi (DutyCycleMode) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT263 | vtempi (DutyCycleMode) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT264 | particles_3d (EmitterType) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT265 | particles_3d (EmitterType) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT266 | face_melt_datamosh (FaceMeltDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT267 | shadertoy_particles (FireParticles) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT268 | shadertoy_particles (FireParticles) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT269 | shadertoy_particles (FireParticles) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT270 | fluid_sim (FluidSimEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT271 | particles_3d (ForceType) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT272 | particles_3d (ForceType) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT273 | fracture_rave_datamosh (FractureRaveDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT274 | vtempi (HumanResolution) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT275 | vtempi (HumanResolution) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT276 | neural_quantum_hyper_tunnel (HyperTunnelNet) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT277 | neural_quantum_hyper_tunnel_effect (HyperTunnelNet) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT278 | hyperspace_quantum_tunnel (HyperspaceQuantumTunnel) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT279 | hyperspace_quantum_tunnel_effect (HyperspaceQuantumTunnel) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT280 | hyperspace_tunnel (HyperspaceTunnelEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT281 | silver_visions (ImageInEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT282 | vtempi (LEDColor) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT283 | vtempi (LEDColor) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT284 | datamosh_3d (LayerSeparationEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT285 | liquid_lsd_datamosh (LiquidLSDDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT286 | ml_effects (MLBaseAsyncEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT287 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT288 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT289 | ml_effects (MLDepthEstimationEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT290 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT291 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT292 | ml_effects (MLSegmentationBlurGLEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT293 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT294 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT295 | ml_effects (MLStyleGLEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT296 | ml_gpu_effects (MLStyleGLEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT297 | ml_gpu_effects (MLStyleGLEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT298 | vtempi (ModBehavior) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT299 | vtempi (ModBehavior) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT300 | mosh_pit_datamosh (MoshPitDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT301 | shadertoy_particles (NebulaParticles) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT302 | shadertoy_particles (NebulaParticles) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT303 | shadertoy_particles (NebulaParticles) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT304 | neural_rave_nexus (NeuralRaveNexus) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT305 | neural_splice_datamosh (NeuralSpliceDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT306 | tunnel_vision_2 (NeuralTunnelNet) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT307 | depth_effects (OpticalFlowEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT308 | particles_3d (Particle3DSystem) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT309 | particles_3d (Particle3DSystem) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT310 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT311 | particles_3d (ParticleState) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT312 | particles_3d (ParticleState) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT313 | plasma_melt_datamosh (PlasmaMeltDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT314 | silver_visions (PreciseDelayEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT315 | prism_realm_datamosh (PrismRealmDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT316 | vtempi (ProgramPage) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT317 | vtempi (ProgramPage) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT318 | quantum_consciousness_datamosh (QuantumConsciousnessDatamosh) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT319 | quantum_consciousness_datamosh_effect (QuantumConsciousnessDatamosh) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT320 | tunnel_vision_3 (QuantumConsciousnessSingularityEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT321 | quantum_depth_nexus (QuantumDepthNexus) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT322 | quantum_depth_nexus_effect (QuantumDepthNexus) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT323 | quantum_entanglement_point_cloud (QuantumEntanglementPointCloud) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT324 | quantum_entanglement_point_cloud_effect (QuantumEntanglementPointCloud) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT325 | quantum_consciousness_explorer (QuantumState) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT326 | quantum_consciousness_explorer_effect (QuantumState) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT327 | r16_deep_mosh_studio (R16DeepMoshStudio) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT328 | r16_depth_wave (R16DepthWave) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT329 | r16_interstellar_mosh (R16InterstellarMosh) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT330 | r16_simulated_depth (R16SimulatedDepth) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT331 | r16_vortex (R16VortexEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT332 | vibrant_retro_styles (RadiantMeshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT333 | vibrant_retro_styles (RadiantMeshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT334 | reaction_diffusion (ReactionDiffusionEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT335 | reality_distortion_field (RealityDistortionField) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT336 | particles_3d (RenderMode) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT337 | particles_3d (RenderMode) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT338 | particles_3d (RenderMode) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT339 | vibrant_retro_styles (RioAestheticEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT340 | vibrant_retro_styles (RioAestheticEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT341 | vtempi (RunStopMode) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT342 | vtempi (RunStopMode) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT343 | sacred_geometry_datamosh (SacredGeometryDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT344 | shadertoy_particles (ShadertoyParticles) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT345 | shadertoy_particles (ShadertoyParticles) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT346 | shadertoy_particles (ShadertoyParticles) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT347 | datamosh_3d (ShatterEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT348 | vtempi (ShiftDirection) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT349 | vtempi (ShiftDirection) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT350 | simulated_color_depth (SimulatedColorDepth) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT351 | spirit_aura_datamosh (SpiritAuraDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT352 | temporal_rift_datamosh (TemporalRiftDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT353 | test_bass_cannon_3 (TestBassCanon3) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT354 | test_neural_quantum_hyper_tunnel (TestIntegrationWithVJLive) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT355 | test_neural_quantum_hyper_tunnel (TestNeuralQuantumHyperTunnel) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT356 | test_plugin (TestPluginPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT357 | agent_avatar (TravelingAvatarEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT358 | agent_avatar (TravelingAvatarEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT359 | tunnel_vision_datamosh (TunnelVisionDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT360 | unicorn_farts_datamosh (UnicornFartsDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT361 | vvoxglitch (VByteBeat) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT362 | vmake_noise (VDXGPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT363 | vmake_noise (VDynaMixPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT364 | vmake_noise (VErbeVerbPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT365 | vmi_complex (VFramesMIPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT366 | vmake_noise (VFxDfPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT367 | vvoxglitch (VGhosts) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT368 | vvoxglitch (VGlitchSequencer) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT369 | vvoxglitch (VGrooveBox) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT370 | vattractors (VHalvorsenPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT371 | vattractors (VHalvorsenPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT372 | vvoxglitch (VHazumi) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT373 | vattractors (VLorenzPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT374 | vattractors (VLorenzPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT375 | vlxd (VLxDPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT376 | vmake_noise (VMorphagenePlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT377 | vmake_noise (VQMMGPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT378 | vmake_noise (VQXGPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT379 | vmake_noise (VRenePlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT380 | vvoxglitch (VRepeater) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT381 | vmi_complex (VRingsMIPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT382 | vmi_complex (VRipplesMIPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT383 | vmake_noise (VRosiePlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT384 | vmake_noise (VRxMxPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT385 | vattractors (VSakaryaPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT386 | vattractors (VSakaryaPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT387 | vvoxglitch (VSatanonaut) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT388 | vbefaco_extra (VScopeXL) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT389 | vmake_noise (VSpectraphonPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT390 | vmi_complex (VStagesMIPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT391 | vmi_complex (VStreamsMIPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT392 | vattractors (VThomasPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT393 | vattractors (VThomasPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT394 | vmi_complex (VTidesMIPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT395 | vmi_complex (VWarpsMIPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT396 | vmake_noise (VWogglebugPlugin) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT397 | vvoxglitch (VXY) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT398 | base (VechophonBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT399 | base (VfunctionBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT400 | silver_visions (VideoOutEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT401 | hyperion (VimanaHyperion) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT402 | vimana_hyperion_ultimate (VimanaHyperionUltimate) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT403 | base (VjumblerBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT404 | base (VlxdBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT405 | base (Vmake_noiseBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT406 | base (VmathsBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT407 | base (Vmi_complexBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT408 | base (VmlBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT409 | void_swirl_datamosh (VoidSwirlDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT410 | volumetric_datamosh (VolumetricDatamoshEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT411 | volumetric_glitch (VolumetricGlitchEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT412 | base (VparticlesBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT413 | base (Vshadertoy_extraBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT414 | base (Vstages_anomBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT415 | base (VstyleBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT416 | base (VtempiBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT417 | base (Vtides_anomBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT418 | base (VvoxglitchBase) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT419 | pop_art_effects (WarholQuadEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT420 | pop_art_effects (WarholQuadEffect) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT421 | ml_effects (_WorkerThread) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT422 | ml_gpu_effects (_WorkerThread) | P0 | ⬜ Todo | VJlive-2 |
| P3-EXT423 | ml_gpu_effects (_WorkerThread) | P0 | ⬜ Todo | VJlive-2 |


### P0-INF4: Core Logic Parity (~1800 Discovered)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P4-COR001 | ai_sanitizer (AIAnomalyDetector) | P0 | ⬜ Todo | Legacy |
| P4-COR002 | ai_assistant (AIAssistant) | P0 | ⬜ Todo | Legacy |
| P4-COR003 | automation_timeline (AIBrain) | P0 | ⬜ Todo | Legacy |
| P4-COR004 | co_creation_enhanced (AICreativeAssistant) | P0 | ⬜ Todo | Legacy |
| P4-COR005 | creative_partner (AICreativePartner) | P0 | ⬜ Todo | Legacy |
| P4-COR006 | creative_partner (AICreativePartnerFactory) | P0 | ⬜ Todo | Legacy |
| P4-COR007 | co_creation_enhanced (AICurator) | P0 | ⬜ Todo | Legacy |
| P4-COR008 | ai_assistant (AIHint) | P0 | ⬜ Todo | Legacy |
| P4-COR009 | ai_integration (AIIntegration) | P0 | ⬜ Todo | Legacy |
| P4-COR010 | quantum_reactor (AIParameterPrediction) | P0 | ⬜ Todo | Legacy |
| P4-COR011 | config_constants (AIParameters) | P0 | ⬜ Todo | Legacy |
| P4-COR012 | brush_engines (AIPartnerBrush) | P0 | ⬜ Todo | Legacy |
| P4-COR013 | ai_sanitizer (AISanitizer) | P0 | ⬜ Todo | Legacy |
| P4-COR014 | brain (AIScheduler) | P0 | ⬜ Todo | Legacy |
| P4-COR015 | ai_shader_generator (AIShaderGenerator) | P0 | ⬜ Todo | Legacy |
| P4-COR016 | ai_suggestion_engine (AISuggestion) | P0 | ⬜ Todo | Legacy |
| P4-COR017 | ai_suggestion_engine (AISuggestionEngine) | P0 | ⬜ Todo | Legacy |
| P4-COR018 | ai_integration (AISystemStatus) | P0 | ⬜ Todo | Legacy |
| P4-COR019 | adain (AdaINStyleTransfer) | P0 | ⬜ Todo | Legacy |
| P4-COR020 | agent_avatar (AgentAvatarEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR021 | config_manager (AgentConfig) | P0 | ⬜ Todo | Legacy |
| P4-COR022 | agent_graph_visualizer (AgentGraphVisualizer) | P0 | ⬜ Todo | Legacy |
| P4-COR023 | unified_hydra_extensions (AgentHydraExtension) | P0 | ⬜ Todo | Legacy |
| P4-COR024 | agent_bridge (AgentInteractionMode) | P0 | ⬜ Todo | Legacy |
| P4-COR025 | agent_manager (AgentManager) | P0 | ⬜ Todo | Legacy |
| P4-COR026 | awesome_collaborative_creation (AgentMood) | P0 | ⬜ Todo | Legacy |
| P4-COR027 | agent_orchestrator (AgentOrchestrator) | P0 | ⬜ Todo | Legacy |
| P4-COR028 | text_overlay (AgentOverlay) | P0 | ⬜ Todo | Legacy |
| P4-COR029 | agent_bridge (AgentPerformanceBridge) | P0 | ⬜ Todo | Legacy |
| P4-COR030 | agent_persona (AgentPersona) | P0 | ⬜ Todo | Legacy |
| P4-COR031 | routes (AgentPersonaCreate) | P0 | ⬜ Todo | Legacy |
| P4-COR032 | models (AgentPersonaModel) | P0 | ⬜ Todo | Legacy |
| P4-COR033 | routes (AgentPersonaResponse) | P0 | ⬜ Todo | Legacy |
| P4-COR034 | awesome_collaborative_creation (AgentPersonality) | P0 | ⬜ Todo | Legacy |
| P4-COR035 | awesome_collaborative_creation (AgentPersonalityEngine) | P0 | ⬜ Todo | Legacy |
| P4-COR036 | rhythm_consciousness (AgentRhythmProfile) | P0 | ⬜ Todo | Legacy |
| P4-COR037 | agent_orchestrator (AgentState) | P0 | ⬜ Todo | Legacy |
| P4-COR038 | agent_bridge (AgentSuggestion) | P0 | ⬜ Todo | Legacy |
| P4-COR039 | creative_hive (AgentType) | P0 | ⬜ Todo | Legacy |
| P4-COR040 | agent_visualizer (AgentVisualizer) | P0 | ⬜ Todo | Legacy |
| P4-COR041 | crowd_analysis_aggregator (AggregatedCrowdState) | P0 | ⬜ Todo | Legacy |
| P4-COR042 | mutable_generators (BraidsGenerator) | P0 | ⬜ Todo | Legacy |
| P4-COR043 | node_modulation_mutable_generators (BraidsNode) | P0 | ⬜ Todo | Legacy |
| P4-COR044 | hotplug_detector_new (CameraInfo) | P0 | ⬜ Todo | Legacy |
| P4-COR045 | depth_calibration (CameraIntrinsics) | P0 | ⬜ Todo | Legacy |
| P4-COR046 | creative_hive (CompositeAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR047 | neural_engine_enhanced (CreativeNeuralEngine) | P0 | ⬜ Todo | Legacy |
| P4-COR048 | crowd_ai (CrowdAI) | P0 | ⬜ Todo | Legacy |
| P4-COR049 | llm_service (CrowdAnalysis) | P0 | ⬜ Todo | Legacy |
| P4-COR050 | crowd_analysis_aggregator (CrowdAnalysisAggregator) | P0 | ⬜ Todo | Legacy |
| P4-COR051 | llm_service (CrowdEmotion) | P0 | ⬜ Todo | Legacy |
| P4-COR052 | multi_camera_manager (CrowdEnergyAggregator) | P0 | ⬜ Todo | Legacy |
| P4-COR053 | crowd_listener (CrowdListener) | P0 | ⬜ Todo | Legacy |
| P4-COR054 | crowd_pulse_engine (CrowdPulseEngine) | P0 | ⬜ Todo | Legacy |
| P4-COR055 | crowd_listener (CrowdSource) | P0 | ⬜ Todo | Legacy |
| P4-COR056 | data_rain (DataRain) | P0 | ⬜ Todo | Legacy |
| P4-COR057 | living_debug_overlay (DebugAgentPersona) | P0 | ⬜ Todo | Legacy |
| P4-COR058 | dreamer_agent (DreamerAgentManager) | P0 | ⬜ Todo | Legacy |
| P4-COR059 | collaborative_canvas (EchoTrailEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR060 | enhanced_llm_service (EnhancedLLMService) | P0 | ⬜ Todo | Legacy |
| P4-COR061 | predictive_failure_detection (FailurePredictor) | P0 | ⬜ Todo | Legacy |
| P4-COR062 | predictive_failure_detection (FailureType) | P0 | ⬜ Todo | Legacy |
| P4-COR063 | shader_base (FramebufferRAII) | P0 | ⬜ Todo | Legacy |
| P4-COR064 | brush_engines (FrequencyPainterBrush) | P0 | ⬜ Todo | Legacy |
| P4-COR065 | ghost_agent (GhostAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR066 | creative_hive (GlitchAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR067 | harmonaig_color_harmonizer (HarmonaigColorHarmonizer) | P0 | ⬜ Todo | Legacy |
| P4-COR068 | base (IAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR069 | isf_effect (ISFEffectChain) | P0 | ⬜ Todo | Legacy |
| P4-COR070 | llm_integration (LLMModelIntegration) | P0 | ⬜ Todo | Legacy |
| P4-COR071 | llm_service (LLMPrompt) | P0 | ⬜ Todo | Legacy |
| P4-COR072 | llm_service (LLMProvider) | P0 | ⬜ Todo | Legacy |
| P4-COR073 | routes (LLMProviderCreate) | P0 | ⬜ Todo | Legacy |
| P4-COR074 | routes (LLMProviderResponse) | P0 | ⬜ Todo | Legacy |
| P4-COR075 | llm_service (LLMService) | P0 | ✅ Done | Legacy |
| P4-COR076 | main_node_graph_integration (MainNodeGraphIntegration) | P0 | ⬜ Todo | Legacy |
| P4-COR077 | media_scanner (MediaItem) | P0 | ⬜ Todo | Legacy |
| P4-COR078 | modifier_nodes (ModifierChain) | P0 | ⬜ Todo | Legacy |
| P4-COR079 | movements (NeuralAwakening) | P0 | ⬜ Todo | Legacy |
| P4-COR080 | neural_creative (NeuralCreativeEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR081 | neural_effects (NeuralEffectsEngine) | P0 | ⬜ Todo | Legacy |
| P4-COR082 | neural_engine (NeuralEngine) | P0 | ⬜ Todo | Legacy |
| P4-COR083 | neural_link (NeuralLink) | P0 | ⬜ Todo | Legacy |
| P4-COR084 | neural_engine_enhanced (NeuralMode) | P0 | ⬜ Todo | Legacy |
| P4-COR085 | automation_timeline (NeuralNetworkConfig) | P0 | ⬜ Todo | Legacy |
| P4-COR086 | neural_engine_enhanced (NeuralPreset) | P0 | ⬜ Todo | Legacy |
| P4-COR087 | node_datamosh (NeuralSpliceNode) | P0 | ⬜ Todo | Legacy |
| P4-COR088 | new_effects (NeuralStructure) | P0 | ⬜ Todo | Legacy |
| P4-COR089 | neural_style_transfer (NeuralStyleTransferNode) | P0 | ⬜ Todo | Legacy |
| P4-COR090 | neural_synthesizer (NeuralVisualSynthesizer) | P0 | ⬜ Todo | Legacy |
| P4-COR091 | openai_provider (OpenAIModelProvider) | P0 | ⬜ Todo | Legacy |
| P4-COR092 | llm_service (OpenAIProvider) | P0 | ⬜ Todo | Legacy |
| P4-COR093 | oracle (OracleBrain) | P0 | ⬜ Todo | Legacy |
| P4-COR094 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR095 | node_datamosh (ParticleTrailsNode) | P0 | ⬜ Todo | Legacy |
| P4-COR096 | creative_hive (PatternAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR097 | performance (PerformanceAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR098 | brush_engines (PersonalityTraits) | P0 | ⬜ Todo | Legacy |
| P4-COR099 | mutable_generators (PlaitsGenerator) | P0 | ⬜ Todo | Legacy |
| P4-COR100 | node_modulation_mutable_generators (PlaitsNode) | P0 | ⬜ Todo | Legacy |
| P4-COR101 | quantum_pattern_recognition (QuantumNeuralNetwork) | P0 | ⬜ Todo | Legacy |
| P4-COR102 | error_handling (SafeNeuralAwakening) | P0 | ⬜ Todo | Legacy |
| P4-COR103 | creative_hive (SentienceAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR104 | agent_example (StrobeAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR105 | creative_hive (StyleAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR106 | tain_instant_cut_switcher (TainInstantCutSwitcher) | P0 | ⬜ Todo | Legacy |
| P4-COR107 | agent_visualizer (TrailPoint) | P0 | ⬜ Todo | Legacy |
| P4-COR108 | v_harmonaig (VHarmonaig) | P0 | ⬜ Todo | Legacy |
| P4-COR109 | intelligent_locking (WaitGraph) | P0 | ⬜ Todo | Legacy |
| P4-COR110 | worker_agent (WorkerAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR111 | collaborative_canvas (AdvancedAudioReactor) | P0 | ⬜ Todo | Legacy |
| P4-COR112 | creative_hive (AudioAgent) | P0 | ⬜ Todo | Legacy |
| P4-COR113 | analyzer (AudioAnalyzer) | P0 | ⬜ Todo | Legacy |
| P4-COR114 | legacy_compat (AudioAnalyzerAdapter) | P0 | ⬜ Todo | Legacy |
| P4-COR115 | config_types (AudioConfig) | P0 | ⬜ Todo | Legacy |
| P4-COR116 | models (AudioControlPayload) | P0 | ⬜ Todo | Legacy |
| P4-COR117 | node_effect_audio (AudioDistortionNode) | P0 | ⬜ Todo | Legacy |
| P4-COR118 | engine (AudioEngine) | P0 | ⬜ Todo | Legacy |
| P4-COR119 | audio_features (AudioFeature) | P0 | ⬜ Todo | Legacy |
| P4-COR120 | audio_features (AudioFeatureExtractor) | P0 | ⬜ Todo | Legacy |
| P4-COR121 | audio_features (AudioFeatureType) | P0 | ⬜ Todo | Legacy |
| P4-COR122 | audio_kaleidoscope (AudioKaleidoscope) | P0 | ⬜ Todo | Legacy |
| P4-COR123 | node_effect_audio (AudioKaleidoscopeNode) | P0 | ⬜ Todo | Legacy |
| P4-COR124 | node_effect_audio (AudioParticleNode) | P0 | ⬜ Todo | Legacy |
| P4-COR125 | audio_particle_system (AudioParticleSystem) | P0 | ⬜ Todo | Legacy |
| P4-COR126 | audio_player (AudioPlayer) | P0 | ⬜ Todo | Legacy |
| P4-COR127 | audio_reactive_3d_effect (AudioReactive3DEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR128 | audio_reactive_3d_scene (AudioReactive3DScene) | P0 | ⬜ Todo | Legacy |
| P4-COR129 | audio_reactive_3d_scene_ultimate (AudioReactive3DSceneUltimate) | P0 | ⬜ Todo | Legacy |
| P4-COR130 | brush_engines (AudioReactiveBrush) | P0 | ⬜ Todo | Legacy |
| P4-COR131 | audio_reactive_effects (AudioReactiveEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR132 | audio_reactive (AudioReactiveEngine) | P0 | ⬜ Todo | Legacy |
| P4-COR133 | unified_hydra_extensions (AudioReactiveHydraExtension) | P0 | ⬜ Todo | Legacy |
| P4-COR134 | unified_base (AudioReactiveMixin) | P0 | ⬜ Todo | Legacy |
| P4-COR135 | living_debug_overlay (AudioReactiveParticle) | P0 | ⬜ Todo | Legacy |
| P4-COR136 | living_debug_overlay (AudioReactiveParticleSystem) | P0 | ⬜ Todo | Legacy |
| P4-COR137 | mood_temporal_patterns (AudioReactivePatternGenerator) | P0 | ⬜ Todo | Legacy |
| P4-COR138 | audio_reactive (AudioReactivePreset) | P0 | ⬜ Todo | Legacy |
| P4-COR139 | audio_reactivity (AudioReactivity) | P0 | ⬜ Todo | Legacy |
| P4-COR140 | unified_matrix_integration (AudioReactivityIntegrator) | P0 | ⬜ Todo | Legacy |
| P4-COR141 | audio_reactor (AudioReactor) | P0 | ⬜ Todo | Legacy |
| P4-COR142 | audio_reactor (AudioReactorManager) | P0 | ⬜ Todo | Legacy |
| P4-COR143 | engine (AudioSource) | P0 | ⬜ Todo | Legacy |
| P4-COR144 | engine (AudioSourceType) | P0 | ⬜ Todo | Legacy |
| P4-COR145 | depth_audio (AudioSpectrum) | P0 | ⬜ Todo | Legacy |
| P4-COR146 | audio_spectrum_trails (AudioSpectrumTrails) | P0 | ⬜ Todo | Legacy |
| P4-COR147 | new_effects (AudioStrobe) | P0 | ⬜ Todo | Legacy |
| P4-COR148 | __init__ (AudioSystem) | P0 | ⬜ Todo | Legacy |
| P4-COR149 | node_effect_audio (AudioTrailsNode) | P0 | ⬜ Todo | Legacy |
| P4-COR150 | audio_waveform_distortion (AudioWaveformDistortion) | P0 | ⬜ Todo | Legacy |
| P4-COR151 | websocket_handler (AudioWebSocketHandler) | P0 | ⬜ Todo | Legacy |
| P4-COR152 | depth_audio (DepthAudioMapping) | P0 | ⬜ Todo | Legacy |
| P4-COR153 | depth_audio (DepthAudioReactor) | P0 | ⬜ Todo | Legacy |
| P4-COR154 | audio_reactive_effects (DreamModeEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR155 | audio_reactive_effects (EnergyCascadeEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR156 | audio_reactive (EnvelopeFollower) | P0 | ⬜ Todo | Legacy |
| P4-COR157 | audio_reactive_effects (KaleidoscopeEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR158 | pll_sync (MIDIClockSync) | P0 | ⬜ Todo | Legacy |
| P4-COR159 | config_types (MIDIConfig) | P0 | ⬜ Todo | Legacy |
| P4-COR160 | unified_hydra_extensions (MIDIHydraExtension) | P0 | ⬜ Todo | Legacy |
| P4-COR161 | midi_controller (MIDIMapping) | P0 | ⬜ Todo | Legacy |
| P4-COR162 | midi (MIDIMessage) | P0 | ⬜ Todo | Legacy |
| P4-COR163 | midi (MIDIMessageType) | P0 | ⬜ Todo | Legacy |
| P4-COR164 | midi_controller (MIDIMode) | P0 | ⬜ Todo | Legacy |
| P4-COR165 | midi_presets (MIDIPresetManager) | P0 | ⬜ Todo | Legacy |
| P4-COR166 | midi_mapper (MidiMapper) | P0 | ⬜ Todo | Legacy |
| P4-COR167 | midi_mapper (MidiMapping) | P0 | ⬜ Todo | Legacy |
| P4-COR168 | matrix_nodes (MidiToParamNode) | P0 | ⬜ Todo | Legacy |
| P4-COR169 | config_types (OSCConfig) | P0 | ⬜ Todo | Legacy |
| P4-COR170 | osc_controller (OSCController) | P0 | ⬜ Todo | Legacy |
| P4-COR171 | osc_dispatcher (OSCDispatcher) | P0 | ⬜ Todo | Legacy |
| P4-COR172 | osc_query_server (OSCQueryHTTPRequestHandler) | P0 | ⬜ Todo | Legacy |
| P4-COR173 | osc_query_server (OSCQueryParameter) | P0 | ⬜ Todo | Legacy |
| P4-COR174 | osc_query_server (OSCQueryServer) | P0 | ⬜ Todo | Legacy |
| P4-COR175 | audio_reactive (OnsetDetector) | P0 | ⬜ Todo | Legacy |
| P4-COR176 | generators (OscEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR177 | oscilloscope (OscilloscopeEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR178 | node_effect_lost_artifacts (OscilloscopeNode) | P0 | ⬜ Todo | Legacy |
| P4-COR179 | matrix_nodes (ParamToMidiNode) | P0 | ⬜ Todo | Legacy |
| P4-COR180 | quantum_analyzer (QuantumAudioAnalyzer) | P0 | ⬜ Todo | Legacy |
| P4-COR181 | quantum_reactor (QuantumAudioReactor) | P0 | ⬜ Todo | Legacy |
| P4-COR182 | audio_reactive (SpectralColorMapper) | P0 | ⬜ Todo | Legacy |
| P4-COR183 | audio_reactive_3d_scene_ultimate (TimeTravelSession) | P0 | ⬜ Todo | Legacy |
| P4-COR184 | audio_reactive_effects (VHSScanlinesEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR185 | av_mixer (VideoAudioMixerModule) | P0 | ⬜ Todo | Legacy |
| P4-COR186 | audio_reactive_3d_scene_ultimate (WorldMemory) | P0 | ⬜ Todo | Legacy |
| P4-COR187 | video_sources (AstraDepthSource) | P0 | ⬜ Todo | Legacy |
| P4-COR188 | astra_linux (AstraLinuxSource) | P0 | ⬜ Todo | Legacy |
| P4-COR189 | astra_native (AstraNativeSource) | P0 | ⬜ Todo | Legacy |
| P4-COR190 | vision_source (AstraSource) | P0 | ⬜ Todo | Legacy |
| P4-COR191 | camera (Camera3D) | P0 | ⬜ Todo | Legacy |
| P4-COR192 | multi_camera_manager (CameraCalibration) | P0 | ⬜ Todo | Legacy |
| P4-COR193 | camera_config_manager (CameraConfigManager) | P0 | ⬜ Todo | Legacy |
| P4-COR194 | multi_camera_fusion (CameraPose) | P0 | ⬜ Todo | Legacy |
| P4-COR195 | camera_profiles_new (CameraProfile) | P0 | ⬜ Todo | Legacy |
| P4-COR196 | camera_profiles_new (CameraProfileConfig) | P0 | ⬜ Todo | Legacy |
| P4-COR197 | camera_profiles_new (CameraProfileManager) | P0 | ⬜ Todo | Legacy |
| P4-COR198 | camera_profiles (CameraType) | P0 | ⬜ Todo | Legacy |
| P4-COR199 | dmx_bridge (DMXBridge) | P0 | ⬜ Todo | Legacy |
| P4-COR200 | lighting_bridge (DMXChannel) | P0 | ⬜ Todo | Legacy |
| P4-COR201 | dmx_engine (DMXEngine) | P0 | ⬜ Todo | Legacy |
| P4-COR202 | dmx_input (DMXInputController) | P0 | ⬜ Todo | Legacy |
| P4-COR203 | dmx_input (DMXInputUniverse) | P0 | ⬜ Todo | Legacy |
| P4-COR204 | sacn_monitor (DMXMonitor) | P0 | ⬜ Todo | Legacy |
| P4-COR205 | dmx_production_ws_handler (DMXProductionWSHandler) | P0 | ⬜ Todo | Legacy |
| P4-COR206 | dmx_bridge (DMXScene) | P0 | ⬜ Todo | Legacy |
| P4-COR207 | dmx_input (DMXShortcut) | P0 | ⬜ Todo | Legacy |
| P4-COR208 | lighting_bridge (DMXUniverse) | P0 | ⬜ Todo | Legacy |
| P4-COR209 | dmx_ws_handler (DMXWSHandler) | P0 | ⬜ Todo | Legacy |
| P4-COR210 | depth_calibration (DepthCameraCalibration) | P0 | ⬜ Todo | Legacy |
| P4-COR211 | accelerator (HardwareAccelerator) | P0 | ⬜ Todo | Legacy |
| P4-COR212 | vjlivest_license_system (HardwareBinding) | P0 | ⬜ Todo | Legacy |
| P4-COR213 | accelerator (HardwareCapabilities) | P0 | ⬜ Todo | Legacy |
| P4-COR214 | hardware_discovery (HardwareDiscovery) | P0 | ⬜ Todo | Legacy |
| P4-COR215 | hardware_hal (HardwareHAL) | P0 | ⬜ Todo | Legacy |
| P4-COR216 | hardware_scanner (HardwareIdentity) | P0 | ⬜ Todo | Legacy |
| P4-COR217 | app (HardwareIntegration) | P0 | ⬜ Todo | Legacy |
| P4-COR218 | hardware_manager (HardwareManager) | P0 | ⬜ Todo | Legacy |
| P4-COR219 | hardware_manifest (HardwareManifest) | P0 | ⬜ Todo | Legacy |
| P4-COR220 | hardware_manifest (HardwareManifestManager) | P0 | ⬜ Todo | Legacy |
| P4-COR221 | hardware_mapper (HardwareMapper) | P0 | ⬜ Todo | Legacy |
| P4-COR222 | hardware_mapper (HardwareMapping) | P0 | ⬜ Todo | Legacy |
| P4-COR223 | hardware (HardwareMixin) | P0 | ⬜ Todo | Legacy |
| P4-COR224 | hardware_report (HardwareReportGenerator) | P0 | ⬜ Todo | Legacy |
| P4-COR225 | hardware_scanner (HardwareScanner) | P0 | ⬜ Todo | Legacy |
| P4-COR226 | network (IPCameraSource) | P0 | ⬜ Todo | Legacy |
| P4-COR227 | hotplug_detector (MacVDCameraDetector) | P0 | ⬜ Todo | Legacy |
| P4-COR228 | multi_camera_fusion (MultiCameraFusion) | P0 | ⬜ Todo | Legacy |
| P4-COR229 | multi_camera_manager (MultiCameraManager) | P0 | ⬜ Todo | Legacy |
| P4-COR230 | vision_source (NDIVisionSource) | P0 | ⬜ Todo | Legacy |
| P4-COR231 | camera (PhysicalCameraSource) | P0 | ⬜ Todo | Legacy |
| P4-COR232 | video_sources_realsense (RealSenseConfig) | P0 | ⬜ Todo | Legacy |
| P4-COR233 | realsense (RealSenseSource) | P0 | ⬜ Todo | Legacy |
| P4-COR234 | silver_visions (SilverVisionsEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR235 | node_datamosh (TunnelVisionNode) | P0 | ⬜ Todo | Legacy |
| P4-COR236 | vision_source (UVCVisionSource) | P0 | ⬜ Todo | Legacy |
| P4-COR237 | vision_source (VisionBackend) | P0 | ⬜ Todo | Legacy |
| P4-COR238 | vision_source (VisionMetadata) | P0 | ⬜ Todo | Legacy |
| P4-COR239 | vision_node (VisionNode) | P0 | ⬜ Todo | Legacy |
| P4-COR240 | vision_source (VisionSource) | P0 | ⬜ Todo | Legacy |
| P4-COR241 | vision_watchdog (VisionWatchdog) | P0 | ⬜ Todo | Legacy |
| P4-COR242 | befaco (ADSR) | P0 | ⬜ Todo | Legacy |
| P4-COR243 | node_modulation_befaco (ADSRNode) | P0 | ⬜ Todo | Legacy |
| P4-COR244 | arvr_modules (ARCanvas) | P0 | ⬜ Todo | Legacy |
| P4-COR245 | arvr_modules (ARController) | P0 | ⬜ Todo | Legacy |
| P4-COR246 | arvr_modules (ARScene) | P0 | ⬜ Todo | Legacy |
| P4-COR247 | engine (ARVRMode) | P0 | ⬜ Todo | Legacy |
| P4-COR248 | engine (ARVRPipeline) | P0 | ⬜ Todo | Legacy |
| P4-COR249 | ascii (ASCIIEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR250 | node_effect_omniverse (ASCIINode) | P0 | ⬜ Todo | Legacy |
| P4-COR251 | decoder (AVDecoder) | P0 | ⬜ Todo | Legacy |
| P4-COR252 | accelerator (AccelerationMode) | P0 | ⬜ Todo | Legacy |
| P4-COR253 | secure_vault (AccessControl) | P0 | ⬜ Todo | Legacy |
| P4-COR254 | secure_vault (AccessPolicy) | P0 | ⬜ Todo | Legacy |
| P4-COR255 | security_manager (AccessToken) | P0 | ⬜ Todo | Legacy |
| P4-COR256 | gamification (Achievement) | P0 | ⬜ Todo | Legacy |
| P4-COR257 | awesome_collaborative_creation (AchievementCategory) | P0 | ⬜ Todo | Legacy |
| P4-COR258 | awesome_collaborative_creation (AchievementSystem) | P0 | ⬜ Todo | Legacy |
| P4-COR259 | gamification (AchievementType) | P0 | ⬜ Todo | Legacy |
| P4-COR260 | rhythm_visual_effects (ActiveBeatEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR261 | intelligent_visual_response (ActiveEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR262 | collaboration (ActivityHeatmapPoint) | P0 | ⬜ Todo | Legacy |
| P4-COR263 | adaptive_config (AdaptationStrategy) | P0 | ⬜ Todo | Legacy |
| P4-COR264 | brush_engines (AdaptiveBrushStroke) | P0 | ⬜ Todo | Legacy |
| P4-COR265 | vcv_effects (AdaptiveContrastEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR266 | video_buffer_manager (AdaptiveQualityScaler) | P0 | ⬜ Todo | Legacy |
| P4-COR267 | adaptive_resolution (AdaptiveResolutionController) | P0 | ⬜ Todo | Legacy |
| P4-COR268 | models (AdminUser) | P0 | ⬜ Todo | Legacy |
| P4-COR269 | routes (AdminUserCreate) | P0 | ⬜ Todo | Legacy |
| P4-COR270 | routes (AdminUserResponse) | P0 | ⬜ Todo | Legacy |
| P4-COR271 | advanced_output (AdvancedOutputEngine) | P0 | ⬜ Todo | Legacy |
| P4-COR272 | particles_3d (AdvancedParticle3DSystem) | P0 | ⬜ Todo | Legacy |
| P4-COR273 | enhanced_collaboration_effects (AdvancedParticlePhysics) | P0 | ⬜ Todo | Legacy |
| P4-COR274 | error_tracking (AlertManager) | P0 | ⬜ Todo | Legacy |
| P4-COR275 | node_effect_analog (AnalogBlurNode) | P0 | ⬜ Todo | Legacy |
| P4-COR276 | node_effect_analog (AnalogColorNode) | P0 | ⬜ Todo | Legacy |
| P4-COR277 | node_effect_analog (AnalogContrastNode) | P0 | ⬜ Todo | Legacy |
| P4-COR278 | node_effect_analog (AnalogEchoNode) | P0 | ⬜ Todo | Legacy |
| P4-COR279 | node_effect_analog (AnalogHDRNode) | P0 | ⬜ Todo | Legacy |
| P4-COR280 | unified_effects (AnalogPulse) | P0 | ⬜ Todo | Legacy |
| P4-COR281 | node_effect_analog (AnalogResonantNode) | P0 | ⬜ Todo | Legacy |
| P4-COR282 | node_effect_analog (AnalogSolarizeNode) | P0 | ⬜ Todo | Legacy |
| P4-COR283 | analog_tv (AnalogTVEffect) | P0 | ⬜ Todo | Legacy |
| P4-COR284 | node_effect_omniverse (AnalogTVNode) | P0 | ⬜ Todo | Legacy |
| P4-COR285 | node_effect_analog (AnalogZoomNode) | P0 | ⬜ Todo | Legacy |
| P4-COR286 | anchor_evolution (AnchorEvolution) | P0 | ⬜ Todo | Legacy |
| P4-COR287 | ui_enhancements (Animation) | P0 | ⬜ Todo | Legacy |
| P4-COR288 | ui_enhancements (AnimationType) | P0 | ⬜ Todo | Legacy |
| P4-COR289 | ai_assistant (Anomaly) | P0 | ⬜ Todo | Legacy |
| P4-COR290 | predictive_failure_detection (AnomalyDetector) | P0 | ⬜ Todo | Legacy |
| P4-COR291 | anthropic_provider (AnthropicModelProvider) | P0 | ⬜ Todo | Legacy |
| P4-COR292 | llm_service (AnthropicProvider) | P0 | ⬜ Todo | Legacy |
| P4-COR293 | brush_engines (AntigravityBrush) | P0 | ⬜ Todo | Legacy |
| P4-COR294 | bootstrap (AppInitializer) | P0 | ⬜ Todo | Legacy |
| P4-COR295 | application_metrics (ApplicationMetrics) | P0 | ⬜ Todo | Legacy |
| P4-COR296 | arbhar_granularizer (ArbharGranularizer) | P0 | ⬜ Todo | Legacy |
| P4-COR297 | intelligent_documentation (ArchitectureGenerator) | P0 | ⬜ Todo | Legacy |
| P4-COR298 | memory_pool (ArrayPool) | P0 | ⬜ Todo | Legacy |
| P4-COR299 | collaborative_canvas (ArtGallery) | P0 | ⬜ Todo | Legacy |
| P4-COR300 | lighting_bridge (ArtNetController) | P0 | ⬜ Todo | Legacy |

> Note: Only the first 300 features are listed here to keep the board manageable. See `WORKSPACE/COMMS/STATUS/CORE_LOGIC_PARITY.md` for the remaining ~1500 items.


---

## Phase 1: Foundation & Rendering (Weeks 1-4) 🔴 RESET — Code wiped. Must read legacy FIRST before rewriting.

### 1A — Core Infrastructure

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-R1 | OpenGL rendering context (ModernGL) | P0 | ✅ Done | `src/vjlive3/render/opengl_context.py` — OpenGLContext, 10/10 tests ✅ |
| P1-R2 | GPU pipeline + framebuffer management (RAII) | P0 | ✅ Done | `chain.py`, `program.py`, `framebuffer.py` - tests pass, 82% coverage ✅ |
| P1-R3 | Shader compilation system (GLSL + Milkdrop) | P0 | ✅ Done | `src/vjlive3/render/shader_compiler.py` — 7 tests @ 81% cov ✅ — 2026-02-22 |
| P1-R4 | Texture manager (pooled, leak-free) | [Agent name] | ✅ Done | 80% coverage mapped across ModernGL dictionary buffers and fallback decoded stream paths. (2026-02-22) |
| P1-R5 | Core rendering engine (60fps loop) | P0 | ✅ Done | `src/vjlive3/render/engine.py` — RenderEngine, 8/8 tests ✅ 2026-02-22 |

### 1B — Audio Engine

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-A1 | FFT + waveform analysis engine | P0 | 🔄 In Progress | `docs/specs/P1-A1_audio_analyzer.md` — spec approved, implementation started |
| P1-A2 | Real-time beat detection | P0 | 🔄 In Progress | `docs/specs/P1-A2_beat_detector.md` — spec approved, implementation started |
| P1-A3 | Audio-reactive effect framework | P0 | 🔄 In Progress | `docs/specs/P1-A3_reactivity_bus.md` — spec approved, implementation started |
| P1-A4 | Multi-source audio input | P1 | 🔄 In Progress | `docs/specs/P1-A4_audio_sources.md` — spec approved, implementation started |

### 1C — Node Graph / Matrix

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-N1 | UnifiedMatrix + node registry (manifest-based) | P0 | 🔄 In Progress | `docs/specs/P1-N1_node_registry.md` — spec approved, implementation started |
| P1-N2 | Node types — full collection from both codebases | P0 | 🔄 In Progress | `docs/specs/P1-N2_node_types.md` — spec approved, implementation started |
| P1-N3 | State persistence (save/load) | P1 | 🔄 In Progress | `docs/specs/P1-N3_state_persistence.md` — spec approved, implementation started |
| P1-N4 | Visual node graph UI | P1 | 🔄 In Progress | `docs/specs/P1-N4_node_graph_ui.md` — spec approved, implementation started |

### 1D — Plugin System

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-P1 | Plugin registry (manifest.json based) | P0 | ✅ Done | `src/vjlive3/plugins/registry.py` — 108 tests @ 81.62% cov — 2026-02-21 |
| P1-P2 | Plugin loading + Pydantic validation | P0 | ✅ Done | `src/vjlive3/plugins/loader.py` — included in test suite |
| P1-P3 | Hot-reloadable plugin system | P0 | 🔄 In Progress | `docs/specs/P1-P3_plugin_hot_reload.md` — spec approved, implementation started |
| P1-P4 | Plugin discovery (auto-scan) | P0 | 🔄 In Progress | `docs/specs/P1-P4_plugin_scanner.md` — spec approved, implementation started |
| P1-P5 | Plugin sandboxing | P1 | 🔄 In Progress | `docs/specs/P1-P5_plugin_sandbox.md` — spec approved, implementation started |

**Phase 1 Gate:** FPS ≥ 58. Window visible. Empty node graph renders. Plugin loads successfully.

---

## Phase 2: Critical Infrastructure Ports (Weeks 5-8) 🔴 RESET — Code wiped, restart with SPEC first
> Features in vjlive with no equivalent in VJlive-2. Block all plugin work until done.

### 2A — DMX System (MISSING from VJlive-2 — CRITICAL)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P2-D1 | DMX512 core engine + fixture profiles | P0 | ✅ Done | Spec ready: `docs/specs/P2-D1_dmx_engine.md` |
| P2-D2 | ArtNet + sACN output | P0 | ✅ Done | Spec ready: `docs/specs/P2-D2_artnet_output.md` |
| P2-D3 | DMX FX engine (chases, rainbow, strobe) | P0 | ✅ Done | Spec ready: `docs/specs/P2-D3_dmx_fx.md` |
| P2-D4 | Show control system | P1 | ✅ Done | Spec ready: `docs/specs/P2-D4_show_control.md` |
| P2-D5 | Audio-reactive DMX | P1 | ✅ Done | `src/vjlive3/core/dmx/audio_dmx.py` — AudioDmxLink, 5/5 tests ✅ 2026-02-22 |
| P2-D6 | DMX WebSocket handler | P1 | ✅ Done | `src/vjlive3/core/dmx/websocket.py` — DmxWebSocketHandler, 7/7 tests ✅ 2026-02-22 |

### 2. Phase 2: Hardware & External IO 🔌

| Task ID | Task Name | Priority | Status | Verification Checkpoint |
|---|---|---|---|---|
| P2-H1 | MIDI controller input | P0 | ✅ Done | `src/vjlive3/core/midi_controller.py` — MidiController, 9/9 tests ✅ 2026-02-22 |
| P2-H2 | Audio reactive input analysis block | P0 | ✅ Done | `src/vjlive3/audio/...` — Audio Analyzer Pipeline Active |OscClient, 20/20 tests ✅ 2026-02-21 |
| P2-H3 | Orbbec Astra / Kinect 2 Depth Camera | P1 | ✅ Done | `src/vjlive3/plugins/astra.py` — AstraDepthCamera, 5/5 tests ✅ 2026-02-22 |
| P2-H4 | NDI video transport (full hub + streams) | P1 | ✅ Done | `src/vjlive3/plugins/ndi.py` — NDIHub/NDISender/NDIReceiver, 9/9 tests ✅ 2026-02-22 |
| P2-H5 | Spout support (Windows video sharing) | P2 | ✅ Done | `src/vjlive3/plugins/spout.py` — SpoutManager, 5/5 tests ✅ 2026-02-22 |
| P2-H6 | Gamepad input (GLFW backend) | P2 | ✅ Done | `src/vjlive3/plugins/gamepad.py` — GamepadPlugin, 4/4 tests ✅ 2026-02-22 |
| P2-H7 | Laser safety system | P1 | ✅ Done | `src/vjlive3/hardware/laser.py` — LaserSafetySystem, 8/8 tests ✅ 2026-02-22 |

### 2C — Distributed Architecture (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P2-X1 | Multi-node coordination (ZeroMQ) | P0 | ✅ Done | `src/vjlive3/sync/zmq_coordinator.py` — ZmqCoordinator, 4/4 tests ✅ 2026-02-22 |
| P2-X2 | Timecode sync (LTC/MTC/NTP) | P0 | ✅ Done | `src/vjlive3/sync/timecode.py` — TimecodeEngine + sources, 28/28 tests ✅ 2026-02-21 |
| P2-X3 | Output mapping + screen warping | P1 | ✅ Done | `src/vjlive3/video/output_mapper.py` — OutputMapper, 6/6 tests ✅ 2026-02-22 |
| P2-X4 | Projection mapping (warp, edge-blend, mask) | P1 | ✅ Done | `src/vjlive3/video/projection_mapper.py` — ProjectionMapper, 4/4 tests ✅ 2026-02-22 |

**Phase 2 Gate:** DMX test signal works. MIDI input registers. Hardware-absent fails gracefully.

---

## Phase 3: Effects — Depth Collection (Weeks 5-10)
> vjlive has a massive depth plugin collection. VJlive-2 has a partial set. Port ALL Depth Plugins artisanally.

### 3A — Missing Depth Plugins (from vjlive/vdepth/ — audit individually, every plugin is unique)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P3-VD7 | Depth Data Mux (DepthDataMuxEffect) | P0 | ✅ Done | `src/vjlive3/plugins/p3_vd7.py` — DepthDataMuxEffect, 8/8 tests ✅ 2026-02-22 |
| P3-VD-Beta1 | Depth Loop Injection (DepthLoopInjectionPlugin) | P0 | ✅ Done | `src/vjlive3/plugins/p3_vd_beta1.py` — DepthLoopInjectionPlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD-Beta2 | Depth Parallel Universe (DepthParallelUniversePlugin) | P0 | ✅ Done | `src/vjlive3/plugins/p3_vd_beta2.py` — DepthParallelUniversePlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD-Beta3 | Depth Portal Composite (DepthPortalCompositePlugin) | P0 | ✅ Done | `src/vjlive3/plugins/p3_vd_beta3.py` — DepthPortalCompositePlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD-Beta4 | Depth Neural Quantum Hyper Tunnel (DepthNeuralQuantumHyperTunnelPlugin) | P0 | ✅ Done | `src/vjlive3/plugins/p3_vd_beta4.py` — DepthNeuralQuantumHyperTunnelPlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD-Beta5 | Depth Reality Distortion (RealityDistortionPlugin) | P0 | ✅ Done | `src/vjlive3/plugins/p3_vd_beta5.py` — RealityDistortionPlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD33 | Depth Distance Filter (DepthDistanceFilterPlugin) | P0 | ✅ Done | `src/vjlive3/plugins/p3_vd33.py` — DepthDistanceFilterPlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD34 | Depth Dual (DepthDualPlugin) | P0 | ✅ Done | `src/vjlive3/plugins/p3_vd34.py` — DepthDualPlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD35 | Depth Edge Glow (DepthEdgeGlowPlugin) | P0 | ✅ Done | `src/vjlive3/plugins/p3_vd35.py` — DepthEdgeGlowPlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD36 | Depth Effects (DepthEffectPlugin) | P0 | ✅ Done | `src/vjlive3/plugins/p3_vd36.py` — DepthEffectPlugin, 8/8 tests ✅ 2026-02-22 |
----------|-------------|----------|--------|--------|
| P3-VD26 | Depth Acid Fractal (DepthAcidFractalDatamoshEffect) | P0 | ✅ Done | Implemented |
| P3-VD27 | Depth Aware Compression (DepthAwareCompressionEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD28 | Depth Blur (DepthBlurEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD29 | Depth Camera Splitter (DepthCameraSplitterEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD30 | Depth Color Grade (DepthColorGradeEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD31 | Depth Contour Datamosh (DepthContourDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD32 | Depth Data Mux (DepthDataMuxEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD33 | Depth Distance Filter (DepthDistanceFilterEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD34 | Depth Dual (DepthDualEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD35 | Depth Edge Glow (DepthEdgeGlowEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD36 | Depth Effects (DepthEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD37 | Depth Effects (DepthPointCloudEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD38 | Depth Effects (DepthPointCloud3DEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD39 | Depth Effects (DepthMeshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD40 | Depth Effects (DepthContourEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD41 | Depth Effects (DepthParticle3DEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD42 | Depth Effects (DepthDistortionEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD43 | Depth Effects (DepthFieldEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD44 | Depth Effects (OpticalFlowEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD45 | Depth Effects (BackgroundSubtractionEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD46 | Depth Erosion Datamosh (DepthErosionDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD47 | Depth Feedback Matrix Datamosh (DepthFeedbackMatrixDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD48 | Depth Fog (DepthFogEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD49 | Depth Fracture Datamosh (DepthFractureDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD50 | Depth Fx Loop (DepthFXLoopEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD51 | Depth Groovy Datamosh (DepthGroovyDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD52 | Depth Holographic (DepthHolographicIridescenceEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD53 | Depth Liquid Refraction (DepthLiquidRefractionEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD54 | Depth Loop Injection Datamosh (DepthLoopInjectionDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD55 | Depth Modular Datamosh (DepthModularDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD56 | Depth Modulated Datamosh (DepthModulatedDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD57 | Depth Mosaic (DepthMosaicEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD58 | Depth Mosh Nexus (DepthMoshNexus) | P0 | ◯ Todo | VJlive-2 |
| P3-VD59 | Depth Motion Transfer (DepthMotionTransferEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD60 | Depth Parallel Universe Datamosh (DepthParallelUniverseDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD61 | Depth Particle Shred (DepthParticleShredEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD62 | Depth Portal Composite (DepthPortalCompositeEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD63 | Depth Raver Datamosh (DepthRaverDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD64 | Depth Reverb (DepthReverbEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD65 | Depth Simulator (DepthSimulatorEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD66 | Depth Slitscan Datamosh (DepthSlitScanDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD67 | Depth Temporal Echo (DepthTemporalEchoEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD68 | Depth Temporal Strat (DepthTemporalStratEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD69 | Depth Vector Field Datamosh (DepthVectorFieldDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD70 | Depth Video Projection (DepthVideoProjectionEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD71 | Depth Void Datamosh (DepthVoidDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD72 | datamosh_3d (DepthDisplacementEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD73 | datamosh_3d (DepthEchoEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD74 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | ◯ Todo | VJlive-2 |
| P3-VD75 | quantum_depth_nexus_effect (QuantumDepthNexus) | P0 | ◯ Todo | VJlive-2 |



### 3B — Existing Depth Plugins (in VJlive-2 — verify quality, keep or improve)
Depth Modulated, Depth Edge Glow, Depth Color Grade, Depth Erosion, Depth Fracture,
Depth Modular, Depth Slitscan, Depth Void, Depth Particle Shred, Depth Motion Transfer,
Depth Feedback Matrix, Depth Holographic, and any others present — **every one gets bespoke review**

**Phase 3 Gate:** Full depth collection loads. Each tested against Astra input. No plugin left behind.

---

## Phase 4: Effects — Audio Plugin Collection (Weeks 7-10)
> Both codebases contain audio-reactive plugins. Port ALL from vjlive that are missing in VJlive-2. Verify and keep all that exist in VJlive-2.

### 4A — Bogaudio Collection (MISSING from VJlive-2)

| Task ID | Plugin | Status |
|---------|--------|--------|
| P4-BA01 | B1to8 | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA01_B1to8.md` — spec approved |
| P4-BA02 | BLFO | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA02_BLFO.md` — spec approved |
| P4-BA03 | BMatrix81 | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA03_BMatrix81.md` — spec approved |
| P4-BA04 | BPEQ6 | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA04_BPEQ6.md` — spec approved |
| P4-BA05 | BSwitch | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA05_BSwitch.md` — spec approved |
| P4-BA06 | BVCF | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA06_BVCF.md` — spec approved |
| P4-BA07 | BVCO | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA07_BVCO.md` — spec approved |
| P4-BA08 | BVELO | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA08_BVELO.md` — spec approved |
| P4-BA09 | NMix4 | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA09_NMix4.md` — spec approved |
| P4-BA10 | NXFade | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA10_NXFade.md` — spec approved |

### 4D — Audio Reactive (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P4-AU02 | Audio Reactive Effects (AudioParticleSystem) | P0 | ◯ Todo | VJlive-2 |
| P4-AU03 | Audio Reactive Effects (AudioWaveformDistortion) | P0 | ◯ Todo | VJlive-2 |
| P4-AU04 | Audio Reactive Effects (AudioSpectrumTrails) | P0 | ◯ Todo | VJlive-2 |
| P4-AU05 | Audio Reactive Effects (AudioKaleidoscope) | P0 | ◯ Todo | VJlive-2 |
| P4-AU06 | cosmic_tunnel_datamosh (CosmicTunnelDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P4-AU07 | raymarched_scenes (AudioReactiveRaymarchedScenes) | P0 | ◯ Todo | VJlive-2 |
| P4-AU08 | vcv_video_generators (ByteBeatGen) | P0 | ◯ Todo | VJlive-2 |

### 4B — Befaco Modulators (MISSING from VJlive-2)

| Task ID | Plugin | Status |
|---------|--------|--------|
| P4-BF01 | V-Even | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF01_V-Even.md` — spec approved |
| P4-BF02 | V-Morphader | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF02_V-Morphader.md` — spec approved |
| P4-BF03 | V-Outs | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF03_V-Outs.md` — spec approved |
| P4-BF04 | V-Pony | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF04_V-Pony.md` — spec approved |
| P4-BF05 | V-Scope | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF05_V-Scope.md` — spec approved |
| P4-BF06 | V-Voltio | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF06_V-Voltio.md` — spec approved |

### 4C — Audio Reactive (in VJlive-2 — verify + keep + extend)
Audio Reactive 3D, Audio Waveform Distortion, Audio Kaleidoscope, Audio Particle System, and all others present — audit vjlive for any additional audio-reactive plugins not yet in VJlive-2.

**Phase 4 Gate:** Full audio plugin collection loaded. All modules respond to live audio. Beat detection drives them.

---

## Phase 5: Effects — Modulators & V-* Collection (Weeks 11-13)

### 5A — Modulators (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P5-MO03 | blend (ModulateEffect) | P0 | ◯ Todo | VJlive-2 |

### 5B — V-* Visual Effects (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P5-VE02 | analog_tv (AnalogTVEffect) | P0 | ◯ Todo | VJlive-2 |

### 5C — Modulators (already in VJlive-2 — keep)
V-Maths, V-Frames, V-Grids, V-Harmonaig, V-LXD, V-Marbles, V-Roots, V-Stages Segment, V-Tides

### 5D — Datamosh Family (verify both sources, keep VJlive-2's cleaner impl)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P5-DM02 | bad_trip_datamosh (BadTripDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM03 | bass_cannon_datamosh (BassCannonDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM04 | bass_therapy_datamosh (BassTherapyDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM05 | blend (GlitchEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM06 | bullet_time_datamosh (BulletTimeDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM07 | cellular_automata_datamosh (CellularAutomataDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM08 | cotton_candy_datamosh (CottonCandyDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM09 | cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM10 | datamosh (CompressionEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM11 | datamosh (DatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM12 | datamosh (PixelBloomEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM13 | datamosh (MeltEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM14 | datamosh (PixelSortEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM15 | datamosh (FrameHoldEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM16 | datamosh_3d (Datamosh3DEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM17 | datamosh_3d (LayerSeparationEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM18 | datamosh_3d (ShatterEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM19 | dimension_splice_datamosh (DimensionSpliceDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM20 | dolly_zoom_datamosh (DollyZoomDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM21 | face_melt_datamosh (FaceMeltDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM22 | fracture_rave_datamosh (FractureRaveDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM23 | liquid_lsd_datamosh (LiquidLSDDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM24 | mosh_pit_datamosh (MoshPitDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM25 | neural_splice_datamosh (NeuralSpliceDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM26 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM27 | plasma_melt_datamosh (PlasmaMeltDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM28 | prism_realm_datamosh (PrismRealmDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM29 | sacred_geometry_datamosh (SacredGeometryDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM30 | spirit_aura_datamosh (SpiritAuraDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM31 | temporal_rift_datamosh (TemporalRiftDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM32 | tunnel_vision_datamosh (TunnelVisionDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM33 | unicorn_farts_datamosh (UnicornFartsDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM34 | void_swirl_datamosh (VoidSwirlDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM35 | volumetric_datamosh (VolumetricDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM36 | volumetric_glitch (VolumetricGlitchEffect) | P0 | ◯ Todo | VJlive-2 |

## Phase 6: AI, Quantum, Generators & Particle Systems (Weeks 15-16)

### 6A — AI / Neural Systems (VJlive-2 leads)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|

### 6B — Quantum Consciousness (VJlive-2 leads)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P6-QC06 | agent_avatar (TravelingAvatarEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC07 | agent_avatar (AgentAvatarEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC08 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC09 | ml_gpu_effects (MLStyleGLEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC10 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC11 | neural_rave_nexus (NeuralRaveNexus) | P0 | ◯ Todo | VJlive-2 |
| P6-QC12 | quantum_consciousness_explorer (QuantumConsciousnessExplorer) | P0 | ◯ Todo | VJlive-2 |
| P6-QC13 | trails (TrailsEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC14 | tunnel_vision_3 (QuantumConsciousnessSingularityEffect) | P0 | ◯ Todo | VJlive-2 |

### 6C — Agent System

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P6-AG1 | Agent Bridge | P0 | ◯ Todo | VJlive-2 arch + vjlive physics |
| P6-AG2 | Agent Physics — 16D manifold + gravity wells | P0 | ◯ Todo | vjlive only |
| P6-AG3 | Agent Memory (50-snapshot system) | P0 | ◯ Todo | vjlive only |
| P6-AG4 | Agent Control UI | P0 | ◯ Todo | Both |

### 6D — Generators (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P6-GE06 | fractal_generator (FractalGenerator) | P0 | ◯ Todo | VJlive-2 |
| P6-GE07 | generators (OscEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE08 | generators (NoiseEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE09 | generators (VoronoiEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE10 | generators (GradientEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE11 | generators (MandalaEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE12 | generators (PlasmaEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE13 | generators (PerlinEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE14 | silver_visions (PathGeneratorEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE15 | vcv_video_generators (HarmonicPatternsGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE16 | vcv_video_generators (FMCoordinatesGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE17 | vcv_video_generators (MacroShapeGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE18 | vcv_video_generators (GranularVideoGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE19 | vcv_video_generators (ResonantGeometryGen) | P0 | ◯ Todo | VJlive-2 |

### 6E — Particle/3D (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P6-P302 | particles_3d (AdvancedParticle3DSystem) | P0 | ◯ Todo | VJlive-2 |
| P6-P303 | particles_3d (Particle3DSystem) | P0 | ◯ Todo | VJlive-2 |
| P6-P304 | shadertoy_particles (ShadertoyParticles) | P0 | ◯ Todo | VJlive-2 |
| P6-P305 | vibrant_retro_styles (RadiantMeshEffect) | P0 | ◯ Todo | VJlive-2 |

## Phase 7: UI, Business & Additional Effects (Weeks 17-18)

### 7A — User Interface

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P7-U1 | Desktop GUI + SentienceOverlay easter egg | P0 | ◯ Todo | VJlive-2 |
| P7-U2 | Web-based remote control | P0 | ◯ Todo | VJlive-2 |
| P7-U3 | Collaborative Studio UI | P0 | ◯ Todo | VJlive-2 only |
| P7-U4 | Quantum Collaborative Studio | P0 | ◯ Todo | VJlive-2 only |
| P7-U5 | TouchOSC export / mobile interface | P0 | ◯ Todo | vjlive |
| P7-U6 | CLI automation | P0 | ◯ Todo | VJlive-2 |

### 7B — Business / Licensing

### 7C — Additional Effects & Utilities (VJlive-2 + vjlive synthesis)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P7-VE01 | V Sws (VSwsEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE02 | V Sws (HorizontalWaveEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE03 | V Sws (VerticalWaveEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE04 | V Sws (RippleEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE05 | V Sws (SpiralWaveEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE06 | ascii_effect (ASCIIEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE07 | bass_cannon_2 (BassCanon2) | P0 | ◯ Todo | VJlive-2 |
| P7-VE08 | blend (FeedbackEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE09 | blend (BlendAddEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE10 | blend (BlendMultEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE11 | blend (BlendDiffEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE12 | blend (ScanlinesEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE13 | blend (VignetteEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE14 | blend (InfiniteFeedbackEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE15 | blend (BloomEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE16 | blend (BloomShadertoyEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE17 | blend (MixerEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE18 | blend_modes (_BlendMode) | P0 | ◯ Todo | VJlive-2 |
| P7-VE19 | chroma_key (ChromaKeyEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE20 | color (PosterizeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE21 | color (ContrastEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE22 | color (SaturateEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE23 | color (HueEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE24 | color (BrightnessEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE25 | color (InvertEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE26 | color (ThreshEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE27 | color (RGBShiftEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE28 | color (ColorCorrectEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE29 | color_grade (ColorGradeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE30 | colorama (ColoramaEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE31 | displacement_map (DisplacementMapEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE32 | distortion (ChromaticDistortionEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE33 | distortion (PatternDistortionEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE34 | dithering (DitheringEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE35 | fluid_sim (FluidSimEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE36 | geometry (MandalascopeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE37 | geometry (RotateEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE38 | geometry (ScaleEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE39 | geometry (PixelateEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE40 | geometry (RepeatEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE41 | geometry (ScrollEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE42 | geometry (MirrorEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE43 | geometry (ProjectionMappingEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE44 | hyperion (VimanaHyperion) | P0 | ◯ Todo | VJlive-2 |
| P7-VE45 | hyperspace_tunnel (HyperspaceTunnelEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE46 | living_fractal_consciousness (LivingFractalConsciousness) | P0 | ◯ Todo | VJlive-2 |
| P7-VE47 | luma_chroma_mask (LumaChromaMaskEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE48 | lut_grading (LUTGradingEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE49 | milkdrop (MilkdropEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE50 | morphology (MorphologyEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE51 | oscilloscope (OscilloscopeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE52 | plugin_template (CustomEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE53 | pop_art_effects (BenDayDotsEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE54 | pop_art_effects (WarholQuadEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE55 | r16_deep_mosh_studio (R16DeepMoshStudio) | P0 | ◯ Todo | VJlive-2 |
| P7-VE56 | r16_interstellar_mosh (R16InterstellarMosh) | P0 | ◯ Todo | VJlive-2 |
| P7-VE57 | reaction_diffusion (ReactionDiffusionEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE58 | resize_effect (ResizeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE59 | rutt_etra_scanline (RuttEtraScanlineEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE60 | silver_visions (VideoOutEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE61 | silver_visions (ImageInEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE62 | silver_visions (CoordinateFolderEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE63 | silver_visions (AffineTransformEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE64 | silver_visions (PreciseDelayEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE65 | slit_scan (SlitScanEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE66 | sync_eater (SyncEaterEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE67 | time_remap (TimeRemapEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE68 | vcv_video_effects (GaussianBlurEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE69 | vcv_video_effects (MultibandColorEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE70 | vcv_video_effects (HDRToneMapEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE71 | vcv_video_effects (SolarizeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE72 | vcv_video_effects (ResonantBlurEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE73 | vcv_video_effects (AdaptiveContrastEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE74 | vcv_video_effects (SpatialEchoEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE75 | vcv_video_effects (DelayZoomEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE76 | vibrant_retro_styles (RioAestheticEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE77 | vimana (Vimana) | P0 | ◯ Todo | VJlive-2 |
| P7-VE78 | vimana_hyperion_ultimate (VimanaHyperionUltimate) | P0 | ◯ Todo | VJlive-2 |
| P7-VE79 | vimana_synth (VimanaEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE80 | visualizer (VisualizerEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE81 | visualizer (SpectrumAnalyzerEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE82 | visualizer (VUMeterEffect) | P0 | ◯ Todo | VJlive-2 |

## Phase 8: Integration & Polish (Weeks 19-24)

| Task ID | Description | Status |
|---------|-------------|--------|
| P8-I1 | End-to-end integration testing | ⬜ Todo |
| P8-I2 | Performance benchmarks (60fps target verified) | ⬜ Todo |
| P8-I3 | Security audit (zero P0 vulns) | ⬜ Todo |
| P8-I4 | 80%+ test coverage on all core systems | ⬜ Todo |
| P8-I5 | Complete documentation for all features | ⬜ Todo |
| P8-I6 | Production deployment validation | ⬜ Todo |
| P8-I7 | User acceptance testing | ⬜ Todo |
| P8-I8 | Parity testing: Legacy VJLive vs VJLive3 | ⬜ Todo |
| P8-I2 | Performance benchmarks (60fps target verified) | ⬜ Todo |
| P8-I3 | Security audit (zero P0 vulns) | ⬜ Todo |
| P8-I4 | 80%+ test coverage on all core systems | ⬜ Todo |
| P8-I5 | Complete documentation for all features | ⬜ Todo |
| P8-I6 | Production deployment validation | ⬜ Todo |
| P8-I7 | User acceptance testing | ⬜ Todo |

---

## Dreamer Ports Scheduled
> See `WORKSPACE/KNOWLEDGE/DREAMER_LOG.md` for full analysis.

| ID | Module | Phase | Verdict |
|----|--------|-------|---------|
| DREAMER-000 | Silicon Sigil | P0 | ✅ Done |
| DREAMER-001 | Quantum Consciousness Explorer | P6-Q2 | 🔍 Analysis pending |
| DREAMER-002 | Living Fractal Consciousness | P6-Q4 | 🔍 Analysis pending |
| DREAMER-003 | Neural Engine | P6-AI1 | 🔍 Analysis pending |
| DREAMER-004 | 16D Agent Manifold | P6-AG2 | 🔍 Analysis pending |

---

## Ongoing Quality Gates

| Gate | Requirement | Status |
|------|-------------|--------|
| Q1 | FPS ≥ 58 at every phase completion | 🔄 Ongoing |
| Q2 | Memory stable (no monotonic increase) | 🔄 Ongoing |
| Q3 | 0 safety rail violations | 🔄 Ongoing |
| Q4 | ≥80% test coverage on new code | 🔄 Ongoing |
| Q5 | Silicon Sigil verified on every boot | 🔄 Ongoing |
| Q6 | No file exceeds 750 lines | ✅ Enforced (pre-commit) |
| Q7 | Bespoke treatment for every plugin port | 🔄 Ongoing |

---

## Safety Rail Status

| Rail | Description | Status |
|------|-------------|--------|
| Rail 1 | 60 FPS Sacred | 🔄 Active |
| Rail 2 | Offline-First Architecture | ✅ Compliant |
| Rail 3 | Plugin System Integrity | 🔄 Active |
| Rail 4 | 750-Line Code Discipline | ✅ Enforced |
| Rail 5 | Test Coverage Gate (≥80%) | 🔄 Active |
| Rail 6 | Hardware Fail-Graceful | 🔄 Active |
| Rail 7 | No Silent Failures | 🔄 Active |
| Rail 8 | Resource Leak Prevention | 🔄 Active |
| Rail 9 | Backward Compatibility | 🔄 Active |
| Rail 10 | Security Non-Negotiables | 🔄 Active |

---

## Scale Summary

| Metric | Note |
|--------|------|
| Total features | Hundreds — every plugin is unique, never assume a complete count |
| vjlive-only plugins | Large collection — full audit required, no ceiling defined |
| VJlive-2-only features | Keep all, enhance with vjlive equivalents where applicable |
| Shared plugins | Verify VJlive-2 implementation quality; port improvements from vjlive |
| Depth collection | vjlive/vdepth/ is extensive — audit and port every one individually |
| Audio/Modulator collection | Both Bogaudio and Befaco families — port every module found |
| V-* visual effects | Full collection spread across both codebases — no shortcuts |
| Estimated timeline | 20-24 weeks minimum |

---

**"The best code is code that knows what it is and does it well."**
*— WORKSPACE/PRIME_DIRECTIVE.md*