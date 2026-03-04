# VJLive3 Project Board
**Version:** 3.4 | **Last Updated:** 2026-02-27 | **Manager:** ANTIGRAVITY (Overseer)

> [!IMPORTANT]
> **REVISED 4-PHASE PIPELINE ARCHITECTURE (STRICT)**
> - **Phase 1 (Pass 1):** Qwen generates initial skeleton specs.
> - **Phase 2 (Pass 2):** Roo Code fleshes out the specs.
> - **⛔ BLOCKER:** NOTHING ELSE HAPPENS until Phase 2 is 100% Complete and this board is 100% DONE. Do not proceed to Phase 3.
> - **Phase 3 (Pass 3):** Global Analysis (Mermaid Architecture Map).
> - **Phase 4 (Pass 4):** Execution (Writing Production Code).
> 
> - 🟩 **DONE**: Specs that have survived Phase 2 and are now awaiting Phase 3.
> - ⬜ **TODO**: Specs currently queued for Phase 1 or Phase 2 generation.

## 🏁 Milestones

### Phase 0: System Boot & Verification
| ID    | Component | Phase | Status | Notes |
|-------|-----------|-------|--------|-------|

## 📦 The Unified Spec Queue (Pass 1 & Pass 2)
| ID | Plugin / Effect Task | Phase | Status | Legacy Path / Notes |
|---|---|---|---|---|
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
| P3-EXT012 | depth_effects (BackgroundSubtractionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out (P3-EXT011) |
| P3-EXT013 | bad_trip_datamosh (BadTripDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/bad_trip_datamosh.py` — 12-param horror datamosh, 21 tests ✅ 2026-02-23 |
| P3-EXT014 | bass_cannon_datamosh (BassCannonDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT015 | bass_cannon_2 (BassCanon2) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/bass_cannon_2.py` — 30-param neural rave cannon, 24 tests ✅ 2026-02-23 |
| P3-EXT016 | bass_therapy_datamosh (BassTherapyDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BassTherapyDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT017 | pop_art_effects (BenDayDotsEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT018 | blend (BlendAddEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT019 | blend (BlendDiffEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BlendDiffEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT020 | blend (BlendMultEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT021 | blend (BloomEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — BloomEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out → P3-EXT021_BloomEffect.md |
| P3-EXT022 | blend (BloomShadertoyEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | *(duplicate — BloomShadertoyEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT023 | color (BrightnessEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — BrightnessEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out → P3-EXT023_BrightnessEffect.md |
| P3-EXT024 | bullet_time_datamosh (BulletTimeDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — BulletTimeDatamoshEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out → P3-EXT024_BulletTimeDatamoshEffect.md |
| P3-EXT025 | vcv_video_generators (ByteBeatGen) | P0 | 🟦 IN PROGRESS (--help) | *(duplicate — ByteBeatGen already shipped in P4/P5/P6/P7)* |
| P3-EXT026 | cellular_automata_datamosh (CellularAutomataDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — CellularAutomataDatamoshEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT027 | chroma_key (ChromaKeyEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — ChromaKeyEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT028 | distortion (ChromaticDistortionEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — ChromaticDistortionEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT029 | color (ColorCorrectEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — ColorCorrectEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT030 | color (ColoramaEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — ColoramaEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT031 | quantum_consciousness_explorer (ConsciousnessLevel) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT032 | tunnel_vision_3 (ConsciousnessNet) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT033 | consciousness_neural_network (ConsciousnessNeuralNetwork) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT034 | color (ContrastEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — ContrastEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT035 | cosmic_tunnel_datamosh (CosmicTunnelDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — CosmicTunnelDatamoshEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT036 | cotton_candy_datamosh (CottonCandyDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — CottonCandyDatamoshEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT037 | cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — CupcakeCascadeDatamoshEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT038 | datamosh_3d (Datamosh3DEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — Datamosh3DEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT039 | vcv_video_effects (DelayZoomEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — DelayZoomEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT040 | depth_acid_fractal (DepthAcidFractalPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/depth_acid_fractal.py` — 6-param depth-reactive fractal, 5 tests ✅ 2026-02-23 |
| P3-EXT041 | depth_camera_splitter (DepthCameraSplitterEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — DepthCameraSplitterEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT042 | depth_data_mux (DepthDataMuxEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — DepthDataMuxEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT043 | datamosh_3d (DepthDisplacementEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT044 | depth_distance_filter (DepthDistanceFilterEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — DepthDistanceFilterEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT045 | depth_effects (DepthDistortionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — DepthDistortionEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT046 | depth_dual (DepthDualEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — DepthDualEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT047 | datamosh_3d (DepthEchoEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — DepthEchoEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT048 | depth_fx_loop (DepthFXLoopEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — DepthFXLoopEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT049 | depth_feedback_matrix_datamosh (DepthFeedbackMatrixDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — DepthFeedbackMatrixDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT050 | depth_effects (DepthFieldEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — DepthFieldEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT051 | depth_fog (DepthFogEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — DepthFogEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT052 | depth_groovy_datamosh (DepthGroovyDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — DepthGroovyDatamoshEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT053 | depth_holographic (DepthHolographicIridescenceEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — DepthHolographicIridescenceEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT054 | depth_loop_injection_datamosh (DepthLoopInjectionDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT055 | depth_effects (DepthMeshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | (duplicate — DepthMeshEffect already shipped in P4/P5/P6/P7) |
| P3-EXT056 | depth_modular_datamosh (DepthModularDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — DepthModularDatamoshEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT057 | depth_modulated_datamosh (DepthModulatedDatamoshEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — DepthModulatedDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT058 | depth_mosh_nexus (DepthMoshNexus) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — DepthMoshNexus already shipped in P4/P5/P6/P7)* |
| P3-EXT059 | depth_parallel_universe_datamosh (DepthParallelUniverseDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | (duplicate — DepthParallelUniverseDatamoshEffect already shipped in P4/P5/P6/P7) |
| P3-EXT060 | depth_effects (DepthParticle3DEffect) | P0 | 🟦 IN PROGRESS (roo_1) | *(duplicate — DepthParticle3DEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT061 | depth_effects (DepthPointCloud3DEffect) | P0 | 🟦 IN PROGRESS (roo_1) | *(duplicate — DepthPointCloud3DEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT062 | depth_effects (DepthPointCloudEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — DepthPointCloudEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT063 | depth_raver_datamosh (DepthRaverDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | (duplicate — DepthRaverDatamoshEffect already shipped in P4/P5/P6/P7) |
| P3-EXT064 | depth_simulator (DepthSimulatorEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | (duplicate — DepthSimulatorEffect already shipped in P4/P5/P6/P7) |
| P3-EXT065 | depth_slitscan_datamosh (DepthSlitScanDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | (duplicate — DepthSlitScanDatamoshEffect already shipped in P4/P5/P6/P7) |
| P3-EXT066 | depth_effects (DepthEffectsPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/depth_effects.py` — 7-effect depth chain (blur, color, distortion, glow, fog, sharpen), 8 tests ✅ 2026-02-23 |
| P3-EXT067 | depth_void_datamosh (DepthVoidDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | (duplicate — DepthVoidDatamoshEffect already shipped in P4/P5/P6/P7) |
| P3-EXT068 | dimension_splice_datamosh (DimensionSpliceDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | (duplicate — DimensionSpliceDatamoshEffect already shipped in P4/P5/P6/P7) |
| P3-EXT069 | displacement_map (DisplacementMapEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | (duplicate — DisplacementMapEffect already shipped in P4/P5/P6/P7) |
| P3-EXT070 | dithering (DitheringEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — DitheringEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT071 | dolly_zoom_datamosh (DollyZoomDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 (spec exists in _02_fleshed_out) | *(duplicate — DollyZoomDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT072 | vtempi (DutyCycleMode) | P0 | 🟦 IN PROGRESS (roo_1) | vjlive |
| P3-EXT073 | particles_3d (EmitterType) | P0 | 🟦 IN PROGRESS (roo_1) | vjlive |
| P3-EXT074 | erbe_verb (ErbeVerb) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | vjlive |
| P3-EXT075 | example_glitch (ExampleGlitchEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | vjlive |
| P3-EXT076 | vcv_video_generators (FMCoordinatesGen) | P0 | 🟩 COMPLETING PASS 2 (spec exists in _02_fleshed_out) | *(duplicate — FMCoordinatesGen already shipped in P4/P5/P6/P7)* |
| P3-EXT077 | face_melt_datamosh (FaceMeltDatamoshEffect) | P0 | 🟦 IN PROGRESS (roo_1) | *(duplicate — FaceMeltDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT078 | shadertoy_particles (FireParticles) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | vjlive |
| P3-EXT079 | fluid_sim (FluidSimEffect) | P0 | 🟦 IN PROGRESS (roo_1) | *(duplicate — FluidSimEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT080 | particles_3d (ForceType) | P0 | 🟦 IN PROGRESS (roo_1) | vjlive |
| P3-EXT081 | fractal_generator (FractalGenerator) | P0 | 🟦 IN PROGRESS (roo_1) | *(duplicate — FractalGenerator already shipped in P4/P5/P6/P7)* |
| P3-EXT082 | fracture_rave_datamosh (FractureRaveDatamoshEffect) | P0 | 🟦 IN PROGRESS (roo_1) | *(duplicate — FractureRaveDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT083 | datamosh (FrameHoldEffect) | P0 | 🟦 IN PROGRESS (roo_1) | *(duplicate — FrameHoldEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT084 | vcv_video_effects (GaussianBlurEffect) | P0 | 🟦 IN PROGRESS (roo_1) | *(duplicate — GaussianBlurEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT085 | generators (GradientEffect) | P0 | 🟦 IN PROGRESS (roo_1) | *(duplicate — GradientEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT086 | vcv_video_generators (GranularVideoGen) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — GranularVideoGen already shipped in P4/P5/P6/P7)* |
| P3-EXT087 | vcv_video_effects (HDRToneMapEffect) | P0 | 🟦 IN PROGRESS (roo3) | *(duplicate — HDRToneMapEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT088 | vcv_video_generators (HarmonicPatternsGen) | P0 | 🟩 COMPLETING PASS 2 (spec exists in _02_fleshed_out) | *(duplicate — HarmonicPatternsGen already shipped in P4/P5/P6/P7)* |
| P3-EXT089 | v_sws (HorizontalWaveEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — HorizontalWaveEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT090 | vtempi (HumanResolution) | P0 | 🟩 COMPLETING PASS 2 (spec exists in _02_fleshed_out) | vjlive |
| P3-EXT091 | neural_quantum_hyper_tunnel (HyperTunnelNet) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | vjlive |
| P3-EXT092 | hyperspace_quantum_tunnel (HyperspaceQuantumTunnel) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | vjlive |
| P3-EXT093 | blend (InfiniteFeedbackEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — InfiniteFeedbackEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT094 | color (InvertEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — InvertEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT095 | vtempi (LEDColor) | P0 | 🟩 COMPLETING PASS 2 | vjlive |
| P3-EXT096 | lut_grading (LUTGradingEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — LUTGradingEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT097 | datamosh_3d (LayerSeparationEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — LayerSeparationEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT098 | liquid_lsd_datamosh (LiquidLSDDatamoshEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — LiquidLSDDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT099 | luma_chroma_mask (LumaChromaMaskEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — LumaChromaMaskEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT100 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — MLBaseAsyncEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT101 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | 🟦 IN PROGRESS (roo) | *(duplicate — MLDepthEstimationEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT102 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | 🟦 IN PROGRESS (roo) | *(duplicate — MLSegmentationBlurGLEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT103 | ml_gpu_effects (MLStyleGLEffect) | P0 | 🟦 IN PROGRESS (desktop-roo) | *(duplicate — MLStyleGLEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT104 | vcv_video_generators (MacroShapeGen) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — MacroShapeGen already shipped in P4/P5/P6/P7)* |
| P3-EXT105 | generators (MandalaEffect) | P0 | 🟦 IN PROGRESS (desktop-roo) | *(duplicate — MandalaEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT106 | geometry (MandalascopeEffect) | P0 | 🟦 IN PROGRESS (desktop-roo) | *(duplicate — MandalascopeEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT107 | geometry (MirrorEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — MirrorEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT108 | blend (MixerEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — MixerEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT109 | vtempi (ModBehavior) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT110 | morphology (MorphologyEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — MorphologyEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT111 | mosh_pit_datamosh (MoshPitDatamoshEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — MoshPitDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT112 | vcv_video_effects (MultibandColorEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — MultibandColorEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT113 | shadertoy_particles (NebulaParticles) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT114 | neural_rave_nexus (NeuralRaveNexus) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — NeuralRaveNexus already shipped in P4/P5/P6/P7)* |
| P3-EXT115 | neural_splice_datamosh (NeuralSpliceDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — NeuralSpliceDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT116 | tunnel_vision_2 (NeuralTunnelNet) | P0 | 🟦 IN PROGRESS (desktop) | `docs/specs/P3-EXT116_NeuralTunnelNet.md` — spec approved |
| P3-EXT117 | optical_flow (OpticalFlowEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — OpticalFlowEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT118 | depth_effects (OpticalFlowEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | *(duplicate — OpticalFlowEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT119 | oscilloscope (OscilloscopeEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — OscilloscopeEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT120 | visualizer (OscilloscopeEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — OscilloscopeEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT121 | particles_3d (Particle3DSystem) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — Particle3DSystem already shipped in P4/P5/P6/P7)* |
| P3-EXT122 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — ParticleDatamoshTrailsEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT123 | particles_3d (ParticleState) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT124 | distortion (PatternDistortionEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — PatternDistortionEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT125 | generators (PerlinEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — PerlinEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT126 | datamosh (PixelBloomEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — PixelBloomEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT127 | datamosh (PixelSortEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — PixelSortEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT128 | geometry (PixelateEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — PixelateEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT129 | plasma_melt_datamosh (PlasmaMeltDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — PlasmaMeltDatamoshEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT130 | color (PosterizeEffect) | P0 | 🟩 COMPLETING PASS 2 | *(duplicate — PosterizeEffect already shipped in P4/P5/P6/P7)* ✅ Spec exists in _02_fleshed_out |
| P3-EXT131 | prism_realm_datamosh (PrismRealmDatamoshEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — PrismRealmDatamoshEffect already shipped in P4/P5/P6/P7)* |
| P3-EXT132 | vtempi (ProgramPage) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT133 | quantum_consciousness_datamosh (QuantumConsciousnessDatamosh) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT134 | tunnel_vision_3 (QuantumConsciousnessSingularityEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT135 | quantum_depth_nexus (QuantumDepthNexus) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT136 | quantum_entanglement_point_cloud (QuantumEntanglementPointCloud) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT137 | quantum_consciousness_explorer (QuantumState) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT138 | quantum_consciousness_explorer (QuantumState) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT139 | r16_deep_mosh_studio (R16DeepMoshStudio) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT140 | r16_depth_wave (R16DepthWave) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT141 | r16_interstellar_mosh (R16InterstellarMosh) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT142 | r16_simulated_depth (R16SimulatedDepth) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT143 | r16_vortex (R16VortexEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT144 | color (RGBShiftEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT145 | vibrant_retro_styles (RadiantMeshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT146 | rainmaker_rhythmic_echo (RainmakerRhythmicEcho) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT147 | reaction_diffusion (ReactionDiffusionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT148 | reality_distortion_field (RealityDistortionField) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT149 | particles_3d (RenderMode) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT150 | geometry (RepeatEffect) | P0 | 🟦 IN PROGRESS (desktop) | *(duplicate — RepeatEffect already shipped in P4/P5/P6/P7)* |
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
| P3-EXT224 | tunnel_vision_3 (ConsciousnessNet) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT225 | consciousness_neural_network (ConsciousnessNeuralNetwork) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT226 | consciousness_neural_network_effect (ConsciousnessNeuralNetwork) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT227 | silver_visions (CoordinateFolderEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT228 | cosmic_tunnel_datamosh (CosmicTunnelDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT229 | cotton_candy_datamosh (CottonCandyDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT230 | cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT231 | datamosh_3d (Datamosh3DEffect) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT232 | depth_acid_fractal (DepthAcidFractalDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
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
| P3-VD08 | Depth R16 Wave (DepthR16WavePlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/depth_r16_wave.py` — DepthR16WavePlugin, 8/8 tests ✅ 2026-02-22 |
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
| P3-EXT362 | vmake_noise (VDXGPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT363 | vmake_noise (VDynaMixPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT364 | vmake_noise (VErbeVerbPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT365 | vmi_complex (VFramesMIPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT366 | vmake_noise (VFxDfPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT367 | vvoxglitch (VGhosts) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT368 | vvoxglitch (VGlitchSequencer) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT369 | vvoxglitch (VGrooveBox) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT370 | vattractors (VHalvorsenPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT371 | vattractors (VHalvorsenPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT372 | vvoxglitch (VHazumi) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT373 | vattractors (VLorenzPlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
| P3-EXT374 | vattractors (VLorenzPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT375 | vlxd (VLxDPlugin) | P0 | ⬜ PENDING SKELETON (Pass 1) | VJlive-2 |
| P3-EXT376 | vmake_noise (VMorphagenePlugin) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
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
| P3-EXT412 | base (VparticlesBase) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | VJlive-2 |
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
| P1-R1 | Agnostic Render Context | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/render/opengl_context.py` — OpenGLContext, 10/10 tests ✅ |
| P1-R2 | GPU pipeline + framebuffer management (RAII) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `chain.py`, `program.py`, `framebuffer.py` - tests pass, 82% coverage ✅ |
| P1-R3 | Shader compilation system (GLSL + Milkdrop) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/render/shader_compiler.py` — 7 tests @ 81% cov ✅ — 2026-02-22 |
| P1-R4 | Texture manager (pooled, leak-free) | [Agent name] | ⬜ PENDING SKELETON (Pass 1) | 80% coverage mapped across ModernGL dictionary buffers and fallback decoded stream paths. (2026-02-22) |
| P1-R5 | Core rendering engine (60fps loop) | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/render/engine.py` — RenderEngine, 8/8 tests ✅ 2026-02-22 |
| P1-R6 | WebGPU Core Renderer (WGSL) | P0 | ⬜ PENDING SKELETON (Pass 1) | WebGPU rendering backend for cross-platform / web compatibility |
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
| P1-S1 | Config manager (centralized app config, env vars, YAML) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | Legacy: `core/config_manager.py` — CameraConfigManager found in Qdrant |
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
| P2-T1 | Audio-to-Video DSP translation pass (convert audio DSP → video equivalents) | P0 | ⬜ PENDING SKELETON (Pass 1) | All audio DSP effects must become video effects with audio-reactive inputs |
| P2-T2 | Plugin packaging / distribution (how users install third-party plugins) | P1 | ⬜ PENDING SKELETON (Pass 1) | No legacy spec — needs design for .vjplugin format or pip |
| P1-MM1 | Mood Manifold Engine | P0 | ⬜ PENDING SKELETON (Pass 1) | Interprets hardware state as a manifold of complexity, heat, and chaos to produce evolving visual patterns |
| P1-HY1 | Hydra Video Synth Integration | P0 | ⬜ PENDING SKELETON (Pass 1) | Integration with Olivia Jack's Hydra |
| P1-LC1 | Live Coding Environment | P0 | ⬜ PENDING SKELETON (Pass 1) | Real-time modification of shaders and Python code |
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
| P3-VD72 | datamosh_3d (DepthDisplacementEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/depth_displacement.py` — DepthDisplacementPlugin, 5/5 tests ✅ 2026-02-23 |
| P3-VD73 | datamosh_3d (DepthEchoEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD74 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD75 | quantum_depth_nexus_effect (QuantumDepthNexus) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P4-BA01 | B1to8 | ⬜ RESET | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |  |
| P4-BA02 | BLFO | ⬜ RESET | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |  |
| P4-BA03 | BMatrix81 | ⬜ RESET | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |  |
| P4-BA04 | BPEQ6 | ⬜ RESET | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |  |
| P4-BA05 | BSwitch | ⬜ RESET | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |  |
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
| P5-MO03 | blend (ModulateEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/modulate.py` — 8/8 tests ✅ 2026-02-23 |
| P5-VE02 | analog_tv (AnalogTVEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/analog_tv.py` — 11/11 tests ✅ 2026-02-23 |
| P5-DM02 | bad_trip_datamosh (BadTripDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/bad_trip_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM03 | bass_cannon_datamosh (BassCannonDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/bass_cannon_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM04 | bass_therapy_datamosh (BassTherapyDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/bass_therapy_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM05 | blend (GlitchEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/glitch_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM06 | bullet_time_datamosh (BulletTimeDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/bullet_time_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM07 | cellular_automata_datamosh (CellularAutomataDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/cellular_automata_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM08 | cotton_candy_datamosh (CottonCandyDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/cotton_candy_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM09 | cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/cupcake_cascade_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM10 | datamosh (CompressionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/compression_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM11 | datamosh (DatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM12 | datamosh (PixelBloomEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/pixel_bloom_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM13 | datamosh (MeltEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/melt_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM14 | datamosh (PixelSortEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/pixel_sort_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM15 | datamosh (FrameHoldEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/frame_hold_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM16 | datamosh_3d (Datamosh3DEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/datamosh_3d.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM17 | datamosh_3d (LayerSeparationEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/layer_separation_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM18 | datamosh_3d (ShatterEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/shatter_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM19 | dimension_splice_datamosh (DimensionSpliceDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/dimension_splice_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM20 | dolly_zoom_datamosh (DollyZoomDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/dolly_zoom_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM21 | face_melt_datamosh (FaceMeltDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/face_melt_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM22 | fracture_rave_datamosh (FractureRaveDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/fracture_rave_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM23 | liquid_lsd_datamosh (LiquidLSDDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/liquid_lsd_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM24 | mosh_pit_datamosh (MoshPitDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/mosh_pit_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM25 | neural_splice_datamosh (NeuralSpliceDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/neural_splice_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM26 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/particle_datamosh_trails.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM27 | plasma_melt_datamosh (PlasmaMeltDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/plasma_melt_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM28 | prism_realm_datamosh (PrismRealmDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/prism_realm_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM29 | sacred_geometry_datamosh (SacredGeometryDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/sacred_geometry_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM30 | spirit_aura_datamosh (SpiritAuraDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/spirit_aura_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM31 | temporal_rift_datamosh (TemporalRiftDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/temporal_rift_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM32 | tunnel_vision_datamosh (TunnelVisionDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/tunnel_vision_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM33 | unicorn_farts_datamosh (UnicornFartsDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/unicorn_farts_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM34 | void_swirl_datamosh (VoidSwirlDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/void_swirl_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM35 | volumetric_datamosh (VolumetricDatamoshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/volumetric_datamosh.py` — 7/7 tests ✅ 2026-02-23 |
| P5-DM36 | volumetric_glitch (VolumetricGlitchEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/volumetric_glitch.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC06 | agent_avatar (TravelingAvatarEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/traveling_avatar.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC07 | agent_avatar (AgentAvatarEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/agent_avatar.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC08 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/ml_base_async.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC09 | ml_gpu_effects (MLStyleGLEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/ml_style_gl.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC10 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/ml_segmentation_blur.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC11 | neural_rave_nexus (NeuralRaveNexus) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/neural_rave_nexus.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC12 | quantum_consciousness_explorer (QuantumConsciousnessExplorer) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/quantum_consciousness_explorer.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC13 | trails (TrailsEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/trails_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-QC14 | tunnel_vision_3 (QuantumConsciousnessSingularityEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/quantum_singularity.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE06 | fractal_generator (FractalGenerator) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/fractal_generator.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE07 | generators (OscEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/osc_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE08 | generators (NoiseEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/noise_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE09 | generators (VoronoiEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/voronoi_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE10 | generators (GradientEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/gradient_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE11 | generators (MandalaEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/mandala_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE12 | generators (PlasmaEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/plasma_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE13 | generators (PerlinEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/perlin_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE14 | silver_visions (PathGeneratorEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/path_generator.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE15 | vcv_video_generators (HarmonicPatternsGen) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/harmonic_patterns.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE16 | vcv_video_generators (FMCoordinatesGen) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/fm_coordinates.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE17 | vcv_video_generators (MacroShapeGen) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/macro_shape.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE18 | vcv_video_generators (GranularVideoGen) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/granular_video.py` — 7/7 tests ✅ 2026-02-23 |
| P6-GE19 | vcv_video_generators (ResonantGeometryGen) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/resonant_geometry.py` — 7/7 tests ✅ 2026-02-23 |
| P6-P302 | particles_3d (AdvancedParticle3DSystem) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/advanced_particle_3d.py` — 7/7 tests ✅ 2026-02-23 |
| P6-P303 | particles_3d (Particle3DSystem) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/particle_3d.py` — 7/7 tests ✅ 2026-02-23 |
| P6-P304 | shadertoy_particles (ShadertoyParticles) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/shadertoy_particles.py` — 7/7 tests ✅ 2026-02-23 |
| P6-P305 | vibrant_retro_styles (RadiantMeshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/radiant_mesh.py` — 7/7 tests ✅ 2026-02-23 |
| P7-U1 | Desktop GUI + SentienceOverlay easter egg | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/desktop_gui.py` (VJLiveGUIApp + SentienceOverlay) — 20/20 tests ✅ 2026-02-23 |
| P7-U2 | Web-based remote control | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/web_remote.py` (HTTP REST API + WS broadcaster) — 17/17 tests ✅ 2026-02-23 |
| P7-U3 | Collaborative Studio UI | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/desktop_gui.py` (CollaborativeStudio, role-based) — 6/6 tests ✅ 2026-02-23 |
| P7-U4 | Quantum Collaborative Studio | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/desktop_gui.py` (QuantumCollaborativeStudio, superposition) — 6/6 tests ✅ 2026-02-23 |
| P7-U5 | TouchOSC export / mobile interface | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/cli.py` (OSCLayoutExporter + address map JSON) — 8/8 tests ✅ 2026-02-23 |
| P7-U6 | CLI automation | P0 | ⬜ PENDING SKELETON (Pass 1) | `src/vjlive3/ui/cli.py` (ParamStore, PresetSequencer, argparse CLI) — 22/22 tests ✅ 2026-02-23 |
| P7-U7 | React Frontend UI Infrastructure | P0 | ⬜ PENDING SKELETON (Pass 1) | React + Vite UI core |
| P7-U8 | Media Browser Component | P0 | ⬜ PENDING SKELETON (Pass 1) | React media browser context |
| P7-U9 | Administration Section | P0 | ⬜ PENDING SKELETON (Pass 1) | System admin and config panel |
| P7-VE01 | V Sws (VSwsEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/v_sws.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE02 | V Sws (HorizontalWaveEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/horizontal_wave.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE03 | V Sws (VerticalWaveEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/vertical_wave.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE04 | V Sws (RippleEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/ripple_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE05 | V Sws (SpiralWaveEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/spiral_wave.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE06 | ascii_effect (ASCIIEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/ascii_effect2.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE07 | bass_cannon_2 (BassCanon2) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/bass_cannon_2.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE08 | blend (FeedbackEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/feedback_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE09 | blend (BlendAddEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/blend_add.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE10 | blend (BlendMultEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/blend_mult.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE11 | blend (BlendDiffEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/blend_diff.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE12 | blend (ScanlinesEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/scanlines_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE13 | blend (VignetteEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/vignette_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE14 | blend (InfiniteFeedbackEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/infinite_feedback.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE15 | blend (BloomEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/bloom_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE16 | blend (BloomShadertoyEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/bloom_shadertoy.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE17 | blend (MixerEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/mixer_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE18 | blend_modes (_BlendMode) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/blend_modes_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE19 | chroma_key (ChromaKeyEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/chroma_key.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE20 | color (PosterizeEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/posterize_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE21 | color (ContrastEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/contrast_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE22 | color (SaturateEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/saturate_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE23 | color (HueEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/hue_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE24 | color (BrightnessEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/brightness_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE25 | color (InvertEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/invert_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE26 | color (ThreshEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/thresh_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE27 | color (RGBShiftEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/rgb_shift.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE28 | color (ColorCorrectEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/color_correct.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE29 | color_grade (ColorGradeEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/color_grade2.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE30 | colorama (ColoramaEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/colorama.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE31 | displacement_map (DisplacementMapEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/displacement_map.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE32 | distortion (ChromaticDistortionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/chromatic_distortion.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE33 | distortion (PatternDistortionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/pattern_distortion.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE34 | dithering (DitheringEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/dithering_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE35 | fluid_sim (FluidSimEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/fluid_sim.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE36 | geometry (MandalascopeEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/mandalascope.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE37 | geometry (RotateEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/rotate_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE38 | geometry (ScaleEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/scale_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE39 | geometry (PixelateEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/pixelate_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE40 | geometry (RepeatEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/repeat_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE41 | geometry (ScrollEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/scroll_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE42 | geometry (MirrorEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/mirror_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE43 | geometry (ProjectionMappingEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/projection_mapping2.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE44 | hyperion (VimanaHyperion) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/vimana_hyperion.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE45 | hyperspace_tunnel (HyperspaceTunnelEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/hyperspace_tunnel.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE46 | living_fractal_consciousness (LivingFractalConsciousness) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/living_fractal.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE47 | luma_chroma_mask (LumaChromaMaskEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/luma_chroma_mask.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE48 | lut_grading (LUTGradingEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/lut_grading.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE49 | milkdrop (MilkdropEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/milkdrop.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE50 | morphology (MorphologyEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/morphology_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE51 | oscilloscope (OscilloscopeEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/oscilloscope_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE52 | plugin_template (CustomEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/custom_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE53 | pop_art_effects (BenDayDotsEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/ben_day_dots.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE54 | pop_art_effects (WarholQuadEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/warhol_quad.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE55 | r16_deep_mosh_studio (R16DeepMoshStudio) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/r16_deep_mosh.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE56 | r16_interstellar_mosh (R16InterstellarMosh) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/r16_interstellar.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE57 | reaction_diffusion (ReactionDiffusionEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/reaction_diffusion.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE58 | resize_effect (ResizeEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/resize_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE59 | rutt_etra_scanline (RuttEtraScanlineEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/rutt_etra.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE60 | silver_visions (VideoOutEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/video_out.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE61 | silver_visions (ImageInEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/image_in.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE62 | silver_visions (CoordinateFolderEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/coordinate_folder.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE63 | silver_visions (AffineTransformEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/affine_transform.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE64 | silver_visions (PreciseDelayEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/precise_delay.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE65 | slit_scan (SlitScanEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/slit_scan.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE66 | sync_eater (SyncEaterEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/sync_eater.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE67 | time_remap (TimeRemapEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/time_remap.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE68 | vcv_video_effects (GaussianBlurEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/gaussian_blur.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE69 | vcv_video_effects (MultibandColorEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/multiband_color.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE70 | vcv_video_effects (HDRToneMapEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/hdr_tonemap.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE71 | vcv_video_effects (SolarizeEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/solarize_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE72 | vcv_video_effects (ResonantBlurEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/resonant_blur.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE73 | vcv_video_effects (AdaptiveContrastEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/adaptive_contrast.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE74 | vcv_video_effects (SpatialEchoEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/spatial_echo.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE75 | vcv_video_effects (DelayZoomEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/delay_zoom.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE76 | vibrant_retro_styles (RioAestheticEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/rio_aesthetic.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE77 | vimana (Vimana) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/vimana.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE78 | vimana_hyperion_ultimate (VimanaHyperionUltimate) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/vimana_hyperion_ultimate.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE79 | vimana_synth (VimanaEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/vimana_synth.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE80 | visualizer (VisualizerEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/visualizer_effect.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE81 | visualizer (SpectrumAnalyzerEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/spectrum_analyzer.py` — 7/7 tests ✅ 2026-02-23 |
| P7-VE82 | visualizer (VUMeterEffect) | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out | `src/vjlive3/plugins/vu_meter.py` — 7/7 tests ✅ 2026-02-23 |

## 📊 Summary
- **Pass 1/2 Completed:** ~110 specs
- **Pass 1/2 Queued:** ~900 specs
- **Pass 3 Queued:** ~110 specs awaiting Frontier Analysis
| P1-QDRANT002 | Quantum Neural Evolution | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `VJlive-2/plugins/quantum_neural_evolution.py` |
| P1-QDRANT003 | Chromatic Aberration | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/chromatic_aberration.py` |
| P1-QDRANT019 | Masking | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/masking.py` |
| P1-QDRANT020 | Mimeophon Control Bridge | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/mimeophon_control_bridge.py` |
| P1-QDRANT021 | Mimeophon Video | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/mimeophon_video.py` |
| P1-QDRANT022 | Planetary Lfos | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/planetary_lfos.py` |
| P1-QDRANT026 | Satanonaut Plugin | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/satanonaut_plugin.py` |
| P1-QDRANT027 | Satanonaut Video | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/satanonaut_video.py` |
| P1-QDRANT029 | Simple Mimeophon Video | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/simple_mimeophon_video.py` |
| P1-QDRANT030 | Texture 3D Integration | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/texture_3d_integration.py` |
| P1-QDRANT031 | Texture 3D Top | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/texture_3d_top.py` |
| P1-QDRANT032 | Texture 3D Websocket | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/texture_3d_websocket.py` |
| P1-QDRANT033 | Time Machine Top | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/time_machine_top.py` |
| P1-QDRANT034 | V Jumbler | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `core/core_plugins/v_jumbler.py` |
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
| P1-QDRANT067 | Vmoddemix Core | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/vmoddemix/vmoddemix_core.py` |
| P1-QDRANT071 |   Init  .Ultimate | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/core/effect_vimana_hyperion/__init__.ultimate.py` |
| P1-QDRANT073 | Make Noise Function | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/core/modulation_function/make_noise_function.py` |
| P1-QDRANT075 | Playground | P1 | ⬜ PENDING SKELETON (Pass 1) | Legacy: `plugins/core/quantum_audio/playground.py` |

## Recovered Core Features (Orphan Specs)
| ID | Name (Class) | Priority | Status | Location / Notes |
|---|---|---|---|---|
| P3-VD46 | Depth_Erosion_Datamosh | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT426 | VJumblerPlugin | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD03 | depth_portal_composite | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD30 | Depth_Color_Grade | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P9-MISS005 | v-languor | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD02 | depth_parallel_universe | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT431 | VAnalogMemoryPlugin | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P9-MISS003 | v-thomas | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD01 | depth_loop_injection | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT428 | VMimeophonPlugin | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P-UNK-1 | Fluid_Simulation | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD28 | depth_blur | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD04 | depth_reverb | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT434 | VFunctionPlugin | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD31 | Depth_Contour_Datamosh | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD23 | depth_vector_field_datamosh | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P9-MISS002 | v-halvorsen | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD19 | depth_liquid_refraction | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD22 | depth_temporal_strat | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P1-A5 | audio_reactivity | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD27 | Depth_Aware_Compression | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT430 | VPolimathsPlugin | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD17 | depth_mosaic | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD76 | Frame_Hold_Effect | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD20 | depth_slitscan_datamosh | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT433 | VContourPlugin | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT429 | VModdemixPlugin | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-EXT432 | VBrainsPlugin | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD18 | depth_video_projection | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P9-MISS004 | v-sakarya | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD49 | Depth_Fracture_Datamosh | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
| P3-VD21 | depth_temporal_echo | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |
