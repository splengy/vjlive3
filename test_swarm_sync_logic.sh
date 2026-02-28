#!/bin/bash
set -e

echo "==========================================="
echo " SWARM SYNC RACE CONDITION TEST (3 METHODS)"
echo "==========================================="

mkdir -p /tmp/swarm_test/host/docs/specs/_01_skeletons
mkdir -p /tmp/swarm_test/host/docs/specs/_02_active_julie
mkdir -p /tmp/swarm_test/host/docs/specs/_02_fleshed_out

mkdir -p /tmp/swarm_test/npu/docs/specs/_01_skeletons
mkdir -p /tmp/swarm_test/npu/docs/specs/_02_active_julie
mkdir -p /tmp/swarm_test/npu/docs/specs/_02_fleshed_out

# The simulated sync loop function with NEW QUEUE RESOLUTION LOGIC
simulate_sync_cycle() {
    # 1. Pull from NPUs
    rsync -aq --update /tmp/swarm_test/npu/docs/specs/ /tmp/swarm_test/host/docs/specs/
    
    # 2.5 QUEUE RESOLUTION (The Fix)
    # 2.5a. If a file is in fleshed out, cull it from ALL active and skeleton queues
    find /tmp/swarm_test/host/docs/specs/_02_fleshed_out/ -type f -name "*.md" 2>/dev/null | while read -r f; do
        base="$(basename "$f")"
        find /tmp/swarm_test/host/docs/specs/ -type d -name "*_active_*" -exec rm -f {}/"$base" \; 2>/dev/null || true
        rm -f "/tmp/swarm_test/host/docs/specs/_01_skeletons/$base" 2>/dev/null || true
    done

    # 2.5b. If a file is in ANY active folder, cull it from skeletons
    find /tmp/swarm_test/host/docs/specs/ -type d -name "*_active_*" 2>/dev/null | while read -r active_dir; do
        find "$active_dir" -type f -name "*.md" 2>/dev/null | while read -r f; do
            base="$(basename "$f")"
            rm -f "/tmp/swarm_test/host/docs/specs/_01_skeletons/$base" 2>/dev/null || true
        done
    done
    
    # 3. Push Global State TO NPUs with --delete
    rsync -aq --update --delete /tmp/swarm_test/host/docs/specs/ /tmp/swarm_test/npu/docs/specs/
}

run_tests() {
    local loop_id=$1
    echo ""
    echo "==========================================="
    echo " RUNNING TEST SUITE: ITERATION $loop_id"
    echo "==========================================="

    # Reset states for clean loop
    rm -f /tmp/swarm_test/host/docs/specs/*/* 2>/dev/null || true
    rm -f /tmp/swarm_test/npu/docs/specs/*/* 2>/dev/null || true

echo ""
echo "--- METHOD 1: Worker Claims Task ---"
# State: Skeletons exist globally
touch /tmp/swarm_test/host/docs/specs/_01_skeletons/task1.md
simulate_sync_cycle

# Action: NPU agent claims task1.md by moving it
mv /tmp/swarm_test/npu/docs/specs/_01_skeletons/task1.md /tmp/swarm_test/npu/docs/specs/_02_active_julie/task1.md

# Sync happens
simulate_sync_cycle

if [ -f "/tmp/swarm_test/host/docs/specs/_01_skeletons/task1.md" ]; then
    echo "❌ FATAL FAIL M1: file task1.md resurrected in _01_skeletons on Host! (Duplication Bug)"
else
    echo "✅ PASS M1: no duplication."
fi

# Assert it isn't also duplicated back onto the NPU
if [ -f "/tmp/swarm_test/npu/docs/specs/_01_skeletons/task1.md" ] && [ -f "/tmp/swarm_test/npu/docs/specs/_02_active_julie/task1.md" ]; then
    echo "❌ FATAL FAIL M1: file duplicated back onto NPU. Two versions exist simultaneously!"
fi

echo ""
echo "--- METHOD 2: Worker Finishes Task ---"
# Action: NPU finishes fleshing out and moves it to _02_fleshed_out
mv /tmp/swarm_test/npu/docs/specs/_02_active_julie/task1.md /tmp/swarm_test/npu/docs/specs/_02_fleshed_out/task1.md

# Sync happens
simulate_sync_cycle

if [ -f "/tmp/swarm_test/host/docs/specs/_02_active_julie/task1.md" ]; then
    echo "❌ FATAL FAIL M2: Ghost clone of task1.md still stuck in _02_active_julie on Host!"
fi

echo ""
echo "--- METHOD 3: Qwen Raw Dump Loop ---"
mkdir -p /tmp/swarm_test/host/docs/specs/_00_raw_dump
mkdir -p /tmp/swarm_test/npu/docs/specs/_00_raw_dump

touch /tmp/swarm_test/npu/docs/specs/_00_raw_dump/qwen_task_spec.md

# Sync code from step 1 WITH --remove-source-files
rsync -aq --update --remove-source-files /tmp/swarm_test/npu/docs/specs/_00_raw_dump/ /tmp/swarm_test/host/docs/specs/_00_raw_dump/
find /tmp/swarm_test/host/docs/specs/_00_raw_dump/ -name "*_spec.md" -exec mv {} /tmp/swarm_test/host/docs/specs/_01_skeletons/ \; 2>/dev/null || true

# Run it a SECOND time
rsync -aq --update --remove-source-files /tmp/swarm_test/npu/docs/specs/_00_raw_dump/ /tmp/swarm_test/host/docs/specs/_00_raw_dump/
find /tmp/swarm_test/host/docs/specs/_00_raw_dump/ -name "*_spec.md" -exec mv {} /tmp/swarm_test/host/docs/specs/_01_skeletons/ \; 2>/dev/null || true

if [ -f "/tmp/swarm_test/npu/docs/specs/_00_raw_dump/qwen_task_spec.md" ]; then
    echo "❌ FATAL FAIL M3: Raw dump was never deleted from Qwen NPU. Same files will be slurped infinitely."
else
    echo "✅ PASS M3: Raw dump consumed locally."
fi

}

run_tests 1
run_tests 2
run_tests 3

echo ""
echo "All 3 loop tests specific to rsync architecture complete."
