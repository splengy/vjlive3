import os
import shutil
import glob

skeletons_dir = "docs/specs/_01_skeletons"
fleshed_dir = "docs/specs/_02_fleshed_out"
desktop_dir = "docs/specs/_02_active_desktop"

# Ensure destination directories exist
os.makedirs(fleshed_dir, exist_ok=True)
os.makedirs(desktop_dir, exist_ok=True)

# 1. Restore the 21 active_desktop files
desktop_files = {
    "P0-G1_Environment_Reboot.md", "P0-INF2_Legacy_Feature_Parity_Audit.md", "P0-M2_MCP_vjlive3switchboard.md", 
    "P0-Q3_scripts_check_file_lock.py.md", "P0-Q1_scripts_check_stubs.py.md", "P0-G7_ROOT_PRIME_DIRECTIVE.md", 
    "P0-A1_Phase0_App_Window.md", "P0-G3_WORKSPACE_COMMS_AGENT_SYNC.md", "P3-EXT157_RunStopMode.md", 
    "P0-G5_KNOWLEDGE_DREAMER_LOG.md", "P0-G4_WORKSPACE_COMMS_LOCKS.md", "P0-G1_WORKSPACE_PRIME_DIRECTIVE.md", 
    "P0-V1_Phase_Gate_Check.md", "P0-G2_WORKSPACE_SAFETY_RAILS.md", "P0-G5_WORKSPACE_COMMS_DECISIONS.md", 
    "P4-COR010_AIParameterPrediction.md", "P0-Q4_pre_commit_config_yaml.md", "P0-M1_MCP_vjlive3brain_knowledge_base.md", 
    "P0-G6_KNOWLEDGE_TOOL_TIPS.md", "P0-Q2_scripts_check_file_size.py.md", "P0-INF4_Core_Logic_Parity_Audit.md"
}

# 2. Files that genuinely belong in skeletons
original_skeletons = {
    "P0-Q1_check_stubs.md", "P0-W3_BESPOKE_PLUGIN_MIGRATION.md", "P0-W4_PHASE_GATE_CHECK.md", 
    "P1-QDRANT001_Create_Panel_Background.md", "P1-QDRANT002_Quantum_Neural_Evolution.md", 
    "P1-QDRANT003_Chromatic_Aberration.md", "P1-QDRANT004_Example_Glitch_Effect.md", 
    "P1-QDRANT005_Run_Depth_Demo.md", "P1-QDRANT006_Run_Ml_Demo.md", "P1-QDRANT007_Run_Ml_Demo.md", 
    "P1-QDRANT008_Run_Ml_Demo.md", "P1-QDRANT009_Run_Ml_Demo.md", "P1-QDRANT010_Run_Ml_Demo.md", 
    "P1-QDRANT011_Run_Ml_Demo.md", "P1-QDRANT012_Run_Ml_Demo.md", "P1-QDRANT013_Run_Ml_Demo.md", 
    "P1-QDRANT014_Run_Ml_Demo.md", "P1-QDRANT015_Run_Ml_Demo.md", "P1-QDRANT016_Run_Ml_Demo.md", 
    "P1-QDRANT017_Run_Ml_Demo.md", "P1-QDRANT018_Run_Ml_Demo.md", "P1-QDRANT019_Run_Ml_Demo.md", 
    "P1-QDRANT020_Run_Ml_Demo.md", "P1-QDRANT021_Run_Ml_Demo.md", "P1-QDRANT022_Run_Ml_Demo.md", 
    "P1-QDRANT023_Run_Ml_Demo.md", "P3-EXT166_ShiftDirection.md", "P3-EXT167_SimulatedColorDepth.md", 
    "P3-EXT176_TestBassCanon3.md", "P3-EXT187_VRainmakerRhythmicEcho.md", "P3-EXT210_AstraNode.md", 
    "P3-EXT214_BackgroundSubtractionEffect.md", "P3-EXT216_BassCannonDatamoshEffect.md", 
    "P3-EXT217_BassCanon2.md", "P3-EXT218_BassTherapyDatamoshEffect.md", "P3-EXT219_BenDayDotsEffect.md", 
    "P3-EXT221_BulletTimeDatamoshEffect.md", "P3-EXT222_CellularAutomataDatamoshEffect.md", 
    "P3-EXT223_ColoramaEffect.md", "P3-EXT233_DepthCameraSplitterEffect.md", "P3-INFRA-CIRCBUF_CircularBuffer.md"
}

print(f"Executing revert operation in {skeletons_dir}...")

moved_to_desktop = 0
moved_to_fleshed = 0
skipped = 0
errors = 0

current_files = glob.glob(os.path.join(skeletons_dir, "*.md"))
for f in current_files:
    basename = os.path.basename(f)
    if basename in original_skeletons:
        skipped += 1
        continue # Leave it in skeletons
    elif basename in desktop_files:
        try:
            shutil.move(f, os.path.join(desktop_dir, basename))
            moved_to_desktop += 1
        except Exception as e:
            print(f"Error moving {basename} to desktop: {e}")
            errors += 1
    else:
        # It was erroneously quarantined from fleshed_out
        try:
            shutil.move(f, os.path.join(fleshed_dir, basename))
            moved_to_fleshed += 1
        except Exception as e:
            print(f"Error moving {basename} to fleshed_out: {e}")
            errors += 1

print(f"\nRevert complete:")
print(f" - Moved back to _02_active_desktop: {moved_to_desktop}")
print(f" - Moved back to _02_fleshed_out: {moved_to_fleshed}")
print(f" - Left intact in _01_skeletons: {skipped}")
print(f" - Errors encountered: {errors}")
