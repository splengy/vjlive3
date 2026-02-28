#!/bin/bash
# ============================================================================
# VJLive3 Swarm Boot — Zero-Database Edition
# ============================================================================
# Run ONCE from the Host at the start of each session.
# Syncs the raw NPU dumps and the pure filesystem queue.
#
# Usage:  bash swarm_boot.sh
# ============================================================================

set -euo pipefail

JULIE_IP="192.168.1.50"
MAXX_IP="192.168.1.60"
WORKSPACE="/home/happy/Desktop/claude projects/VJLive3_The_Reckoning"
SSH_PASS="655369"
SSH_OPTS="-o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SSH_CMD="sshpass -p ${SSH_PASS} ssh ${SSH_OPTS}"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✅ $1${NC}"; }
fail() { echo -e "  ${RED}❌ $1${NC}"; }
warn() { echo -e "  ${YELLOW}⚠️  $1${NC}"; }
step() { echo -e "\n${YELLOW}━━━ $1 ━━━${NC}"; }

# ── Step 1: Network ───────────────────────────────────────────────────────
step "Step 1: Network"
for node in "$JULIE_IP:Julie" "$MAXX_IP:Maxx"; do
    ip="${node%%:*}"; name="${node##*:}"
    if ping -W 1 -c 1 "$ip" &>/dev/null; then ok "$name ($ip) alive"
    else fail "$name ($ip) UNREACHABLE"; exit 1; fi
done

# ── Step 2: One-Shot Sync ────────────────────────────────────────────────
step "Step 2: Sync (Init Queue)"
bash "${WORKSPACE}/swarm_sync.sh"
ok "Initial filesystem sync complete"

# ── Step 3: Verify local .roo/mcp.json ────────────────────────────────────
step "Step 3: MCP Config (No Switchboards!)"
for node in "$JULIE_IP:Julie" "$MAXX_IP:Maxx"; do
    ip="${node%%:*}"; name="${node##*:}"
    count=$($SSH_CMD "happy@$ip" "python3 -c \"import json; print(len(json.load(open('${WORKSPACE}/.roo/mcp.json')).get('mcpServers',{})))\"" 2>/dev/null)
    if [ "$count" = "5" ]; then ok "$name: .roo/mcp.json has $count servers (Switchboard dead)"
    else fail "$name: .roo/mcp.json missing or broken (got: ${count:-empty})"; fi
done

# ── Step 4: Restart code-server ───────────────────────────────────────────
step "Step 4: Code-Server"
for node in "$JULIE_IP:Julie" "$MAXX_IP:Maxx"; do
    ip="${node%%:*}"; name="${node##*:}"
    $SSH_CMD "happy@$ip" "systemctl --user restart code-server 2>/dev/null || true"
    ok "$name code-server restarted to wipe ghost locks"
done
sleep 3

# ── Step 5: Start sync daemon ────────────────────────────────────────────
step "Step 5: Sync Daemon (Zero-DB Queue Router)"
pkill -f "swarm_sync.sh" || true
nohup bash "${WORKSPACE}/swarm_sync.sh" --loop \
    > /dev/null 2>&1 &
sleep 1
pgrep -f "swarm_sync.sh" &>/dev/null && ok "Daemon Started (pid $(pgrep -f swarm_sync.sh | head -1))" || fail "Failed to start daemon"

# ── Step 6: RDP ──────────────────────────────────────────────────────────
step "Step 6: RDP Windows"
if command -v remmina &>/dev/null; then
    nohup remmina -c "rdp://happy:655369@${JULIE_IP}" >/dev/null 2>&1 &
    nohup remmina -c "rdp://happy:655369@${MAXX_IP}" >/dev/null 2>&1 &
    ok "Launched"
else warn "remmina not installed locally"; fi

# ── Done ─────────────────────────────────────────────────────────────────
step "ZERO-DATABASE SWARM READY"
cat << 'EOF'

  Paste into Julie's Roo Code:
  ─────────────────────────────
  You are julie-roo. Your environment is fully configured.
  Read the rules at:
  /home/happy/Desktop/claude projects/VJLive3_The_Reckoning/.clinerules
  Then read your protocol at:
  /home/happy/Desktop/claude projects/VJLive3_The_Reckoning/agent-heartbeat/ROO_INSTRUCTIONS.md
  Your first action: check docs/specs/_01_skeletons/ for work. Use `mv` to claim it.

  Paste into Maxx's Roo Code:
  ─────────────────────────────
  You are maxx-roo. Your environment is fully configured.
  Read the rules at:
  /home/happy/Desktop/claude projects/VJLive3_The_Reckoning/.clinerules
  Then read your protocol at:
  /home/happy/Desktop/claude projects/VJLive3_The_Reckoning/agent-heartbeat/ROO_INSTRUCTIONS.md
  Your first action: check docs/specs/_01_skeletons/ for work. Use `mv` to claim it.

  Paste into Desktop's Roo Code (Host):
  ─────────────────────────────
  You are desktop-roo. Your environment is fully configured.
  Read the rules at:
  /home/happy/Desktop/claude projects/VJLive3_The_Reckoning/.clinerules
  Then read your protocol at:
  /home/happy/Desktop/claude projects/VJLive3_The_Reckoning/agent-heartbeat/ROO_INSTRUCTIONS.md
  Your first action: check docs/specs/_01_skeletons/ for work. Use `mv` to claim it.

EOF
