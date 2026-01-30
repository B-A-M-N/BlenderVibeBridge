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

# BlenderVibeBridge Hardened Startup Script

# --- CONFIGURATION (User Editable) ---
# Set to 'true' to enable specific security layers
USE_BWRAP=${USE_BWRAP:-false}
USE_FIREJAIL=${USE_FIREJAIL:-false}
USE_APPARMOR=${USE_APPARMOR:-false}

PROJECT_DIR="/home/bamn/BlenderVibeBridge"
LOG_FILE="$PROJECT_DIR/server.log"

echo "--- Starting BlenderVibeBridge MCP Server ---"
echo "Security Layers: BWRAP=$USE_BWRAP, FIREJAIL=$USE_FIREJAIL, APPARMOR=$USE_APPARMOR"

# 1. AppArmor Check (Requires manual loading once: sudo apparmor_parser -r security/blender_vibe_bridge.apparmor)
if [ "$USE_APPARMOR" = "true" ]; then
    if ! command -v apparmor_status &> /dev/null; then
        echo "[!] Warning: AppArmor not found. Skipping."
    else
        echo "[+] AppArmor enforcement expected via kernel (Ensure profile is loaded)."
    fi
fi

# 2. Command Construction
CMD="python3 server.py"

# Layer: Firejail
if [ "$USE_FIREJAIL" = "true" ]; then
    if command -v firejail &> /dev/null; then
        CMD="firejail --profile=$PROJECT_DIR/security/blender_vibe_bridge.local $CMD"
        echo "[+] Firejail wrapper added."
    else
        echo "[!] Error: Firejail not found. Proceeding without it."
    fi
fi

# Layer: Bubblewrap (Namespaced Sandbox)
if [ "$USE_BWRAP" = "true" ]; then
    if command -v bwrap &> /dev/null; then
        # Create a read-only sandbox with specific write access to logs and metadata
        CMD="bwrap \
            --ro-bind / / \
            --dev /dev \
            --proc /proc \
            --tmpfs /tmp \
            --bind $PROJECT_DIR $PROJECT_DIR \
            --chdir $PROJECT_DIR/mcp-server \
            $CMD"
        echo "[+] Bubblewrap sandbox active."
    else
        echo "[!] Error: Bubblewrap not found. Proceeding without it."
    fi
fi

# 3. Execution
cd "$PROJECT_DIR/mcp-server"

if [ "$USE_BWRAP" = "true" ]; then
    # Bwrap handles the chdir and pathing internally
    $CMD > "$LOG_FILE" 2>&1 &
else
    $CMD > "$LOG_FILE" 2>&1 &
fi

MCP_PID=$!

echo "Server started with PID: $MCP_PID"
echo "Logs: $LOG_FILE"
echo "Bridge is ready. Ensure Blender Vibe Bridge is active on port 22000."

# Wait for PID
wait $MCP_PID