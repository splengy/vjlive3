#!/bin/bash
# ============================================================================
# VJLive3 Swarm Sync — Zero-Database Edition
# ============================================================================
# Syncs the raw NPU dumps and the pure filesystem queue between nodes
# ============================================================================

set -e

JULIE_IP="192.168.1.50"
MAXX_IP="192.168.1.60"
WORKSPACE="/home/happy/Desktop/claude projects/VJLive3_The_Reckoning"
SSH_OPTS="-o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no"

sync_cycle() {
    # ── 1. Pull Raw NPU Dumps from Edge Devices (Maxx & Julie) ───────────
    # The Edge RKLLMs output to /home/happy/outback/
    # We pull them into _00_raw_dump/ (We only pull *.md files)
    
    # Pull from Maxx
    rsync -aq --update \
        -e "ssh $SSH_OPTS" \
        "happy@${MAXX_IP}:/home/happy/outback/*.md" \
        "${WORKSPACE}/docs/specs/_00_raw_dump/" 2>/dev/null || true

    # Pull from Julie
    rsync -aq --update \
        -e "ssh $SSH_OPTS" \
        "happy@${JULIE_IP}:/home/happy/outback/*.md" \
        "${WORKSPACE}/docs/specs/_00_raw_dump/" 2>/dev/null || true

    # Move anything in _00_raw_dump/ into _01_skeletons/ on the Host to activate it
    # We only move files that end in _spec.md
    find "${WORKSPACE}/docs/specs/_00_raw_dump/" -maxdepth 1 -name "*_spec.md" -exec mv {} "${WORKSPACE}/docs/specs/_01_skeletons/" \; 2>/dev/null || true

    # ── 2. Pull Active Agent Work FROM OPis to Host ──────────────────────
    rsync -aq --update \
        --exclude='.venv' --exclude='__pycache__' \
        -e "ssh $SSH_OPTS" \
        "happy@${JULIE_IP}:${WORKSPACE}/docs/specs/" \
        "${WORKSPACE}/docs/specs/" 2>/dev/null || true

    rsync -aq --update \
        --exclude='.venv' --exclude='__pycache__' \
        -e "ssh $SSH_OPTS" \
        "happy@${MAXX_IP}:${WORKSPACE}/docs/specs/" \
        "${WORKSPACE}/docs/specs/" 2>/dev/null || true

    # ── 3. Push Global State TO OPis ─────────────────────────────────────
    # This pushes the current state of _01_skeletons, _02, _03, _04 down to the workers
    rsync -aq --update --delete \
        --exclude='.venv' --exclude='__pycache__' \
        -e "ssh $SSH_OPTS" \
        "${WORKSPACE}/docs/specs/" \
        "happy@${JULIE_IP}:${WORKSPACE}/docs/specs/" 2>/dev/null || true

    rsync -aq --update --delete \
        --exclude='.venv' --exclude='__pycache__' \
        -e "ssh $SSH_OPTS" \
        "${WORKSPACE}/docs/specs/" \
        "happy@${MAXX_IP}:${WORKSPACE}/docs/specs/" 2>/dev/null || true
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
