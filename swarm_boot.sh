#!/bin/bash
# ============================================================================
# VJLive3 Swarm Boot — Scalable N-Node Edition
# ============================================================================
# Run ONCE from the Host at the start of each session.
# Syncs the raw NPU dumps and the pure filesystem queue.
#
# Usage:  bash swarm_boot.sh
# ============================================================================

set -euo pipefail

HOST_WORKSPACE="/home/happy/Desktop/claude projects/VJLive3_The_Reckoning"
NPU_WORKSPACE="/home/happy/vjlive_worker"
SSH_PASS="655369"
SSH_OPTS="-o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SSH_CMD="sshpass -p ${SSH_PASS} ssh ${SSH_OPTS}"

# Define all external worker nodes here.
# The Host desktop is implicitly included as the orchestrator.
WORKER_NODES=(
    "192.168.1.60:Julie"
    "192.168.1.50:Maxx"
    # "192.168.1.X:Node3"  <-- Add future scaling nodes here
)

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✅ $1${NC}"; }
fail() { echo -e "  ${RED}❌ $1${NC}"; }
warn() { echo -e "  ${YELLOW}⚠️  $1${NC}"; }
step() { echo -e "\n${YELLOW}━━━ $1 ━━━${NC}"; }

# ── Step 1: Network ───────────────────────────────────────────────────────
step "Step 1: Network"
for node in "${WORKER_NODES[@]}"; do
    ip="${node%%:*}"; name="${node##*:}"
    if ping -W 1 -c 1 "$ip" &>/dev/null; then ok "$name ($ip) alive"
    else fail "$name ($ip) UNREACHABLE"; exit 1; fi
done

# ── Step 1.5: Enforce NPU Folder Structure ───────────────────────────────
step "Step 1.5: Verify Worker Structure"
for node in "${WORKER_NODES[@]}"; do
    ip="${node%%:*}"
    $SSH_CMD "happy@$ip" "mkdir -p ${NPU_WORKSPACE}/docs/specs/_00_raw_dump"
done
ok "All NPUs are strictly utilizing ${NPU_WORKSPACE}"

# ── Step 2: One-Shot Sync ────────────────────────────────────────────────
step "Step 2: Sync (Init Queue)"
bash "${HOST_WORKSPACE}/swarm_sync.sh"
ok "Initial filesystem sync complete"

# ── Step 3: Verify local .roo/mcp.json ────────────────────────────────────
step "Step 3: MCP Config (No Switchboards!)"
for node in "${WORKER_NODES[@]}"; do
    ip="${node%%:*}"; name="${node##*:}"
    count=$($SSH_CMD "happy@$ip" "python3 -c \"import json; print(len(json.load(open('${NPU_WORKSPACE}/.roo/mcp.json')).get('mcpServers',{})))\"" 2>/dev/null || echo "ERROR")
    if [ "$count" = "5" ]; then ok "$name: .roo/mcp.json has $count servers (Switchboard dead)"
    else fail "$name: .roo/mcp.json missing or broken (got: ${count:-empty})"; fi
done

# ── Step 4: Restart code-server ───────────────────────────────────────────
step "Step 4: Code-Server"
for node in "${WORKER_NODES[@]}"; do
    ip="${node%%:*}"; name="${node##*:}"
    $SSH_CMD "happy@$ip" "systemctl --user restart code-server 2>/dev/null || true"
    ok "$name code-server restarted to wipe ghost locks"
done
sleep 3

# ── Step 5: Start sync daemon ────────────────────────────────────────────
step "Step 5: Sync Daemon (Zero-DB Queue Router)"
pkill -f "swarm_sync.sh" || true
nohup bash "${HOST_WORKSPACE}/swarm_sync.sh" --loop \
    > /dev/null 2>&1 &
sleep 1
pgrep -f "swarm_sync.sh" &>/dev/null && ok "Daemon Started (pid $(pgrep -f swarm_sync.sh | head -1))" || fail "Failed to start daemon"

# ── Step 6: RDP ──────────────────────────────────────────────────────────
step "Step 6: RDP Windows"
for node in "${WORKER_NODES[@]}"; do
    ip="${node%%:*}"; name="${node##*:}"
    if command -v remmina &>/dev/null; then
        nohup remmina -c "rdp://happy:655369@${ip}" >/dev/null 2>&1 &
        ok "${name} Launched"
    else 
        warn "remmina not installed locally"; break
    fi
done

# ── Done ─────────────────────────────────────────────────────────────────
step "ZERO-DATABASE SWARM READY"
echo ""

for node in "${WORKER_NODES[@]}"; do
    name="${node##*:}"
    echo "  Paste into ${name}'s Roo Code:"
    echo "  ─────────────────────────────"
    echo "  You are ${name,,}-roo. Your environment is fully configured."
    echo "  Read the rules at:"
    echo "  ${NPU_WORKSPACE}/.clinerules"
    echo "  Then read your protocol at:"
    echo "  ${NPU_WORKSPACE}/agent-heartbeat/ROO_INSTRUCTIONS.md"
    echo "  Your first action: check docs/specs/_01_skeletons/ for work. Use \`mv\` to claim it."
    echo ""
done

echo "  Paste into Desktop's Local Roo Code Instances (OpenRouter):"
echo "  Run as many instances as needed. They all share this identical Host workspace."
echo "  ─────────────────────────────"
echo "  You are desktop-roo. Your environment is fully configured."
echo "  Read the rules at:"
echo "  ${HOST_WORKSPACE}/.clinerules"
echo "  Then read your protocol at:"
echo "  ${HOST_WORKSPACE}/agent-heartbeat/ROO_INSTRUCTIONS.md"
echo "  Your first action: check docs/specs/_01_skeletons/ for work. Use \`mv\` to claim it."
echo ""
