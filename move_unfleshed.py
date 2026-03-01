import os
import shutil
import glob

# Source and destination directories
src_dir = "docs/specs/_02_active_desktop"
dest_dir = "docs/specs/_01_skeletons"

# Ensure destination directory exists (though it should)
os.makedirs(dest_dir, exist_ok=True)

# List of identified unfleshed files from previous step
unfleshed_files = [
    "P0-G1_Environment_Reboot.md",
    "P0-INF2_Legacy_Feature_Parity_Audit.md",
    "P0-M2_MCP_vjlive3switchboard.md",
    "P0-Q3_scripts_check_file_lock.py.md",
    "P0-Q1_scripts_check_stubs.py.md",
    "P0-G7_ROOT_PRIME_DIRECTIVE.md",
    "P0-A1_Phase0_App_Window.md",
    "P0-G3_WORKSPACE_COMMS_AGENT_SYNC.md",
    "P3-EXT157_RunStopMode.md",
    "P0-G5_KNOWLEDGE_DREAMER_LOG.md",
    "P0-G4_WORKSPACE_COMMS_LOCKS.md",
    "P0-G1_WORKSPACE_PRIME_DIRECTIVE.md",
    "P0-V1_Phase_Gate_Check.md",
    "P0-G2_WORKSPACE_SAFETY_RAILS.md",
    "P0-G5_WORKSPACE_COMMS_DECISIONS.md",
    "P4-COR010_AIParameterPrediction.md",
    "P0-Q4_pre_commit_config_yaml.md",
    "P0-M1_MCP_vjlive3brain_knowledge_base.md",
    "P0-G6_KNOWLEDGE_TOOL_TIPS.md",
    "P0-Q2_scripts_check_file_size.py.md",
    "P0-INF4_Core_Logic_Parity_Audit.md"
]

print(f"Moving {len(unfleshed_files)} unfleshed specs from {src_dir} to {dest_dir}...")

moved_count = 0
for filename in unfleshed_files:
    src_path = os.path.join(src_dir, filename)
    dest_path = os.path.join(dest_dir, filename)
    
    if os.path.exists(src_path):
        try:
            shutil.move(src_path, dest_path)
            print(f"  [MOVED] {filename}")
            moved_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to move {filename}: {e}")
    else:
        print(f"  [NOT FOUND] {filename} not found in {src_dir}")

print(f"\nSuccessfully moved {moved_count} out of {len(unfleshed_files)} files.")
