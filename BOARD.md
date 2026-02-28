# VJLive3 Project Board
**Version:** 3.4 | **Last Updated:** 2026-02-27 | **Manager:** ANTIGRAVITY (Overseer)

> [!IMPORTANT]
> **REVISED 3-PASS PIPELINE ARCHITECTURE**
> The grid below tracks all 1000+ legacy plugins. 
> - 🟩 **DONE**: Specs that have survived Pass 2 and are now awaiting Pass 3 Frontier Analysis.
> - ⬜ **TODO**: Specs currently queued for Qwen/Roo generation.

## 🏁 Milestones

### Phase 0: System Boot & Verification
| ID    | Component | Phase | Status | Notes |
|-------|-----------|-------|--------|-------|
| P0-G1 | Environment Reboot | P0 | ✅ Done | 3-Pass architecture initialized |

## 📦 The Unified Spec Queue (Pass 1 & Pass 2)
| ID | Plugin / Effect Task | Phase | Status | Legacy Path / Notes |
|---|---|---|---|---|
| P0-G1 | WORKSPACE/PRIME_DIRECTIVE.md | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-G2 | WORKSPACE/SAFETY_RAILS.md | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-G3 | WORKSPACE/COMMS/AGENT_SYNC.md | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-G4 | WORKSPACE/COMMS/LOCKS.md | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-G5 | WORKSPACE/COMMS/DECISIONS.md | P0 | ⬜ PENDING SKELETON (Pass 1) | 7 ADRs logged |
| P0-G6 | WORKSPACE/KNOWLEDGE/DREAMER_LOG.md | P0 | ⬜ PENDING SKELETON (Pass 1) | Sigil + 3 entries |
| P0-G7 | WORKSPACE/KNOWLEDGE/TOOL_TIPS.md | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-G8 | Root PRIME_DIRECTIVE.md | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-W1 | .agent/workflows/manager-job.md | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-W2 | .agent/workflows/no-stub-policy.md | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-W3 | .agent/workflows/bespoke-plugin-migration.md | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-W4 | .agent/workflows/phase-gate-check.md | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-Q1 | scripts/check_stubs.py | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-Q2 | scripts/check_file_size.py | P0 | ⬜ PENDING SKELETON (Pass 1) | 750-line enforcer |
| P0-Q3 | scripts/check_file_lock.py | P0 | ⬜ PENDING SKELETON (Pass 1) |  |
| P0-Q4 | .pre-commit-config.yaml | P0 | ⬜ PENDING SKELETON (Pass 1) | 3 custom hooks |
| P0-S1 | Silicon Sigil — src/vjlive3/core/sigil.py | P0 | ⬜ PENDING SKELETON (Pass 1) | Cave painting v3 — 11/11 tests ✅ 2026-02-21 |
| P0-M1 | MCP server: vjlive3brain (knowledge base) | P0 | ⬜ PENDING SKELETON (Pass 1) | FastMCP, 7 tools, 19k+ concepts seeded |
| P0-M2 | MCP server: vjlive-switchboard (locks + comms + queue) | P0 | ⬜ PENDING SKELETON (Pass 1) | FastMCP, 9 tools, orchestrator active |
| P0-A1 | Phase 0 App Window (FPS · Memory · Agents) | P0 | ⬜ PENDING SKELETON (Pass 1) | Implementation plan drafted |
| P0-V1 | Phase gate check | P0 | ⬜ PENDING SKELETON (Pass 1) | MCP verified, FPS validation passed |
| P0-INF2 | Legacy Feature Parity - 218 missing plugins (comprehensive audit) | P0 | ⬜ PENDING SKELETON (Pass 1) | Comprehensive audit of vjlive/ & VJlive-2/ ✅ 2026-02-22 |
| P3-EXT001 | ascii_effect (ASCIIEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT002 | vcv_video_effects (AdaptiveContrastEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT003 | particles_3d (AdvancedParticle3DSystem) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT004 | agent_avatar (AgentAvatarEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT005 | living_fractal_consciousness (AgentPersonality) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT006 | analog_tv (AnalogTVEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT007 | arbhar_granular_engine (ArbharGranularEngine) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT008 | arbhar_granularizer (ArbharGranularizer) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT009 | raymarched_scenes (AudioReactiveRaymarchedScenes) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT010 | audio_reactive_effects (AudioSpectrumTrails) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT011 | background_subtraction (BackgroundSubtractionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT012 | depth_effects (BackgroundSubtractionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BackgroundSubtractionEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT013 | bad_trip_datamosh (BadTripDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/bad_trip_datamosh.py` — 12-param horror datamosh, 21 tests ✅ 2026-02-23 |
| P3-EXT014 | bass_cannon_datamosh (BassCannonDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT015 | bass_cannon_2 (BassCanon2) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/bass_cannon_2.py` — 30-param neural rave cannon, 24 tests ✅ 2026-02-23 |
| P3-EXT016 | bass_therapy_datamosh (BassTherapyDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BassTherapyDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT017 | pop_art_effects (BenDayDotsEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT018 | blend (BlendAddEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT019 | blend (BlendDiffEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BlendDiffEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT020 | blend (BlendMultEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BlendMultEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT021 | blend (BloomEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BloomEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT022 | blend (BloomShadertoyEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BloomShadertoyEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT023 | color (BrightnessEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BrightnessEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT024 | bullet_time_datamosh (BulletTimeDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BulletTimeDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT025 | vcv_video_generators (ByteBeatGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ByteBeatGen already shipped in P4/P5/P6/P7)* |
| P3-EXT026 | cellular_automata_datamosh (CellularAutomataDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — CellularAutomataDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT027 | chroma_key (ChromaKeyEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ChromaKeyEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT028 | distortion (ChromaticDistortionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ChromaticDistortionEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT029 | color (ColorCorrectEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ColorCorrectEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT030 | color (ColoramaEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ColoramaEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT031 | quantum_consciousness_explorer (ConsciousnessLevel) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT032 | tunnel_vision_3 (ConsciousnessNet) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT033 | consciousness_neural_network (ConsciousnessNeuralNetwork) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT034 | color (ContrastEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ContrastEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT035 | cosmic_tunnel_datamosh (CosmicTunnelDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — CosmicTunnelDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT036 | cotton_candy_datamosh (CottonCandyDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — CottonCandyDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT037 | cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — CupcakeCascadeDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT038 | datamosh_3d (Datamosh3DEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — Datamosh3DEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT039 | vcv_video_effects (DelayZoomEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DelayZoomEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT040 | depth_acid_fractal (DepthAcidFractalPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_acid_fractal.py` — 6-param depth-reactive fractal, 5 tests ✅ 2026-02-23 |
| P3-EXT041 | depth_camera_splitter (DepthCameraSplitterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthCameraSplitterEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT042 | depth_data_mux (DepthDataMuxEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthDataMuxEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT043 | datamosh_3d (DepthDisplacementEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthDisplacementEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT044 | depth_distance_filter (DepthDistanceFilterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthDistanceFilterEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT045 | depth_effects (DepthDistortionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthDistortionEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT046 | depth_dual (DepthDualEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthDualEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT047 | datamosh_3d (DepthEchoEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthEchoEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT048 | depth_fx_loop (DepthFXLoopEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthFXLoopEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT049 | depth_feedback_matrix_datamosh (DepthFeedbackMatrixDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthFeedbackMatrixDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT050 | depth_effects (DepthFieldEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthFieldEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT051 | depth_fog (DepthFogEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthFogEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT052 | depth_groovy_datamosh (DepthGroovyDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthGroovyDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT053 | depth_holographic (DepthHolographicIridescenceEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthHolographicIridescenceEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT054 | depth_loop_injection_datamosh (DepthLoopInjectionDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT055 | depth_effects (DepthMeshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthMeshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT056 | depth_modular_datamosh (DepthModularDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthModularDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT057 | depth_modulated_datamosh (DepthModulatedDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthModulatedDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT058 | depth_mosh_nexus (DepthMoshNexus) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthMoshNexus already shipped in P4/P5/P6/P7)* |
| P3-EXT059 | depth_parallel_universe_datamosh (DepthParallelUniverseDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthParallelUniverseDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT060 | depth_effects (DepthParticle3DEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthParticle3DEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT061 | depth_effects (DepthPointCloud3DEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthPointCloud3DEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT062 | depth_effects (DepthPointCloudEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthPointCloudEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT063 | depth_raver_datamosh (DepthRaverDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthRaverDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT064 | depth_simulator (DepthSimulatorEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthSimulatorEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT065 | depth_slitscan_datamosh (DepthSlitScanDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthSlitScanDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT066 | depth_effects (DepthEffectsPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_effects.py` — 7-effect depth chain (blur, color, distortion, glow, fog, sharpen), 8 tests ✅ 2026-02-23 |
| P3-EXT067 | depth_void_datamosh (DepthVoidDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DepthVoidDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT068 | dimension_splice_datamosh (DimensionSpliceDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DimensionSpliceDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT069 | displacement_map (DisplacementMapEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DisplacementMapEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT070 | dithering (DitheringEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DitheringEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT071 | dolly_zoom_datamosh (DollyZoomDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — DollyZoomDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT072 | vtempi (DutyCycleMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT073 | particles_3d (EmitterType) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT074 | erbe_verb (ErbeVerb) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT075 | example_glitch (ExampleGlitchEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT076 | vcv_video_generators (FMCoordinatesGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — FMCoordinatesGen already shipped in P4/P5/P6/P7)* |
| P3-EXT077 | face_melt_datamosh (FaceMeltDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — FaceMeltDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT078 | shadertoy_particles (FireParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT079 | fluid_sim (FluidSimEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — FluidSimEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT080 | particles_3d (ForceType) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT081 | fractal_generator (FractalGenerator) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — FractalGenerator already shipped in P4/P5/P6/P7)* |
| P3-EXT082 | fracture_rave_datamosh (FractureRaveDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — FractureRaveDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT083 | datamosh (FrameHoldEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — FrameHoldEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT084 | vcv_video_effects (GaussianBlurEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — GaussianBlurEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT085 | generators (GradientEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — GradientEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT086 | vcv_video_generators (GranularVideoGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — GranularVideoGen already shipped in P4/P5/P6/P7)* |
| P3-EXT087 | vcv_video_effects (HDRToneMapEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — HDRToneMapEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT088 | vcv_video_generators (HarmonicPatternsGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — HarmonicPatternsGen already shipped in P4/P5/P6/P7)* |
| P3-EXT089 | v_sws (HorizontalWaveEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — HorizontalWaveEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT090 | vtempi (HumanResolution) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT091 | neural_quantum_hyper_tunnel (HyperTunnelNet) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT092 | hyperspace_quantum_tunnel (HyperspaceQuantumTunnel) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT093 | blend (InfiniteFeedbackEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — InfiniteFeedbackEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT094 | color (InvertEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — InvertEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT095 | vtempi (LEDColor) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT096 | lut_grading (LUTGradingEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — LUTGradingEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT097 | datamosh_3d (LayerSeparationEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — LayerSeparationEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT098 | liquid_lsd_datamosh (LiquidLSDDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — LiquidLSDDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT099 | luma_chroma_mask (LumaChromaMaskEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — LumaChromaMaskEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT100 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MLBaseAsyncEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT101 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MLDepthEstimationEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT102 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MLSegmentationBlurGLEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT103 | ml_gpu_effects (MLStyleGLEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MLStyleGLEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT104 | vcv_video_generators (MacroShapeGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MacroShapeGen already shipped in P4/P5/P6/P7)* |
| P3-EXT105 | generators (MandalaEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MandalaEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT106 | geometry (MandalascopeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MandalascopeEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT107 | geometry (MirrorEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MirrorEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT108 | blend (MixerEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MixerEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT109 | vtempi (ModBehavior) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT110 | morphology (MorphologyEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MorphologyEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT111 | mosh_pit_datamosh (MoshPitDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MoshPitDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT112 | vcv_video_effects (MultibandColorEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — MultibandColorEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT113 | shadertoy_particles (NebulaParticles) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT114 | neural_rave_nexus (NeuralRaveNexus) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — NeuralRaveNexus already shipped in P4/P5/P6/P7)* |
| P3-EXT115 | neural_splice_datamosh (NeuralSpliceDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — NeuralSpliceDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT116 | tunnel_vision_2 (NeuralTunnelNet) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P3-EXT116_NeuralTunnelNet.md` — spec approved |
| P3-EXT117 | optical_flow (OpticalFlowEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — OpticalFlowEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT118 | depth_effects (OpticalFlowEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — OpticalFlowEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT119 | oscilloscope (OscilloscopeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — OscilloscopeEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT120 | visualizer (OscilloscopeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — OscilloscopeEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT121 | particles_3d (Particle3DSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — Particle3DSystem already shipped in P4/P5/P6/P7)* |
| P3-EXT122 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ParticleDatamoshTrailsEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT123 | particles_3d (ParticleState) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT124 | distortion (PatternDistortionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — PatternDistortionEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT125 | generators (PerlinEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — PerlinEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT126 | datamosh (PixelBloomEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — PixelBloomEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT127 | datamosh (PixelSortEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — PixelSortEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT128 | geometry (PixelateEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — PixelateEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT129 | plasma_melt_datamosh (PlasmaMeltDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — PlasmaMeltDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT130 | color (PosterizeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — PosterizeEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT131 | prism_realm_datamosh (PrismRealmDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — PrismRealmDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT132 | vtempi (ProgramPage) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT133 | quantum_consciousness_datamosh (QuantumConsciousnessDatamosh) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P3-EXT133_QuantumConsciousnessDatamosh.md` — spec approved |
| P3-EXT134 | tunnel_vision_3 (QuantumConsciousnessSingularityEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — QuantumConsciousnessSingularityEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT135 | quantum_depth_nexus (QuantumDepthNexus) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — QuantumDepthNexus already shipped in P4/P5/P6/P7)* |
| P3-EXT136 | quantum_entanglement_point_cloud (QuantumEntanglementPointCloud) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT137 | quantum_consciousness_explorer (QuantumState) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT138 | quantum_consciousness_explorer (QuantumState) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT139 | r16_deep_mosh_studio (R16DeepMoshStudio) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — R16DeepMoshStudio already shipped in P4/P5/P6/P7)* |
| P3-EXT140 | r16_depth_wave (R16DepthWave) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT141 | r16_interstellar_mosh (R16InterstellarMosh) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — R16InterstellarMosh already shipped in P4/P5/P6/P7)* |
| P3-EXT142 | r16_simulated_depth (R16SimulatedDepth) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT143 | r16_vortex (R16VortexEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT144 | color (RGBShiftEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — RGBShiftEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT145 | vibrant_retro_styles (RadiantMeshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — RadiantMeshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT146 | rainmaker_rhythmic_echo (RainmakerRhythmicEcho) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT147 | reaction_diffusion (ReactionDiffusionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ReactionDiffusionEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT148 | reality_distortion_field (RealityDistortionField) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT149 | particles_3d (RenderMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT150 | geometry (RepeatEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — RepeatEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT151 | resize_effect (ResizeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ResizeEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT152 | vcv_video_effects (ResonantBlurEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ResonantBlurEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT153 | vcv_video_generators (ResonantGeometryGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ResonantGeometryGen already shipped in P4/P5/P6/P7)* |
| P3-EXT154 | vibrant_retro_styles (RioAestheticEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — RioAestheticEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT155 | v_sws (RippleEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — RippleEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT156 | geometry (RotateEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — RotateEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT157 | vtempi (RunStopMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT158 | rutt_etra_scanline (RuttEtraScanlineEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — RuttEtraScanlineEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT159 | sacred_geometry_datamosh (SacredGeometryDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — SacredGeometryDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT160 | color (SaturateEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — SaturateEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT161 | blend (ScanlinesEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ScanlinesEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT162 | scion_biometric_flux (ScionBiometricFlux) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT163 | geometry (ScrollEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ScrollEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT164 | shadertoy_particles (ShadertoyParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ShadertoyParticles already shipped in P4/P5/P6/P7)* |
| P3-EXT165 | datamosh_3d (ShatterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ShatterEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT166 | vtempi (ShiftDirection) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT167 | simulated_color_depth (SimulatedColorDepth) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT168 | slit_scan (SlitScanEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — SlitScanEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT169 | vcv_video_effects (SolarizeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — SolarizeEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT170 | vcv_video_effects (SpatialEchoEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — SpatialEchoEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT171 | visualizer (SpectrumAnalyzerEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — SpectrumAnalyzerEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT172 | v_sws (SpiralWaveEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — SpiralWaveEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT173 | spirit_aura_datamosh (SpiritAuraDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — SpiritAuraDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT174 | sync_eater (SyncEaterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — SyncEaterEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT175 | temporal_rift_datamosh (TemporalRiftDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — TemporalRiftDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT176 | test_bass_cannon_3 (TestBassCanon3) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT177 | test_neural_quantum_hyper_tunnel (TestIntegrationWithVJLive) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT178 | test_neural_quantum_hyper_tunnel (TestNeuralQuantumHyperTunnel) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT179 | test_plugin (TestPluginPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT180 | color (ThreshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — ThreshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT181 | time_remap (TimeRemapEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — TimeRemapEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT182 | agent_avatar (TravelingAvatarEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — TravelingAvatarEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT183 | tunnel_vision_datamosh (TunnelVisionDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — TunnelVisionDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT184 | unicorn_farts_datamosh (UnicornFartsDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — UnicornFartsDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT185 | vattractors (VHalvorsenPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT186 | vattractors (VLorenzPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT187 | v_rainmaker_rhythmic_echo (VRainmakerRhythmicEcho) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT188 | vattractors (VSakaryaPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/vattractors.py` — VAttractorsPlugin (mode=3), 41 tests ✅ 2026-02-23 |
| P3-EXT189 | vbefaco_extra (VScopeXL) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(hardware-specific VCV Rack scope, no equivalent in VJLive3 alpha)* |
| P3-EXT190 | v_sws (VSwsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — VSwsEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT191 | vattractors (VThomasPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT192 | visualizer (VUMeterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — VUMeterEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT193 | v_warps (VWarps) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(VCV Rack hardware warp module, no GPU equivalent for alpha)* |
| P3-EXT194 | v_sws (VerticalWaveEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — VerticalWaveEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT195 | blend (VignetteEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — VignetteEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT196 | visualizer (VisualizerEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — VisualizerEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT197 | void_swirl_datamosh (VoidSwirlDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — VoidSwirlDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT198 | volumetric_datamosh (VolumetricDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — VolumetricDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT199 | volumetric_glitch (VolumetricGlitchEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — VolumetricGlitchEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT200 | generators (VoronoiEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — VoronoiEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT201 | pop_art_effects (WarholQuadEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — WarholQuadEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT202 | blend_modes (_BlendMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — _BlendMode already shipped in P4/P5/P6/P7)* |
| P3-EXT203 | ml_gpu_effects (_WorkerThread) | P0 | ⬜ PENDING SKELETON (Pass 1) | vjlive |
| P3-EXT204 | particles_3d (AdvancedParticle3DSystem) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT205 | particles_3d (AdvancedParticle3DSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT206 | particles_3d (AdvancedParticle3DSystem) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT207 | silver_visions (AffineTransformEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT208 | agent_avatar (AgentAvatarEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT209 | agent_avatar (AgentAvatarEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT210 | astra_node (AstraNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT211 | raymarched_scenes (AudioReactiveRaymarchedScenes) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT212 | raymarched_scenes (AudioReactiveRaymarchedScenes) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT213 | audio_reactive (AudioSpectrumTrails) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT214 | depth_effects (BackgroundSubtractionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT215 | bad_trip_datamosh (BadTripDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT216 | bass_cannon_datamosh (BassCannonDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT217 | bass_cannon_2 (BassCanon2) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT218 | bass_therapy_datamosh (BassTherapyDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT219 | pop_art_effects (BenDayDotsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT220 | pop_art_effects (BenDayDotsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT221 | bullet_time_datamosh (BulletTimeDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT222 | cellular_automata_datamosh (CellularAutomataDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT223 | colorama (ColoramaEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT224 | tunnel_vision_3 (ConsciousnessNet) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT225 | consciousness_neural_network (ConsciousnessNeuralNetwork) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT226 | consciousness_neural_network_effect (ConsciousnessNeuralNetwork) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT227 | silver_visions (CoordinateFolderEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT228 | cosmic_tunnel_datamosh (CosmicTunnelDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT229 | cotton_candy_datamosh (CottonCandyDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT230 | cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT231 | datamosh_3d (Datamosh3DEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT232 | depth_acid_fractal (DepthAcidFractalDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT233 | depth_camera_splitter (DepthCameraSplitterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT234 | depth_data_mux (DepthDataMuxEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT235 | datamosh_3d (DepthDisplacementEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT236 | depth_distance_filter (DepthDistanceFilterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT237 | depth_effects (DepthDistortionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT238 | depth_dual (DepthDualEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT239 | datamosh_3d (DepthEchoEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT240 | depth_fx_loop (DepthFXLoopEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT241 | depth_feedback_matrix_datamosh (DepthFeedbackMatrixDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT242 | depth_effects (DepthFieldEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT243 | depth_fog (DepthFogEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT244 | depth_groovy_datamosh (DepthGroovyDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT245 | depth_holographic (DepthHolographicIridescenceEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT246 | depth_loop_injection_datamosh (DepthLoopInjectionDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT247 | depth_effects (DepthMeshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT248 | depth_modular_datamosh (DepthModularDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT249 | depth_modulated_datamosh (DepthModulatedDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT250 | depth_mosh_nexus (DepthMoshNexus) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT251 | depth_parallel_universe_datamosh (DepthParallelUniverseDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT252 | depth_effects (DepthParticle3DEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT253 | depth_effects (DepthPointCloud3DEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT254 | depth_effects (DepthPointCloudEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT255 | depth_raver_datamosh (DepthRaverDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT256 | depth_simulator (DepthSimulatorEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT257 | depth_slitscan_datamosh (DepthSlitScanDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT258 | depth_effects (DepthVisualizationMode) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT259 | depth_void_datamosh (DepthVoidDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT260 | dimension_splice_datamosh (DimensionSpliceDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT261 | dolly_zoom_datamosh (DollyZoomDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT262 | vtempi (DutyCycleMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT263 | vtempi (DutyCycleMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT264 | particles_3d (EmitterType) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT265 | particles_3d (EmitterType) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT266 | face_melt_datamosh (FaceMeltDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT267 | shadertoy_particles (FireParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT268 | shadertoy_particles (FireParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT269 | shadertoy_particles (FireParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT270 | fluid_sim (FluidSimEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT271 | particles_3d (ForceType) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT272 | particles_3d (ForceType) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT273 | fracture_rave_datamosh (FractureRaveDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT274 | vtempi (HumanResolution) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT275 | vtempi (HumanResolution) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT276 | neural_quantum_hyper_tunnel (HyperTunnelNet) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT277 | neural_quantum_hyper_tunnel_effect (HyperTunnelNet) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT278 | hyperspace_quantum_tunnel (HyperspaceQuantumTunnel) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT279 | hyperspace_quantum_tunnel_effect (HyperspaceQuantumTunnel) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT280 | hyperspace_tunnel (HyperspaceTunnelEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT281 | silver_visions (ImageInEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT282 | vtempi (LEDColor) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT283 | vtempi (LEDColor) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT284 | datamosh_3d (LayerSeparationEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT285 | liquid_lsd_datamosh (LiquidLSDDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT286 | ml_effects (MLBaseAsyncEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT287 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT288 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT289 | ml_effects (MLDepthEstimationEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT290 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT291 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT292 | ml_effects (MLSegmentationBlurGLEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT293 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT294 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT295 | ml_effects (MLStyleGLEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT296 | ml_gpu_effects (MLStyleGLEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT297 | ml_gpu_effects (MLStyleGLEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT298 | vtempi (ModBehavior) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT299 | vtempi (ModBehavior) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT300 | mosh_pit_datamosh (MoshPitDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT301 | shadertoy_particles (NebulaParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT302 | shadertoy_particles (NebulaParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT303 | shadertoy_particles (NebulaParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT304 | neural_rave_nexus (NeuralRaveNexus) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT305 | neural_splice_datamosh (NeuralSpliceDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT306 | tunnel_vision_2 (NeuralTunnelNet) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT307 | depth_effects (OpticalFlowEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT308 | particles_3d (Particle3DSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT309 | particles_3d (Particle3DSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT310 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT311 | particles_3d (ParticleState) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT312 | particles_3d (ParticleState) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT313 | plasma_melt_datamosh (PlasmaMeltDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT314 | silver_visions (PreciseDelayEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT315 | prism_realm_datamosh (PrismRealmDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT316 | vtempi (ProgramPage) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT317 | vtempi (ProgramPage) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT318 | quantum_consciousness_datamosh (QuantumConsciousnessDatamosh) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT319 | quantum_consciousness_datamosh_effect (QuantumConsciousnessDatamosh) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT320 | tunnel_vision_3 (QuantumConsciousnessSingularityEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT321 | quantum_depth_nexus (QuantumDepthNexus) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT322 | quantum_depth_nexus_effect (QuantumDepthNexus) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT323 | quantum_entanglement_point_cloud (QuantumEntanglementPointCloud) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT324 | quantum_entanglement_point_cloud_effect (QuantumEntanglementPointCloud) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT325 | quantum_consciousness_explorer (QuantumState) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT326 | quantum_consciousness_explorer_effect (QuantumState) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT327 | r16_deep_mosh_studio (R16DeepMoshStudio) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-VD08 | Depth R16 Wave (DepthR16WavePlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_r16_wave.py` — DepthR16WavePlugin, 8/8 tests ✅ 2026-02-22 |
| P3-EXT329 | r16_interstellar_mosh (R16InterstellarMosh) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT330 | r16_simulated_depth (R16SimulatedDepth) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT331 | r16_vortex (R16VortexEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT332 | vibrant_retro_styles (RadiantMeshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT333 | vibrant_retro_styles (RadiantMeshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT334 | reaction_diffusion (ReactionDiffusionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT335 | reality_distortion_field (RealityDistortionField) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT336 | particles_3d (RenderMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT337 | particles_3d (RenderMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT338 | particles_3d (RenderMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT339 | vibrant_retro_styles (RioAestheticEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT340 | vibrant_retro_styles (RioAestheticEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT341 | vtempi (RunStopMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT342 | vtempi (RunStopMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT343 | sacred_geometry_datamosh (SacredGeometryDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT344 | shadertoy_particles (ShadertoyParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT345 | shadertoy_particles (ShadertoyParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT346 | shadertoy_particles (ShadertoyParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT347 | datamosh_3d (ShatterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT348 | vtempi (ShiftDirection) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT349 | vtempi (ShiftDirection) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT350 | simulated_color_depth (SimulatedColorDepth) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT351 | spirit_aura_datamosh (SpiritAuraDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT352 | temporal_rift_datamosh (TemporalRiftDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT353 | test_bass_cannon_3 (TestBassCanon3) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT354 | test_neural_quantum_hyper_tunnel (TestIntegrationWithVJLive) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT355 | test_neural_quantum_hyper_tunnel (TestNeuralQuantumHyperTunnel) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT356 | test_plugin (TestPluginPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT357 | agent_avatar (TravelingAvatarEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT358 | agent_avatar (TravelingAvatarEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT359 | tunnel_vision_datamosh (TunnelVisionDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT360 | unicorn_farts_datamosh (UnicornFartsDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT361 | vvoxglitch (VByteBeat) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT362 | vmake_noise (VDXGPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT363 | vmake_noise (VDynaMixPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT364 | vmake_noise (VErbeVerbPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT365 | vmi_complex (VFramesMIPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT366 | vmake_noise (VFxDfPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT367 | vvoxglitch (VGhosts) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT368 | vvoxglitch (VGlitchSequencer) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT369 | vvoxglitch (VGrooveBox) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT370 | vattractors (VHalvorsenPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT371 | vattractors (VHalvorsenPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT372 | vvoxglitch (VHazumi) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT373 | vattractors (VLorenzPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT374 | vattractors (VLorenzPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT375 | vlxd (VLxDPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT376 | vmake_noise (VMorphagenePlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT377 | vmake_noise (VQMMGPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT378 | vmake_noise (VQXGPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT379 | vmake_noise (VRenePlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT380 | vvoxglitch (VRepeater) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT381 | vmi_complex (VRingsMIPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT382 | vmi_complex (VRipplesMIPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT383 | vmake_noise (VRosiePlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT384 | vmake_noise (VRxMxPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT385 | vattractors (VSakaryaPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT386 | vattractors (VSakaryaPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT387 | vvoxglitch (VSatanonaut) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT388 | vbefaco_extra (VScopeXL) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT389 | vmake_noise (VSpectraphonPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT390 | vmi_complex (VStagesMIPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT391 | vmi_complex (VStreamsMIPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT392 | vattractors (VThomasPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT393 | vattractors (VThomasPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT394 | vmi_complex (VTidesMIPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT395 | vmi_complex (VWarpsMIPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT396 | vmake_noise (VWogglebugPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT397 | vvoxglitch (VXY) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT398 | base (VechophonBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT399 | base (VfunctionBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT400 | silver_visions (VideoOutEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT401 | hyperion (VimanaHyperion) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT402 | vimana_hyperion_ultimate (VimanaHyperionUltimate) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT403 | base (VjumblerBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT404 | base (VlxdBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT405 | base (Vmake_noiseBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT406 | base (VmathsBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT407 | base (Vmi_complexBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT408 | base (VmlBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT409 | void_swirl_datamosh (VoidSwirlDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT410 | volumetric_datamosh (VolumetricDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT411 | volumetric_glitch (VolumetricGlitchEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT412 | base (VparticlesBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT413 | base (Vshadertoy_extraBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT414 | base (Vstages_anomBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT415 | base (VstyleBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT416 | base (VtempiBase) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT417 | base (Vtides_anomBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT418 | base (VvoxglitchBase) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT419 | pop_art_effects (WarholQuadEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT420 | pop_art_effects (WarholQuadEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT421 | ml_effects (_WorkerThread) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT422 | ml_gpu_effects (_WorkerThread) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT423 | ml_gpu_effects (_WorkerThread) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P0-INF4 | Core Logic Parity - Complete scan of 1800 entities | P0 | ⬜ PENDING SKELETON (Pass 1) | Comprehensive audit of vjlive/ & VJlive-2/ core/ ✅ 2026-02-22 |
| P4-COR001 | ai_sanitizer (AIAnomalyDetector) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR002 | ai_assistant (AIAssistant) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR003 | automation_timeline (AIBrain) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR003_AIBrain.md` |
| P4-COR004 | co_creation_enhanced (AICreativeAssistant) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR004_AICreativeAssistant.md` |
| P4-COR005 | creative_partner (AICreativePartner) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR005_AICreativePartner.md` |
| P4-COR006 | creative_partner (AICreativePartnerFactory) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR006_AICreativePartnerFactory.md` |
| P4-COR007 | co_creation_enhanced (AICurator) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR007_AICurator.md` |
| P4-COR008 | ai_assistant (AIHint) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR009 | ai_integration (AIIntegration) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR009_AIIntegration.md` |
| P4-COR010 | quantum_reactor (AIParameterPrediction) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR010_AIParameterPrediction.md` |
| P4-COR011 | config_constants (AIParameters) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR011_AIParameters.md` |
| P4-COR012 | brush_engines (AIPartnerBrush) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR012_AIPartnerBrush.md` |
| P4-COR013 | ai_sanitizer (AISanitizer) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR013_AISanitizer.md` |
| P4-COR014 | brain (AIScheduler) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR014_AIScheduler.md` |
| P4-COR015 | ai_shader_generator (AIShaderGenerator) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR015_AIShaderGenerator.md` |
| P4-COR016 | ai_suggestion_engine (AISuggestion) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR016_AISuggestion.md` |
| P4-COR017 | ai_suggestion_engine (AISuggestionEngine) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR017_AISuggestionEngine.md` |
| P4-COR018 | ai_integration (AISystemStatus) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR018_AISystemStatus.md` |
| P4-COR019 | adain (AdaINStyleTransfer) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR019_AdaINStyleTransfer.md` |
| P4-COR020 | agent_avatar (AgentAvatarEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR020_AgentAvatarEffect.md` |
| P4-COR021 | config_manager (AgentConfig) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR021_AgentConfig.md` |
| P4-COR022 | agent_graph_visualizer (AgentGraphVisualizer) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR022_AgentGraphVisualizer.md` |
| P4-COR023 | unified_hydra_extensions (AgentHydraExtension) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR023_AgentHydraExtension.md` |
| P4-COR024 | agent_bridge (AgentInteractionMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR024_AgentInteractionMode.md` |
| P4-COR025 | agent_manager (AgentManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR025_AgentManager.md` |
| P4-COR026 | awesome_collaborative_creation (AgentMood) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR027 | agent_orchestrator (AgentOrchestrator) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR027_AgentOrchestrator.md` |
| P4-COR028 | text_overlay (AgentOverlay) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR028_AgentOverlay.md` |
| P4-COR029 | agent_bridge (AgentPerformanceBridge) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P4-COR029_AgentPerformanceBridge.md` |
| P4-COR030 | agent_persona (AgentPersona) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR031 | routes (AgentPersonaCreate) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR032 | models (AgentPersonaModel) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR033 | routes (AgentPersonaResponse) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR034 | awesome_collaborative_creation (AgentPersonality) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR035 | awesome_collaborative_creation (AgentPersonalityEngine) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR036 | rhythm_consciousness (AgentRhythmProfile) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR037 | agent_orchestrator (AgentState) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR038 | agent_bridge (AgentSuggestion) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR039 | creative_hive (AgentType) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR040 | agent_visualizer (AgentVisualizer) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR041 | crowd_analysis_aggregator (AggregatedCrowdState) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR042 | mutable_generators (BraidsGenerator) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR043 | node_modulation_mutable_generators (BraidsNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR044 | hotplug_detector_new (CameraInfo) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR045 | depth_calibration (CameraIntrinsics) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR046 | creative_hive (CompositeAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR047 | neural_engine_enhanced (CreativeNeuralEngine) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR048 | crowd_ai (CrowdAI) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR048_CrowdAI.md) |
| P4-COR049 | llm_service (CrowdAnalysis) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR050 | crowd_analysis_aggregator (CrowdAnalysisAggregator) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR050_CrowdAnalysisAggregator.md) |
| P4-COR051 | llm_service (CrowdEmotion) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR052 | multi_camera_manager (CrowdEnergyAggregator) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR052_CrowdEnergyAggregator.md) |
| P4-COR053 | crowd_listener (CrowdListener) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR053_CrowdListener.md) |
| P4-COR054 | crowd_pulse_engine (CrowdPulseEngine) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR054_CrowdPulseEngine.md) |
| P4-COR055 | crowd_listener (CrowdSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR055_CrowdSource.md) |
| P4-COR056 | data_rain (DataRain) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR056_DataRain.md) |
| P4-COR057 | living_debug_overlay (DebugAgentPersona) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR058 | dreamer_agent (DreamerAgentManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR058_DreamerAgentManager.md) |
| P4-COR059 | collaborative_canvas (EchoTrailEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR060 | enhanced_llm_service (EnhancedLLMService) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR061 | predictive_failure_detection (FailurePredictor) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR062 | predictive_failure_detection (FailureType) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR063 | shader_base (FramebufferRAII) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR063_FramebufferRAII.md) |
| P4-COR064 | brush_engines (FrequencyPainterBrush) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR064_FrequencyPainterBrush.md) |
| P4-COR065 | ghost_agent (GhostAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR065_GhostAgent.md) |
| P4-COR066 | creative_hive (GlitchAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR067 | harmonaig_color_harmonizer (HarmonaigColorHarmonizer) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR067_HarmonaigColorHarmonizer.md) |
| P4-COR068 | base (IAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR068_IAgent.md) |
| P4-COR069 | isf_effect (ISFEffectChain) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR069_ISFEffectChain.md) |
| P4-COR070 | llm_integration (LLMModelIntegration) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR071 | llm_service (LLMPrompt) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR072 | llm_service (LLMProvider) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR073 | routes (LLMProviderCreate) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR074 | routes (LLMProviderResponse) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR075 | llm_service (LLMService) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR076 | main_node_graph_integration (MainNodeGraphIntegration) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR076_MainNodeGraphIntegration.md) |
| P4-COR077 | media_scanner (MediaItem) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR077_MediaItem.md) |
| P4-COR078 | modifier_nodes (ModifierChain) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR078_ModifierChain.md) |
| P4-COR079 | movements (NeuralAwakening) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR079_NeuralAwakening.md) |
| P4-COR080 | neural_creative (NeuralCreativeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR080_NeuralCreativeEffect.md) |
| P4-COR081 | neural_effects (NeuralEffectsEngine) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(Duplicate)* |
| P4-COR082 | neural_engine (NeuralEngine) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(Duplicate)* |
| P4-COR083 | neural_link (NeuralLink) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(Duplicate)* |
| P4-COR084 | neural_engine_enhanced (NeuralMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR084_NeuralMode.md) |
| P4-COR085 | automation_timeline (NeuralNetworkConfig) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR085_NeuralNetworkConfig.md) |
| P4-COR086 | neural_engine_enhanced (NeuralPreset) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR086_NeuralPreset.md) |
| P4-COR087 | node_datamosh (NeuralSpliceNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR087_NeuralSpliceNode.md) |
| P4-COR088 | node_graph_bridge (NodeGraphBridge) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR088_NodeGraphBridge.md) |
| P4-COR089 | patch_manager (PatchManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR089_PatchManager.md) |
| P4-COR090 | node_datamosh (ParticleTrailsNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR090_ParticleDatamoshTrailsEffect.md) |
| P4-COR091 | openai_provider (OpenAIModelProvider) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR092 | llm_service (OpenAIProvider) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR093 | oracle (OracleBrain) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR093_OracleBrain.md) |
| P4-COR094 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(Duplicate)* |
| P4-COR095 | node_datamosh (ParticleTrailsNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(Duplicate)* |
| P4-COR096 | creative_hive (PatternAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR097 | performance (PerformanceAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR097_PerformanceAgent.md) |
| P4-COR098 | brush_engines (PersonalityTraits) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(Missing)* |
| P4-COR099 | mutable_generators (PlaitsGenerator) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR099_PlaitsGenerator.md) |
| P4-COR100 | node_modulation_mutable_generators (PlaitsNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR100_PlaitsNode.md) |
| P4-COR101 | quantum_pattern_recognition (QuantumNeuralNetwork) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR101_QuantumNeuralNetwork.md) |
| P4-COR102 | error_handling (SafeNeuralAwakening) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR102_SafeNeuralAwakening.md) |
| P4-COR103 | creative_hive (SentienceAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR104 | agent_example (StrobeAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR104_StrobeAgent.md) |
| P4-COR105 | creative_hive (StyleAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-CORXXX_A | node_modulation_mutable_generators (ShadesNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR104_ShadesNode.md) |
| P4-COR106 | tain_instant_cut_switcher (TainInstantCutSwitcher) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR106_TainInstantCutSwitcher.md) |
| P4-COR107 | agent_visualizer (TrailPoint) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR107_TrailPoint.md) |
| P4-COR108 | v_harmonaig (VHarmonaig) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR108_VHarmonaig.md) |
| P4-COR109 | intelligent_locking (WaitGraph) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR109_WaitGraph.md) |
| P4-COR110 | worker_agent (WorkerAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR110_WorkerAgent.md) |
| P4-COR111 | collaborative_canvas (AdvancedAudioReactor) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR112 | creative_hive (AudioAgent) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR113 | analyzer (AudioAnalyzer) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR113_AudioAnalyzer.md) |
| P4-COR114 | legacy_compat (AudioAnalyzerAdapter) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR114_AudioAnalyzerAdapter.md) |
| P4-COR115 | config_types (AudioConfig) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR115_AudioConfig.md) |
| P4-COR116 | models (AudioControlPayload) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR117 | node_effect_audio (AudioDistortionNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR117_AudioDistortionNode.md) |
| P4-COR118 | engine (AudioEngine) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR118_AudioEngine.md) |
| P4-COR119 | audio_features (AudioFeature) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR119_AudioFeature.md) |
| P4-COR120 | audio_features (AudioFeatureExtractor) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR120_AudioFeatureExtractor.md) |
| P4-COR121 | audio_features (AudioFeatureType) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR121_AudioFeatureType.md) |
| P4-COR122 | audio_kaleidoscope (AudioKaleidoscope) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR122_AudioKaleidoscope.md) |
| P4-COR123 | node_effect_audio (AudioKaleidoscopeNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR123_AudioKaleidoscopeNode.md) |
| P4-COR124 | node_effect_audio (AudioParticleNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR124_AudioParticleNode.md) |
| P4-COR125 | audio_particle_system (AudioParticleSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR125_AudioParticleSystem.md) |
| P4-COR126 | audio_player (AudioPlayer) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR126_AudioPlayer.md) |
| P4-COR127 | audio_reactive_3d_effect (AudioReactive3DEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR127_AudioReactive3DEffect.md) |
| P4-COR128 | audio_reactive_3d_scene (AudioReactive3DScene) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR128_AudioReactive3DScene.md) |
| P4-COR129 | audio_reactive_3d_scene_ultimate (AudioReactive3DSceneUltimate) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR129_AudioReactive3DSceneUltimate.md) |
| P4-COR130 | brush_engines (AudioReactiveBrush) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR131 | audio_reactive_effects (AudioReactiveEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR132 | audio_reactive (AudioReactiveEngine) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR133 | unified_hydra_extensions (AudioReactiveHydraExtension) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR133_AudioReactiveHydraExtension.md) |
| P4-COR134 | unified_base (AudioReactiveMixin) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR134_AudioReactiveMixin.md) |
| P4-COR135 | living_debug_overlay (AudioReactiveParticle) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR136 | living_debug_overlay (AudioReactiveParticleSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR137 | mood_temporal_patterns (AudioReactivePatternGenerator) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR137_AudioReactivePatternGenerator.md) |
| P4-COR138 | audio_reactive (AudioReactivePreset) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR138_AudioReactivePreset.md) |
| P4-COR139 | audio_reactivity (AudioReactivity) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR139_AudioReactivity.md) |
| P4-COR140 | unified_matrix_integration (AudioReactivityIntegrator) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR140_AudioReactivityIntegrator.md) |
| P4-COR141 | audio_reactor (AudioReactor) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR141_AudioReactor.md) |
| P4-COR142 | audio_reactor (AudioReactorManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR142_AudioReactorManager.md) |
| P4-COR143 | engine (AudioSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR143_AudioSource.md) |
| P4-COR144 | engine (AudioSourceType) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR144_AudioSourceType.md) |
| P4-COR145 | depth_audio (AudioSpectrum) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR145_AudioSpectrum.md) |
| P4-COR146 | audio_spectrum_trails (AudioSpectrumTrails) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR146_AudioSpectrumTrails.md) |
| P4-COR147 | new_effects (AudioStrobe) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR147_AudioStrobe.md) |
| P4-COR148 | __init__ (AudioSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR148_AudioSystem.md) |
| P4-COR149 | node_effect_audio (AudioTrailsNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR149_AudioTrailsNode.md) |
| P4-COR150 | audio_waveform_distortion (AudioWaveformDistortion) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR150_AudioWaveformDistortion.md) |
| P4-COR151 | websocket_handler (AudioWebSocketHandler) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR151_AudioWebSocketHandler.md) |
| P4-COR152 | depth_audio (DepthAudioMapping) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR152_DepthAudioMapping.md) |
| P4-COR153 | depth_audio (DepthAudioReactor) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR153_DepthAudioReactor.md) |
| P4-COR154 | audio_reactive_effects (DreamModeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR154_DreamModeEffect.md) |
| P4-COR155 | audio_reactive_effects (EnergyCascadeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR155_EnergyCascadeEffect.md) |
| P4-COR156 | audio_reactive (EnvelopeFollower) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR156_EnvelopeFollower.md) |
| P4-COR157 | audio_reactive_effects (KaleidoscopeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR157_KaleidoscopeEffect.md) |
| P4-COR158 | pll_sync (MIDIClockSync) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR158_MIDIClockSync.md) |
| P4-COR159 | config_types (MIDIConfig) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR159_MIDIConfig.md) |
| P4-COR160 | unified_hydra_extensions (MIDIHydraExtension) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR160_MIDIHydraExtension.md) |
| P4-COR161 | midi_controller (MIDIMapping) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR161_MIDIMapping.md) |
| P4-COR162 | midi (MIDIMessage) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR162_MIDIMessage.md) |
| P4-COR163 | midi (MIDIMessageType) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR163_MIDIMessageType.md) |
| P4-COR164 | midi_controller (MIDIMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR164_MIDIMode.md) |
| P4-COR165 | midi_presets (MIDIPresetManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR165_MIDIPresetManager.md) |
| P4-COR166 | midi_mapper (MidiMapper) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR166_MidiMapper.md) |
| P4-COR167 | midi_mapper (MidiMapping) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR167_MidiMapping.md) |
| P4-COR168 | matrix_nodes (MidiToParamNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR168_MidiToParamNode.md) |
| P4-COR169 | config_types (OSCConfig) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR169_OSCConfig.md) |
| P4-COR170 | osc_controller (OSCController) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR170_OSCController.md) |
| P4-COR171 | osc_dispatcher (OSCDispatcher) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR171_OSCDispatcher.md) |
| P4-COR172 | osc_query_server (OSCQueryHTTPRequestHandler) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR172_OSCQueryHTTPRequestHandler.md) |
| P4-COR173 | osc_query_server (OSCQueryParameter) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR173_OSCQueryParameter.md) |
| P4-COR174 | osc_query_server (OSCQueryServer) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR174_OSCQueryServer.md) |
| P4-COR175 | audio_reactive (OnsetDetector) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR175_OnsetDetector.md) |
| P4-COR176 | generators (OscEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR176_OscEffect.md) |
| P4-COR177 | oscilloscope (OscilloscopeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR177_OscilloscopeEffect.md) |
| P4-COR178 | node_effect_lost_artifacts (OscilloscopeNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR178_OscilloscopeNode.md) |
| P4-COR179 | matrix_nodes (ParamToMidiNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR179_ParamToMidiNode.md) |
| P4-COR180 | quantum_analyzer (QuantumAudioAnalyzer) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR180_QuantumAudioAnalyzer.md) |
| P4-COR181 | quantum_reactor (QuantumAudioReactor) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR181_QuantumAudioReactor.md) |
| P4-COR182 | audio_reactive (SpectralColorMapper) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR182_SpectralColorMapper.md) |
| P4-COR183 | audio_reactive_3d_scene_ultimate (TimeTravelSession) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR183_TimeTravelSession.md) |
| P4-COR184 | audio_reactive_effects (VHSScanlinesEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR184_VHSScanlinesEffect.md) |
| P4-COR185 | av_mixer (VideoAudioMixerModule) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR185_VideoAudioMixerModule.md) |
| P4-COR186 | audio_reactive_3d_scene_ultimate (WorldMemory) | P0 | ⬜ PENDING SKELETON (Pass 1) | [link](docs/specs/P4-COR186_WorldMemory.md) |
| P4-COR187 | video_sources (AstraDepthSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR188 | astra_linux (AstraLinuxSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR189 | astra_native (AstraNativeSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR190 | vision_source (AstraSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR191 | camera (Camera3D) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR192 | multi_camera_manager (CameraCalibration) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR193 | camera_config_manager (CameraConfigManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR194 | multi_camera_fusion (CameraPose) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR195 | camera_profiles_new (CameraProfile) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR196 | camera_profiles_new (CameraProfileConfig) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR197 | camera_profiles_new (CameraProfileManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR198 | camera_profiles (CameraType) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR199 | dmx_bridge (DMXBridge) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR200 | lighting_bridge (DMXChannel) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR201 | dmx_engine (DMXEngine) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR202 | dmx_input (DMXInputController) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR203 | dmx_input (DMXInputUniverse) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR204 | sacn_monitor (DMXMonitor) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR205 | dmx_production_ws_handler (DMXProductionWSHandler) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR206 | dmx_bridge (DMXScene) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR207 | dmx_input (DMXShortcut) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR208 | lighting_bridge (DMXUniverse) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR209 | dmx_ws_handler (DMXWSHandler) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR210 | depth_calibration (DepthCameraCalibration) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR211 | accelerator (HardwareAccelerator) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR212 | vjlivest_license_system (HardwareBinding) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR213 | accelerator (HardwareCapabilities) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR214 | hardware_discovery (HardwareDiscovery) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR215 | hardware_hal (HardwareHAL) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR216 | hardware_scanner (HardwareIdentity) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR217 | app (HardwareIntegration) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR218 | hardware_manager (HardwareManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR219 | hardware_manifest (HardwareManifest) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR220 | hardware_manifest (HardwareManifestManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR221 | hardware_mapper (HardwareMapper) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR222 | hardware_mapper (HardwareMapping) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR223 | hardware (HardwareMixin) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR224 | hardware_report (HardwareReportGenerator) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR225 | hardware_scanner (HardwareScanner) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR226 | network (IPCameraSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR227 | hotplug_detector (MacVDCameraDetector) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR228 | multi_camera_fusion (MultiCameraFusion) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR229 | multi_camera_manager (MultiCameraManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR230 | vision_source (NDIVisionSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR231 | camera (PhysicalCameraSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR232 | video_sources_realsense (RealSenseConfig) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR233 | realsense (RealSenseSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR234 | silver_visions (SilverVisionsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR235 | node_datamosh (TunnelVisionNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR236 | vision_source (UVCVisionSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR237 | vision_source (VisionBackend) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR238 | vision_source (VisionMetadata) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR239 | vision_node (VisionNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR240 | vision_source (VisionSource) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR241 | vision_watchdog (VisionWatchdog) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR242 | befaco (ADSR) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR243 | node_modulation_befaco (ADSRNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR244 | arvr_modules (ARCanvas) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR245 | arvr_modules (ARController) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR246 | arvr_modules (ARScene) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR247 | engine (ARVRMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR248 | engine (ARVRPipeline) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR249 | ascii (ASCIIEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR250 | node_effect_omniverse (ASCIINode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR251 | decoder (AVDecoder) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR252 | accelerator (AccelerationMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR253 | secure_vault (AccessControl) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR254 | secure_vault (AccessPolicy) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR255 | security_manager (AccessToken) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR256 | gamification (Achievement) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR257 | awesome_collaborative_creation (AchievementCategory) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR258 | awesome_collaborative_creation (AchievementSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR259 | gamification (AchievementType) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR260 | rhythm_visual_effects (ActiveBeatEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR261 | intelligent_visual_response (ActiveEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR262 | collaboration (ActivityHeatmapPoint) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR263 | adaptive_config (AdaptationStrategy) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR264 | brush_engines (AdaptiveBrushStroke) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR265 | vcv_effects (AdaptiveContrastEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR266 | video_buffer_manager (AdaptiveQualityScaler) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR267 | adaptive_resolution (AdaptiveResolutionController) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR268 | models (AdminUser) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR269 | routes (AdminUserCreate) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR270 | routes (AdminUserResponse) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR271 | advanced_output (AdvancedOutputEngine) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR272 | particles_3d (AdvancedParticle3DSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR273 | enhanced_collaboration_effects (AdvancedParticlePhysics) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR274 | error_tracking (AlertManager) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR275 | node_effect_analog (AnalogBlurNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR276 | node_effect_analog (AnalogColorNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR277 | node_effect_analog (AnalogContrastNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR278 | node_effect_analog (AnalogEchoNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR279 | node_effect_analog (AnalogHDRNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR280 | unified_effects (AnalogPulse) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR281 | node_effect_analog (AnalogResonantNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR282 | node_effect_analog (AnalogSolarizeNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR283 | analog_tv (AnalogTVEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR284 | node_effect_omniverse (AnalogTVNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR285 | node_effect_analog (AnalogZoomNode) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR286 | anchor_evolution (AnchorEvolution) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR287 | ui_enhancements (Animation) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR288 | ui_enhancements (AnimationType) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR289 | ai_assistant (Anomaly) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR290 | predictive_failure_detection (AnomalyDetector) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR291 | anthropic_provider (AnthropicModelProvider) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR292 | llm_service (AnthropicProvider) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR293 | brush_engines (AntigravityBrush) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR294 | bootstrap (AppInitializer) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR295 | application_metrics (ApplicationMetrics) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR296 | arbhar_granularizer (ArbharGranularizer) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P4-COR297 | intelligent_documentation (ArchitectureGenerator) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR298 | memory_pool (ArrayPool) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR299 | collaborative_canvas (ArtGallery) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(out of scope for Alpha)* |
| P4-COR300 | lighting_bridge (ArtNetController) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy |
| P1-R1 | OpenGL rendering context (ModernGL) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/render/opengl_context.py` — OpenGLContext, 10/10 tests ✅ |
| P1-R2 | GPU pipeline + framebuffer management (RAII) | P0 | ⬜ PENDING SKELETON (Pass 1) | `chain.py`, `program.py`, `framebuffer.py` - tests pass, 82% coverage ✅ |
| P1-R3 | Shader compilation system (GLSL + Milkdrop) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/render/shader_compiler.py` — 7 tests @ 81% cov ✅ — 2026-02-22 |
| P1-R4 | Texture manager (pooled, leak-free) | [Agent name] | ⬜ PENDING SKELETON (Pass 1) | 80% coverage mapped across ModernGL dictionary buffers and fallback decoded stream paths. (2026-02-22) |
| P1-R5 | Core rendering engine (60fps loop) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/render/engine.py` — RenderEngine, 8/8 tests ✅ 2026-02-22 |
| P1-A1 | FFT + waveform analysis engine | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P1-A2 | Real-time beat detection | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P1-A3 | Audio-reactive effect framework | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P1-A4 | Multi-source audio input | P1 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P1-N1 | UnifiedMatrix + node registry (manifest-based) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P1-N1_node_registry.md` — spec approved, implementation started |
| P1-N2 | Node types — full collection from both codebases | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P1-N2_node_types.md` — spec approved, implementation started |
| P1-N3 | State persistence (save/load) | P1 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P1-N3_state_persistence.md` — spec approved, implementation started |
| P1-N4 | Visual node graph UI | P1 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P1-N4_node_graph_ui.md` — spec approved, implementation started |
| P1-P1 | Plugin registry (manifest.json based) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/registry.py` — 108 tests @ 81.62% cov — 2026-02-21 |
| P1-P2 | Plugin loading + Pydantic validation | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/loader.py` — included in test suite |
| P1-P3 | Hot-reloadable plugin system | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P1-P3_plugin_hot_reload.md` — spec approved, implementation started |
| P1-P4 | Plugin discovery (auto-scan) | P0 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P1-P4_plugin_scanner.md` — spec approved, implementation started |
| P1-P5 | Plugin sandboxing | P1 | ⬜ PENDING SKELETON (Pass 1) | `docs/specs/P1-P5_plugin_sandbox.md` — spec approved, implementation started |
| P1-S1 | Config manager (centralized app config, env vars, YAML) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/config_manager.py` — CameraConfigManager found in Qdrant |
| P1-S2 | Video buffer manager (circular buffer, shared across effects) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/video_buffer_manager.py` — used by datamosh, granular, depth |
| P1-S3 | Preset system (save/load/recall VJ setups) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/preset_manager.py` — found in Qdrant, no BOARD task existed |
| P1-S4 | Display / output manager (multi-monitor, NDI out, Syphon) | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/display_manager.py` — routing to projectors, stream outputs |
| P1-S5 | Timeline / sequencer (show programming, cue lists) | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/timeline.py` — sequence automation, timed transitions |
| P1-S6 | Camera config manager (depth camera calibration) | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/camera_config_manager.py` — found in Qdrant |
| P2-D1 | DMX512 core engine + fixture profiles | P0 | ⬜ PENDING SKELETON (Pass 1) | Spec ready: `docs/specs/P2-D1_dmx_engine.md` |
| P2-D2 | ArtNet + sACN output | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P2-D3 | DMX FX engine (chases, rainbow, strobe) | P0 | ⬜ PENDING SKELETON (Pass 1) | Spec ready: `docs/specs/P2-D3_dmx_fx.md` |
| P2-D4 | Show control system | P1 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P2-D5 | Audio-reactive DMX | P1 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P2-D6 | DMX WebSocket handler | P1 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/core/dmx/websocket.py` — DmxWebSocketHandler, 7/7 tests ✅ 2026-02-22 |
| P2-H1 | MIDI controller input | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P2-H2 | Audio reactive input analysis block | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/audio/...` — Audio Analyzer Pipeline Active |
| P2-H3 | Orbbec Astra / Kinect 2 Depth Camera | P1 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/astra.py` — AstraDepthCamera, 5/5 tests ✅ 2026-02-22 |
| P2-H4 | NDI video transport (full hub + streams) | P1 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/ndi.py` — NDIHub/NDISender/NDIReceiver, 9/9 tests ✅ 2026-02-22 |
| P2-H5 | Spout support (Windows video sharing) | P2 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/spout.py` — SpoutManager, 5/5 tests ✅ 2026-02-22 |
| P2-H6 | Gamepad input (GLFW backend) | P2 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/gamepad.py` — GamepadPlugin, 4/4 tests ✅ 2026-02-22 |
| P2-H7 | Laser safety system | P1 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/hardware/laser.py` — LaserSafetySystem, 8/8 tests ✅ 2026-02-22 |
| P2-X1 | Multi-node coordination (ZeroMQ) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/sync/zmq_coordinator.py` — ZmqCoordinator, 4/4 tests ✅ 2026-02-22 |
| P2-X2 | Timecode sync (LTC/MTC/NTP) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/sync/timecode.py` — TimecodeEngine + sources, 28/28 tests ✅ 2026-02-21 |
| P2-X3 | Output mapping + screen warping | P1 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/video/output_mapper.py` — OutputMapper, 6/6 tests ✅ 2026-02-22 |
| P2-X4 | Projection mapping (warp, edge-blend, mask) | P1 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P2-I1 | Error handling strategy (graceful degradation, GPU fail, camera disconnect) | P0 | ⬜ PENDING SKELETON (Pass 1) | No legacy spec — must be designed from scratch |
| P2-I2 | Logging framework (structured logging, per-module levels, file + console) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy: scattered print() calls — needs unified approach |
| P2-I3 | Testing infrastructure (GL mock, fixture library, headless CI support) | P0 | ⬜ PENDING SKELETON (Pass 1) | Existing: `gl_stub` pattern, needs formal spec |
| P2-I4 | CI/CD pipeline (GitHub Actions, lint, test, coverage, deploy) | P1 | ⬜ PENDING SKELETON (Pass 1) | Existing: `.github/workflows/ci.yml` — needs cleanup spec |
| P2-I5 | Performance monitoring (runtime FPS, memory, GPU stats, leak detection) | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: ad-hoc timing — needs real-time dashboard |
| P2-I6 | Documentation generation (API docs, plugin docs, user guide) | P2 | ⬜ PENDING SKELETON (Pass 1) | Existing: docstrings — needs Sphinx/MkDocs spec |
| P2-U1 | UI framework (desktop GUI — Qt/Dear ImGui/web-based) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy: Qt5 in vjlive, tkinter in VJlive-2 — needs decision |
| P2-U2 | REST/WebSocket API (remote control, browser UI, mobile control) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy: Flask API in vjlive — needs FastAPI spec |
| P2-U3 | Video source management (capture cards, file playback, live cameras) | P0 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/video_source.py` — needs unified spec |
| P2-U4 | Recording / output to file (capture performance to MP4/ProRes) | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: scattered ffmpeg calls — needs proper spec |
| P2-U5 | Transition engine (crossfade, cut, dissolve between sources/scenes) | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/transitions.py` — found in Qdrant |
| P2-U6 | Scene management (group effects into scenes, scene switching) | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/scene_manager.py` — found in Qdrant |
| P2-U7 | MIDI mapping engine (learn mode, CC→parameter, mapping presets) | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/midi_mapper.py` — found in Qdrant |
| P2-U8 | Media asset management (images, videos, SVGs used by effects) | P2 | ⬜ PENDING SKELETON (Pass 1) | No legacy spec — needs design |
| P2-T1 | Audio-to-Video DSP translation pass (convert audio DSP → video equivalents) | P0 | ⬜ PENDING SKELETON (Pass 1) | All audio DSP effects must become video effects with audio-reactive inputs |
| P2-T2 | Plugin packaging / distribution (how users install third-party plugins) | P1 | ⬜ PENDING SKELETON (Pass 1) | No legacy spec — needs design for .vjplugin format or pip |
| P3-VD7 | Depth Data Mux (DepthDataMuxEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/p3_vd7.py` — DepthDataMuxEffect, 8/8 tests ✅ 2026-02-22 |
| P3-VD-Beta1 | Depth Loop Injection (DepthLoopInjectionPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/p3_vd_beta1.py` — DepthLoopInjectionPlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD-Beta2 | Depth Parallel Universe (DepthParallelUniversePlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/p3_vd_beta2.py` — DepthParallelUniversePlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD-Beta3 | Depth Portal Composite (DepthPortalCompositePlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/p3_vd_beta3.py` — DepthPortalCompositePlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD06 | Depth Neural Quantum Hyper Tunnel (DepthNeuralQuantumHyperTunnelPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_neural_quantum_hyper_tunnel.py` — DepthNeuralQuantumHyperTunnelPlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD07 | Depth Reality Distortion (RealityDistortionPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_reality_distortion.py` — RealityDistortionPlugin, 7/7 tests ✅ 2026-02-22 |
| P3-VD33 | Depth Distance Filter (DepthDistanceFilterPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD34 | Depth Dual (DepthDualPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD35 | Depth Edge Glow (DepthEdgeGlowPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD36 | Depth Effects (DepthEffectPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD09 | Depth Acid Fractal (DepthAcidFractalPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_acid_fractal.py` — DepthAcidFractalPlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD15 | Depth Aware Compression (DepthAwareCompressionPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_aware_compression.py` — DepthAwareCompressionPlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD10 | Depth Blur (DepthBlurPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_blur.py` — DepthBlurPlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD29 | Depth Camera Splitter (DepthCameraSplitterEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD26 | Depth Acid Fractal Datamosh (DepthAcidFractalDatamoshEffectPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD11 | Depth Color Grade (DepthColorGradePlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_color_grade.py` — DepthColorGradePlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD12 | Depth Contour Datamosh (DepthContourDatamoshPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_contour_datamosh.py` — DepthContourDatamoshPlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD32 | Depth Data Mux (DepthDataMuxEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD33 | Depth Distance Filter (DepthDistanceFilterEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD34 | Depth Dual (DepthDualEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD16 | Depth Edge Glow (DepthEdgeGlowPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_edge_glow.py` — DepthEdgeGlowPlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD36 | Depth Effects (DepthEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD37 | Depth Effects (DepthPointCloudEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD38 | Depth Effects (DepthPointCloud3DEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD39 | Depth Effects (DepthMeshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD40 | Depth Effects (DepthContourEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD41 | Depth Effects (DepthParticle3DEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD42 | Depth Effects (DepthDistortionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD43 | Depth Effects (DepthFieldEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD44 | Depth Effects (OpticalFlowEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Spec ready: `docs/specs/P3-EXT044_depth_effects_optical_flow_effect.md` |
| P3-VD45 | Depth Effects (BackgroundSubtractionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD13 | Depth Erosion Datamosh (DepthErosionDatamoshPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_erosion_datamosh.py` — DepthErosionDatamoshPlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD47 | Depth Feedback Matrix Datamosh (DepthFeedbackMatrixDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD48 | Depth Fog (DepthFogEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD14 | Depth Fracture Datamosh (DepthFractureDatamoshPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_fracture_datamosh.py` — DepthFractureDatamoshPlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD50 | Depth Fx Loop (DepthFXLoopEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD51 | Depth Groovy Datamosh (DepthGroovyDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD52 | Depth Holographic (DepthHolographicIridescenceEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD53 | Depth Liquid Refraction (DepthLiquidRefractionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD54 | Depth Loop Injection Datamosh (DepthLoopInjectionDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD55 | Depth Modular Datamosh (DepthModularDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD56 | Depth Modulated Datamosh (DepthModulatedDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD57 | Depth Mosaic (DepthMosaicEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD58 | Depth Mosh Nexus (DepthMoshNexus) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD59 | Depth Motion Transfer (DepthMotionTransferEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD60 | Depth Parallel Universe Datamosh (DepthParallelUniverseDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Spec ready: `docs/specs/P3-EXT060_depth_parallel_universe_datamosh_effect.md` |
| P3-VD61 | Depth Particle Shred (DepthParticleShredEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD62 | Depth Portal Composite (DepthPortalCompositeEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD63 | Depth Raver Datamosh (DepthRaverDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Spec ready: `docs/specs/P3-EXT063_depth_raver_datamosh_effect.md` |
| P3-VD64 | Depth Reverb (DepthReverbEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD65 | Depth Simulator (DepthSimulatorEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | Spec ready: `docs/specs/P3-EXT065_depth_simulator_effect.md` |
| P3-VD66 | Depth Slitscan Datamosh (DepthSlitScanDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD67 | Depth Temporal Echo (DepthTemporalEchoEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD68 | Depth Temporal Strat (DepthTemporalStratEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD05 | Depth Slice (DepthSliceEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_slice.py` — DepthSlicePlugin, 7/7 tests ✅ 2026-02-22 |
| P3-VD69 | Depth Vector Field Datamosh (DepthVectorFieldDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD70 | Depth Video Projection (DepthVideoProjectionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD71 | Depth Void Datamosh (DepthVoidDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD72 | datamosh_3d (DepthDisplacementEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/depth_displacement.py` — DepthDisplacementPlugin, 5/5 tests ✅ 2026-02-23 |
| P3-VD73 | datamosh_3d (DepthEchoEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD74 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD75 | quantum_depth_nexus_effect (QuantumDepthNexus) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P4-BA01 | B1to8 | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BA02 | BLFO | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BA03 | BMatrix81 | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BA04 | BPEQ6 | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BA05 | BSwitch | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BA06 | BVCF | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BA07 | BVCO | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BA08 | BVELO | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BA09 | NMix4 | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BA10 | NXFade | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-AU02 | Audio Reactive Effects (AudioParticleSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/audio_particle_system.py` — AudioParticleSystemPlugin, 14/14 tests ✅ 2026-02-23 |
| P4-AU03 | Audio Reactive Effects (AudioWaveformDistortion) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/audio_waveform_distortion.py` — 9/9 tests ✅ 2026-02-23 |
| P4-AU04 | Audio Reactive Effects (AudioSpectrumTrails) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/audio_spectrum_trails.py` — 9/9 tests ✅ 2026-02-23 |
| P4-AU05 | Audio Reactive Effects (AudioKaleidoscope) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/audio_kaleidoscope.py` — 8/8 tests ✅ 2026-02-23 |
| P4-AU06 | cosmic_tunnel_datamosh (CosmicTunnelDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/cosmic_tunnel_datamosh.py` — 8/8 tests ✅ 2026-02-23 |
| P4-AU07 | raymarched_scenes (AudioReactiveRaymarchedScenes) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/audio_reactive_raymarched_scenes.py` — 8/8 tests ✅ 2026-02-23 |
| P4-AU08 | vcv_video_generators (ByteBeatGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/bytebeat_generator.py` — 8/8 tests ✅ 2026-02-23 |
| P4-BF01 | V-Even | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BF02 | V-Morphader | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BF03 | V-Outs | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BF04 | V-Pony | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BF05 | V-Scope | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P4-BF06 | V-Voltio | ⬜ RESET | ⬜ PENDING SKELETON (Pass 1) |  |
| P5-MO03 | blend (ModulateEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/modulate.py` — 8/8 tests ✅ 2026-02-23 |
| P5-VE02 | analog_tv (AnalogTVEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/analog_tv.py` — 11/11 tests ✅ 2026-02-23 |
| P5-DM02 | bad_trip_datamosh (BadTripDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/bad_trip_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM03 | bass_cannon_datamosh (BassCannonDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/bass_cannon_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM04 | bass_therapy_datamosh (BassTherapyDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/bass_therapy_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM05 | blend (GlitchEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/glitch_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM06 | bullet_time_datamosh (BulletTimeDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/bullet_time_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM07 | cellular_automata_datamosh (CellularAutomataDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/cellular_automata_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM08 | cotton_candy_datamosh (CottonCandyDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/cotton_candy_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM09 | cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/cupcake_cascade_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM10 | datamosh (CompressionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/compression_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM11 | datamosh (DatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM12 | datamosh (PixelBloomEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/pixel_bloom_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM13 | datamosh (MeltEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/melt_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM14 | datamosh (PixelSortEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/pixel_sort_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM15 | datamosh (FrameHoldEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/frame_hold_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM16 | datamosh_3d (Datamosh3DEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/datamosh_3d.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM17 | datamosh_3d (LayerSeparationEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/layer_separation_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM18 | datamosh_3d (ShatterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/shatter_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM19 | dimension_splice_datamosh (DimensionSpliceDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/dimension_splice_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM20 | dolly_zoom_datamosh (DollyZoomDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/dolly_zoom_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM21 | face_melt_datamosh (FaceMeltDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/face_melt_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM22 | fracture_rave_datamosh (FractureRaveDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/fracture_rave_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM23 | liquid_lsd_datamosh (LiquidLSDDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/liquid_lsd_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM24 | mosh_pit_datamosh (MoshPitDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/mosh_pit_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM25 | neural_splice_datamosh (NeuralSpliceDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/neural_splice_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM26 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/particle_datamosh_trails.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM27 | plasma_melt_datamosh (PlasmaMeltDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/plasma_melt_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM28 | prism_realm_datamosh (PrismRealmDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/prism_realm_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM29 | sacred_geometry_datamosh (SacredGeometryDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/sacred_geometry_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM30 | spirit_aura_datamosh (SpiritAuraDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/spirit_aura_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM31 | temporal_rift_datamosh (TemporalRiftDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/temporal_rift_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM32 | tunnel_vision_datamosh (TunnelVisionDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/tunnel_vision_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM33 | unicorn_farts_datamosh (UnicornFartsDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/unicorn_farts_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM34 | void_swirl_datamosh (VoidSwirlDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/void_swirl_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM35 | volumetric_datamosh (VolumetricDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/volumetric_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM36 | volumetric_glitch (VolumetricGlitchEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/volumetric_glitch.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC06 | agent_avatar (TravelingAvatarEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/traveling_avatar.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC07 | agent_avatar (AgentAvatarEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/agent_avatar.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC08 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/ml_base_async.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC09 | ml_gpu_effects (MLStyleGLEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/ml_style_gl.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC10 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/ml_segmentation_blur.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC11 | neural_rave_nexus (NeuralRaveNexus) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/neural_rave_nexus.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC12 | quantum_consciousness_explorer (QuantumConsciousnessExplorer) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/quantum_consciousness_explorer.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC13 | trails (TrailsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/trails_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC14 | tunnel_vision_3 (QuantumConsciousnessSingularityEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/quantum_singularity.py` — 7/7 tests ✅ 2026-02-23 |
| P6-AG1 | Agent Bridge | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/agents/bridge.py` — 20/20 tests ✅ 2026-02-23 |
| P6-AG2 | Agent Physics — 16D manifold + gravity wells | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/agents/physics.py` + `manifold.py` — 22/22 tests ✅ 2026-02-23 |
| P6-AG3 | Agent Memory (50-snapshot system) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/agents/memory.py` — 13/13 tests ✅ 2026-02-23 |
| P6-AG4 | Agent Control UI | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/agents/` (bridge.step() publishes agent_state to context) — 62/62 tests ✅ 2026-02-23 |
| P6-GE06 | fractal_generator (FractalGenerator) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/fractal_generator.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE07 | generators (OscEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/osc_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE08 | generators (NoiseEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/noise_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE09 | generators (VoronoiEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/voronoi_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE10 | generators (GradientEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/gradient_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE11 | generators (MandalaEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/mandala_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE12 | generators (PlasmaEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/plasma_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE13 | generators (PerlinEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/perlin_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE14 | silver_visions (PathGeneratorEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/path_generator.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE15 | vcv_video_generators (HarmonicPatternsGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/harmonic_patterns.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE16 | vcv_video_generators (FMCoordinatesGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/fm_coordinates.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE17 | vcv_video_generators (MacroShapeGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/macro_shape.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE18 | vcv_video_generators (GranularVideoGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/granular_video.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE19 | vcv_video_generators (ResonantGeometryGen) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/resonant_geometry.py` — 7/7 tests ✅ 2026-02-23 |
| P6-P302 | particles_3d (AdvancedParticle3DSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/advanced_particle_3d.py` — 7/7 tests ✅ 2026-02-23 |
| P6-P303 | particles_3d (Particle3DSystem) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/particle_3d.py` — 7/7 tests ✅ 2026-02-23 |
| P6-P304 | shadertoy_particles (ShadertoyParticles) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/shadertoy_particles.py` — 7/7 tests ✅ 2026-02-23 |
| P6-P305 | vibrant_retro_styles (RadiantMeshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/radiant_mesh.py` — 7/7 tests ✅ 2026-02-23 |
| P7-U1 | Desktop GUI + SentienceOverlay easter egg | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/desktop_gui.py` (VJLiveGUIApp + SentienceOverlay) — 20/20 tests ✅ 2026-02-23 |
| P7-U2 | Web-based remote control | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/web_remote.py` (HTTP REST API + WS broadcaster) — 17/17 tests ✅ 2026-02-23 |
| P7-U3 | Collaborative Studio UI | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/desktop_gui.py` (CollaborativeStudio, role-based) — 6/6 tests ✅ 2026-02-23 |
| P7-U4 | Quantum Collaborative Studio | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/desktop_gui.py` (QuantumCollaborativeStudio, superposition) — 6/6 tests ✅ 2026-02-23 |
| P7-U5 | TouchOSC export / mobile interface | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/cli.py` (OSCLayoutExporter + address map JSON) — 8/8 tests ✅ 2026-02-23 |
| P7-U6 | CLI automation | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/cli.py` (ParamStore, PresetSequencer, argparse CLI) — 22/22 tests ✅ 2026-02-23 |
| P7-VE01 | V Sws (VSwsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/v_sws.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE02 | V Sws (HorizontalWaveEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/horizontal_wave.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE03 | V Sws (VerticalWaveEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/vertical_wave.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE04 | V Sws (RippleEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/ripple_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE05 | V Sws (SpiralWaveEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/spiral_wave.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE06 | ascii_effect (ASCIIEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/ascii_effect2.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE07 | bass_cannon_2 (BassCanon2) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/bass_cannon_2.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE08 | blend (FeedbackEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/feedback_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE09 | blend (BlendAddEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/blend_add.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE10 | blend (BlendMultEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/blend_mult.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE11 | blend (BlendDiffEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/blend_diff.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE12 | blend (ScanlinesEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/scanlines_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE13 | blend (VignetteEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/vignette_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE14 | blend (InfiniteFeedbackEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/infinite_feedback.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE15 | blend (BloomEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/bloom_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE16 | blend (BloomShadertoyEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/bloom_shadertoy.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE17 | blend (MixerEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/mixer_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE18 | blend_modes (_BlendMode) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/blend_modes_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE19 | chroma_key (ChromaKeyEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/chroma_key.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE20 | color (PosterizeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/posterize_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE21 | color (ContrastEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/contrast_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE22 | color (SaturateEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/saturate_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE23 | color (HueEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/hue_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE24 | color (BrightnessEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/brightness_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE25 | color (InvertEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/invert_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE26 | color (ThreshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/thresh_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE27 | color (RGBShiftEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/rgb_shift.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE28 | color (ColorCorrectEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/color_correct.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE29 | color_grade (ColorGradeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/color_grade2.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE30 | colorama (ColoramaEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/colorama.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE31 | displacement_map (DisplacementMapEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/displacement_map.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE32 | distortion (ChromaticDistortionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/chromatic_distortion.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE33 | distortion (PatternDistortionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/pattern_distortion.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE34 | dithering (DitheringEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/dithering_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE35 | fluid_sim (FluidSimEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/fluid_sim.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE36 | geometry (MandalascopeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/mandalascope.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE37 | geometry (RotateEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/rotate_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE38 | geometry (ScaleEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/scale_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE39 | geometry (PixelateEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/pixelate_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE40 | geometry (RepeatEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/repeat_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE41 | geometry (ScrollEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/scroll_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE42 | geometry (MirrorEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/mirror_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE43 | geometry (ProjectionMappingEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/projection_mapping2.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE44 | hyperion (VimanaHyperion) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/vimana_hyperion.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE45 | hyperspace_tunnel (HyperspaceTunnelEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/hyperspace_tunnel.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE46 | living_fractal_consciousness (LivingFractalConsciousness) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/living_fractal.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE47 | luma_chroma_mask (LumaChromaMaskEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/luma_chroma_mask.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE48 | lut_grading (LUTGradingEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/lut_grading.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE49 | milkdrop (MilkdropEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/milkdrop.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE50 | morphology (MorphologyEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/morphology_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE51 | oscilloscope (OscilloscopeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/oscilloscope_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE52 | plugin_template (CustomEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/custom_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE53 | pop_art_effects (BenDayDotsEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/ben_day_dots.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE54 | pop_art_effects (WarholQuadEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/warhol_quad.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE55 | r16_deep_mosh_studio (R16DeepMoshStudio) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/r16_deep_mosh.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE56 | r16_interstellar_mosh (R16InterstellarMosh) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/r16_interstellar.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE57 | reaction_diffusion (ReactionDiffusionEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/reaction_diffusion.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE58 | resize_effect (ResizeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/resize_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE59 | rutt_etra_scanline (RuttEtraScanlineEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/rutt_etra.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE60 | silver_visions (VideoOutEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/video_out.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE61 | silver_visions (ImageInEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/image_in.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE62 | silver_visions (CoordinateFolderEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/coordinate_folder.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE63 | silver_visions (AffineTransformEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/affine_transform.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE64 | silver_visions (PreciseDelayEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/precise_delay.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE65 | slit_scan (SlitScanEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/slit_scan.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE66 | sync_eater (SyncEaterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/sync_eater.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE67 | time_remap (TimeRemapEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/time_remap.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE68 | vcv_video_effects (GaussianBlurEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/gaussian_blur.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE69 | vcv_video_effects (MultibandColorEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/multiband_color.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE70 | vcv_video_effects (HDRToneMapEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/hdr_tonemap.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE71 | vcv_video_effects (SolarizeEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/solarize_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE72 | vcv_video_effects (ResonantBlurEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/resonant_blur.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE73 | vcv_video_effects (AdaptiveContrastEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/adaptive_contrast.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE74 | vcv_video_effects (SpatialEchoEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/spatial_echo.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE75 | vcv_video_effects (DelayZoomEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/delay_zoom.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE76 | vibrant_retro_styles (RioAestheticEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/rio_aesthetic.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE77 | vimana (Vimana) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/vimana.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE78 | vimana_hyperion_ultimate (VimanaHyperionUltimate) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/vimana_hyperion_ultimate.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE79 | vimana_synth (VimanaEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/vimana_synth.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE80 | visualizer (VisualizerEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/visualizer_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE81 | visualizer (SpectrumAnalyzerEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/spectrum_analyzer.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE82 | visualizer (VUMeterEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/plugins/vu_meter.py` — 7/7 tests ✅ 2026-02-23 |

## 📊 Summary
- **Pass 1/2 Completed:** ~110 specs
- **Pass 1/2 Queued:** ~900 specs
- **Pass 3 Queued:** ~110 specs awaiting Frontier Analysis
| P1-QDRANT001 | Create Panel Background | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `USEDGIT/developer_tools/inkscape_plugins/create_panel_background.py` |
| P1-QDRANT002 | Quantum Neural Evolution | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `VJlive-2/plugins/quantum_neural_evolution.py` |
| P1-QDRANT003 | Chromatic Aberration | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/chromatic_aberration.py` |
| P1-QDRANT004 | Example Glitch Effect | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/example_glitch_effect.py` |
| P1-QDRANT005 | Run Depth Demo | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/run_depth_demo.py` |
| P1-QDRANT006 | Run Ml Demo | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/run_ml_demo.py` |
| P1-QDRANT007 | Time Machine Demo | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/time_machine_demo.py` |
| P1-QDRANT008 | Use Automation | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/use_automation.py` |
| P1-QDRANT009 | Use Mask Manager | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/use_mask_manager.py` |
| P1-QDRANT010 | Use Midi Presets | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/use_midi_presets.py` |
| P1-QDRANT011 | Use Ml Effects | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/use_ml_effects.py` |
| P1-QDRANT012 | Use Preset Manager | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/use_preset_manager.py` |
| P1-QDRANT013 | Use Recorder | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/use_recorder.py` |
| P1-QDRANT014 | Use Sequencer | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/use_sequencer.py` |
| P1-QDRANT015 | Use Shader Manager | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/use_shader_manager.py` |
| P1-QDRANT016 | Use Volumetric Datamosh | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/examples/use_volumetric_datamosh.py` |
| P1-QDRANT017 | Gpu Compatibility | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/gpu_compatibility.py` |
| P1-QDRANT018 | Marketplace Client | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/marketplace_client.py` |
| P1-QDRANT019 | Masking | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/masking.py` |
| P1-QDRANT020 | Mimeophon Control Bridge | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/mimeophon_control_bridge.py` |
| P1-QDRANT021 | Mimeophon Video | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/mimeophon_video.py` |
| P1-QDRANT022 | Planetary Lfos | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/planetary_lfos.py` |
| P1-QDRANT023 | Plugin Api | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/plugin_api.py` |
| P1-QDRANT024 | Plugin Isolation | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/plugin_isolation.py` |
| P1-QDRANT025 | Plugin Loader | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/plugin_loader.py` |
| P1-QDRANT026 | Satanonaut Plugin | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/satanonaut_plugin.py` |
| P1-QDRANT027 | Satanonaut Video | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/satanonaut_video.py` |
| P1-QDRANT028 | Shader Hot Reload | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/shader_hot_reload.py` |
| P1-QDRANT029 | Simple Mimeophon Video | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/simple_mimeophon_video.py` |
| P1-QDRANT030 | Texture 3D Integration | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/texture_3d_integration.py` |
| P1-QDRANT031 | Texture 3D Top | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/texture_3d_top.py` |
| P1-QDRANT032 | Texture 3D Websocket | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/texture_3d_websocket.py` |
| P1-QDRANT033 | Time Machine Top | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/time_machine_top.py` |
| P1-QDRANT034 | V Jumbler | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/v_jumbler.py` |
| P1-QDRANT035 | Collaborative Creation Panel | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `gui/plugins/collaborative_creation_panel.py` |
| P1-QDRANT036 | Debug Overlay Controls | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `gui/plugins/debug_overlay_controls.py` |
| P1-QDRANT037 | Mimeophon Video Panel | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `gui/plugins/mimeophon_video_panel.py` |
| P1-QDRANT038 | Style Transfer Ui | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `gui/plugins/style_transfer_ui.py` |
| P1-QDRANT039 |  Add Groups | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/_add_groups.py` |
| P1-QDRANT040 |  Refactor Befaco | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/_refactor_befaco.py` |
| P1-QDRANT041 |  Refactor Bogaudio | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/_refactor_bogaudio.py` |
| P1-QDRANT042 |  Refactor Bogaudio V2 | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/_refactor_bogaudio_v2.py` |
| P1-QDRANT043 |  Refactor Remaining | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/_refactor_remaining.py` |
| P1-QDRANT044 |  Verify | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/_verify.py` |
| P1-QDRANT045 | Vbogaudio Extra | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vbogaudio/vbogaudio_extra.py` |
| P1-QDRANT046 | Vcontour | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vcontour/vcontour.py` |
| P1-QDRANT047 | Ffmpeg Filter | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vcore/ffmpeg_filter.py` |
| P1-QDRANT048 | Milkdrop Equations | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vcore/milkdrop_equations.py` |
| P1-QDRANT049 | Milkdrop Parser | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vcore/milkdrop_parser.py` |
| P1-QDRANT050 | Milkdrop Shaders | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vcore/milkdrop_shaders.py` |
| P1-QDRANT051 | Rgb Separator | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vcore/rgb_separator.py` |
| P1-QDRANT052 | Depth Slice Effect | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/depth_slice_effect.py` |
| P1-QDRANT053 | Hap Compatibility Layer | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/hap_compatibility_layer.py` |
| P1-QDRANT054 | R16 Bad Trip | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_bad_trip.py` |
| P1-QDRANT055 | R16 Block Mosh | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_block_mosh.py` |
| P1-QDRANT056 | R16 Cosmic Tunnel | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_cosmic_tunnel.py` |
| P1-QDRANT057 | R16 Face Melt | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_face_melt.py` |
| P1-QDRANT058 | R16 Feedback Mosh | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_feedback_mosh.py` |
| P1-QDRANT059 | R16 Hyper Slice | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_hyper_slice.py` |
| P1-QDRANT060 | R16 Interlace Mosh | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_interlace_mosh.py` |
| P1-QDRANT061 | R16 Liquid Mosh | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_liquid_mosh.py` |
| P1-QDRANT062 | R16 Metric Scan | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_metric_scan.py` |
| P1-QDRANT063 | R16 Point Cloud | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_point_cloud.py` |
| P1-QDRANT064 | R16 Topography | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/r16_topography.py` |
| P1-QDRANT065 | Showcase Demo | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vdepth/showcase_demo.py` |
| P1-QDRANT066 | Vmi Utilities | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vmi_utilities/vmi_utilities.py` |
| P1-QDRANT067 | Vmoddemix Core | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vmoddemix/vmoddemix_core.py` |
| P1-QDRANT068 | Parity Test | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vtempi/parity_test.py` |
| P1-QDRANT069 | Plugin Validator | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/plugins/plugin_validator.py` |
| P1-QDRANT070 | Datamosh Collaborative Panel | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `gui/plugins/datamosh_collaborative_panel.py` |
| P1-QDRANT071 |   Init  .Ultimate | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/core/effect_vimana_hyperion/__init__.ultimate.py` |
| P1-QDRANT072 | Vg Lib | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/core/maths/vg_lib.py` |
| P1-QDRANT073 | Make Noise Function | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/core/modulation_function/make_noise_function.py` |
| P1-QDRANT074 | Mutable Utilities | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/core/modulation_mutable_utilities/mutable_utilities.py` |
| P1-QDRANT075 | Playground | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/core/quantum_audio/playground.py` |
| P1-QDRANT076 | Gl Helpers | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/utils/gl_helpers.py` |
| P1-QDRANT077 | Test Colorama | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `tests/plugins/vcore/test_colorama.py` |
| P1-QDRANT078 | Vbefaco Core | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `/home/happy/vjlive_codebases/vjlive1/plugins/vbefaco/vbefaco_core.py` |
| P1-QDRANT079 | Enhanced Collaboration Overlay | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `/home/happy/vjlive_codebases/vjlive1/gui/plugins/enhanced_collaboration_overlay.py` |
| P1-QDRANT080 | Vbogaudio Filter Env | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `/home/happy/vjlive_codebases/vjlive1/plugins/vbogaudio/vbogaudio_filter_env.py` |
| P1-QDRANT081 | Vbogaudio Mix Util | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `/home/happy/vjlive_codebases/vjlive1/plugins/vbogaudio/vbogaudio_mix_util.py` |
| P1-QDRANT082 | Vbefaco Utils | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `/home/happy/vjlive_codebases/vjlive1/plugins/vbefaco/vbefaco_utils.py` |
| P1-QDRANT083 | Collaboration Overlay | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `/home/happy/vjlive_codebases/vjlive1/gui/plugins/collaboration_overlay.py` |
| P1-QDRANT084 | Vmi Generators | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `/home/happy/vjlive_codebases/vjlive1/plugins/vmi_generators/vmi_generators.py` |
| P1-QDRANT085 | Vbogaudio Osc | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `/home/happy/vjlive_codebases/vjlive1/plugins/vbogaudio/vbogaudio_osc.py` |
| P1-QDRANT086 | Rene Engine | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `/home/happy/vjlive_codebases/vjlive1/plugins/vmake_noise/rene_engine.py` |
