#!/bin/bash
# ============================================================================
# VJLive3 Swarm Sync — Scalable N-Node Edition
# ============================================================================
# Syncs the raw NPU dumps and the pure filesystem queue between the Host
# and any number of scaling worker nodes (NPUs or other machines).
#
# NOTE: The Host itself (Desktop) is natively part of this queue since it
# operates directly out of HOST_WORKSPACE. You can run as many local Roo
# instances pointing at HOST_WORKSPACE as your API limits allow.
# ============================================================================

set -e

HOST_WORKSPACE="/home/happy/Desktop/claude projects/VJLive3_The_Reckoning"
NPU_WORKSPACE="/home/happy/vjlive_worker"
SSH_PASS="655369"
SSH_OPTS="-o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
RSYNC_RSH="sshpass -p ${SSH_PASS} ssh ${SSH_OPTS}"

# Define all external worker nodes here. 
# Format: "IP_ADDRESS:NAME"
# The Host desktop is implicitly included because it owns HOST_WORKSPACE.
WORKER_NODES=(
    "192.168.1.60:Julie"
    "192.168.1.50:Maxx"
    # "192.168.1.X:Node3"  <-- Add future scaling nodes here
)

sync_cycle() {
    # ── 1. Pull Raw NPU Dumps from Edge Devices ───────────
    for node in "${WORKER_NODES[@]}"; do
        ip="${node%%:*}"
        rsync -aq --update --remove-source-files \
            -e "$RSYNC_RSH" \
            "happy@${ip}:${NPU_WORKSPACE}/docs/specs/_00_raw_dump/*.md" \
            "${HOST_WORKSPACE}/docs/specs/_00_raw_dump/" 2>/dev/null || true
    done

    # Move anything successfully pulled into _01_skeletons/ on the Host to activate it
    find "${HOST_WORKSPACE}/docs/specs/_00_raw_dump/" -maxdepth 1 -name "*_spec.md" -exec mv {} "${HOST_WORKSPACE}/docs/specs/_01_skeletons/" \; 2>/dev/null || true

    # ── 2. Pull Active Agent Work FROM External Nodes to Host ─────────────
    # This brings any files moved to _02_fleshed_out back to the mothership
    for node in "${WORKER_NODES[@]}"; do
        ip="${node%%:*}"
        rsync -aq --update \
            --exclude='.venv' --exclude='__pycache__' \
            -e "$RSYNC_RSH" \
            "happy@${ip}:${NPU_WORKSPACE}/docs/specs/" \
            "${HOST_WORKSPACE}/docs/specs/" 2>/dev/null || true
    done

    # ── 2.5 Resolve Queue Movements (Authoritative Host state) ────────────
    # 2.5a. If a file is in _02_fleshed_out, cull it from ALL active and skeleton queues
    find "${HOST_WORKSPACE}/docs/specs/_02_fleshed_out/" -type f -name "*.md" 2>/dev/null | while read -r f; do
        base="$(basename "$f")"
        find "${HOST_WORKSPACE}/docs/specs/" -type d -name "*_active_*" -exec rm -f {}/"$base" \; 2>/dev/null || true
        rm -f "${HOST_WORKSPACE}/docs/specs/_01_skeletons/$base" 2>/dev/null || true
    done

    # 2.5b. If a file is in ANY active folder, cull it from skeletons
    find "${HOST_WORKSPACE}/docs/specs/" -type d -name "*_active_*" 2>/dev/null | while read -r active_dir; do
        find "$active_dir" -type f -name "*.md" 2>/dev/null | while read -r f; do
            base="$(basename "$f")"
            rm -f "${HOST_WORKSPACE}/docs/specs/_01_skeletons/$base" 2>/dev/null || true
        done
    done

    # ── 3. Push Global State TO All External Nodes ─────────────────────────
    # This pushes the authoritative state of _01_skeletons, _02, _03 down to everyone
    for node in "${WORKER_NODES[@]}"; do
        ip="${node%%:*}"
        rsync -aq --update --delete \
            --exclude='.venv' --exclude='__pycache__' \
            -e "$RSYNC_RSH" \
            "${HOST_WORKSPACE}/docs/specs/" \
            "happy@${ip}:${NPU_WORKSPACE}/docs/specs/" 2>/dev/null || true
    done
}

# Daemon mode or one-shot
if [ "${1:-}" == "--loop" ]; then
    echo "Starting Swarm Sync Daemon (Zero-Database Filesystem Queue)..."
    echo "Tracking ${#WORKER_NODES[@]} external nodes + 1 Local Host"
    while true; do
        sync_cycle
        sleep 10  # Very fast sync for tight queue feedback
    done
else
    echo "Running one-shot sync across ${#WORKER_NODES[@]} nodes..."
    sync_cycle
    echo "Sync complete."
fi
