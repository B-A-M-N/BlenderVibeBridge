#!/bin/bash
# BlenderVibeBridge: Dual-License & Maintenance Agreement (v1.2)
# Copyright (C) 2026 B-A-M-N (The "Author")
#
# This software is distributed under a Dual-Licensing Model:
# 1. THE OPEN-SOURCE PATH: GNU AGPLv3 (see LICENSE for details)
# 2. THE COMMERCIAL PATH: "WORK-OR-PAY" MODEL
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.

# BlenderVibeBridge: Hardened Startup (v1.5.0)

# --- SECURITY CONFIG ---
USE_BWRAP=${USE_BWRAP:-true}
PROJECT_DIR="/home/bamn/BlenderVibeBridge"
LOG_FILE="$PROJECT_DIR/server.log"

echo "--- Starting Hardened BlenderVibeBridge ---"

# Bubblewrap Sandbox Logic
if [ "$USE_BWRAP" = "true" ]; then
    CMD="bwrap \
        --ro-bind /usr /usr \
        --ro-bind /lib /lib \
        --ro-bind /lib64 /lib64 \
        --ro-bind /bin /bin \
        --ro-bind /sbin /sbin \
        --ro-bind /etc/alternatives /etc/alternatives \
        --dev /dev \
        --proc /proc \
        --tmpfs /tmp \
        --bind $PROJECT_DIR $PROJECT_DIR \
        --unshare-all \
        --share-net \
        --die-with-parent \
        --chdir $PROJECT_DIR/mcp-server \
        python3 server.py"
    echo "[+] Bubblewrap Sandbox: ENABLED"
else
    cd "$PROJECT_DIR/mcp-server"
    CMD="python3 server.py"
    echo "[!] Bubblewrap Sandbox: DISABLED"
fi

$CMD > "$LOG_FILE" 2>&1 &
MCP_PID=$!

echo "MCP Server PID: $MCP_PID"
echo "Logs: tail -f server.log"
wait $MCP_PID