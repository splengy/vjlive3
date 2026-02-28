#!/bin/bash
# ============================================================================
# VJLive3 Swarm Sync — Zero-Database Edition
# ============================================================================
# Syncs the raw NPU dumps and the pure filesystem queue between nodes
# ============================================================================

set -e

JULIE_IP="192.168.1.60"
MAXX_IP="192.168.1.50"
HOST_WORKSPACE="/home/happy/Desktop/claude projects/VJLive3_The_Reckoning"
NPU_WORKSPACE="/home/happy/vjlive_worker"
SSH_PASS="655369"
SSH_OPTS="-o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
RSYNC_RSH="sshpass -p ${SSH_PASS} ssh ${SSH_OPTS}"

sync_cycle() {
    # ── 1. Pull Raw NPU Dumps from Edge Devices (Maxx & Julie) ───────────
    # The Edge RKLLMs output to their structured local _00_raw_dump directory
    # Pull from Maxx
    rsync -aq --update \
        -e "$RSYNC_RSH" \
        "happy@${MAXX_IP}:${NPU_WORKSPACE}/docs/specs/_00_raw_dump/*.md" \
        "${HOST_WORKSPACE}/docs/specs/_00_raw_dump/" 2>/dev/null || true

    # Pull from Julie
    rsync -aq --update \
        -e "$RSYNC_RSH" \
        "happy@${JULIE_IP}:${NPU_WORKSPACE}/docs/specs/_00_raw_dump/*.md" \
        "${HOST_WORKSPACE}/docs/specs/_00_raw_dump/" 2>/dev/null || true

    # Move anything in _00_raw_dump/ into _01_skeletons/ on the Host to activate it
    find "${HOST_WORKSPACE}/docs/specs/_00_raw_dump/" -maxdepth 1 -name "*_spec.md" -exec mv {} "${HOST_WORKSPACE}/docs/specs/_01_skeletons/" \; 2>/dev/null || true

    # ── 2. Pull Active Agent Work FROM OPis to Host ──────────────────────
    rsync -aq --update \
        --exclude='.venv' --exclude='__pycache__' \
        -e "$RSYNC_RSH" \
        "happy@${JULIE_IP}:${NPU_WORKSPACE}/docs/specs/" \
        "${HOST_WORKSPACE}/docs/specs/" 2>/dev/null || true

    rsync -aq --update \
        --exclude='.venv' --exclude='__pycache__' \
        -e "$RSYNC_RSH" \
        "happy@${MAXX_IP}:${NPU_WORKSPACE}/docs/specs/" \
        "${HOST_WORKSPACE}/docs/specs/" 2>/dev/null || true

    # ── 3. Push Global State TO OPis ─────────────────────────────────────
    # This pushes the current state of _01_skeletons, _02, _03, _04 down to the workers
    rsync -aq --update --delete \
        --exclude='.venv' --exclude='__pycache__' \
        -e "$RSYNC_RSH" \
        "${HOST_WORKSPACE}/docs/specs/" \
        "happy@${JULIE_IP}:${NPU_WORKSPACE}/docs/specs/" 2>/dev/null || true

    rsync -aq --update --delete \
        --exclude='.venv' --exclude='__pycache__' \
        -e "$RSYNC_RSH" \
        "${HOST_WORKSPACE}/docs/specs/" \
        "happy@${MAXX_IP}:${NPU_WORKSPACE}/docs/specs/" 2>/dev/null || true
}

# Daemon mode or one-shot
if [ "${1:-}" == "--loop" ]; then
    echo "Starting Swarm Sync Daemon (Zero-Database Filesystem Queue)..."
    while true; do
        sync_cycle
        sleep 10  # Very fast sync for tight queue feedback
    done
else
    echo "Running one-shot sync..."
    sync_cycle
    echo "Sync complete."
fi
