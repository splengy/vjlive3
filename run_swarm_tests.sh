#!/bin/bash
set -e
HOST_SPEC_DIR="/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/docs/specs"

echo "=== TEST METHOD 1: Qwen Raw Dump Promotion (Pass 1) ==="
# Setup dummy raw dump on Host
mkdir -p "$HOST_SPEC_DIR/_00_raw_dump" "$HOST_SPEC_DIR/_01_skeletons"
touch "$HOST_SPEC_DIR/_00_raw_dump/dummy_spec.md"

# Simulate the sync cycle section 1 (Pulling raw dumps and moving to skeletons)
echo "Running dummy promote..."
find "${HOST_SPEC_DIR}/_00_raw_dump/" -maxdepth 1 -name "*_spec.md" -exec mv {} "${HOST_SPEC_DIR}/_01_skeletons/" \;

if [ -f "${HOST_SPEC_DIR}/_01_skeletons/dummy_spec.md" ] && [ ! -f "${HOST_SPEC_DIR}/_00_raw_dump/dummy_spec.md" ]; then
    echo "✅ TEST 1 PASSED: File moved successfully."
else
    echo "❌ TEST 1 FAILED: File missing or duplicated."
fi
rm -f "${HOST_SPEC_DIR}/_01_skeletons/dummy_spec.md"

