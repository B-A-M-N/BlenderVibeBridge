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

# BlenderVibeBridge: Management Tools (v1.5.0)
import json
import os
import time
from ..ipc.blender_interface import blender_request
from ..core.kernel import monitor, AuditLogger

def register_management_tools(mcp):
    @mcp.tool()
    def begin_transaction() -> str:
        """THE ARCHIVIST: Starts a multi-command transaction."""
        return str(blender_request("POST", "/command", data={"type": "system_op", "action": "begin_transaction", "intent": "GENERAL"}, is_mutation=True))

    @mcp.tool()
    def commit_transaction(rationale_check: str, intent: str = "GENERAL") -> str:
        """THE ARCHIVIST: Finalizes the current transaction. Requires JSON rationale_check with 'scene_hash'."""
        try:
            check = json.loads(rationale_check)
            if "scene_hash" not in check:
                return "Error: Hard Gate Violation. 'scene_hash' missing."
            
            current_state = blender_request("GET", "/blender/scene_state")
            if current_state.get("scene_hash") != check["scene_hash"]:
                return f"Error: Hash Mismatch. Expected {current_state.get('scene_hash')}, got {check['scene_hash']}."
            
            high_impact = intent.upper() in ["RIG", "CLEANUP", "SCENE_SETUP", "OPTIMIZE"]
            if high_impact and (len(check.get("technical_rationale", "")) < 20):
                return f"Error: Insufficient Rationale for intent '{intent}'."
                
            return str(blender_request("POST", "/command", data={"type": "system_op", "action": "commit_transaction", "intent": intent.upper(), "rationale": check}, is_mutation=True))
        except Exception as e:
            return f"Error processing Hard Gate: {str(e)}"

    @mcp.tool()
    def rollback_transaction() -> str:
        """THE ARCHIVIST: Aborts the current transaction."""
        return str(blender_request("POST", "/command", data={"type": "system_op", "action": "rollback_transaction", "intent": "GENERAL"}, is_mutation=True))

    @mcp.tool()
    def get_vibe_audit_log(lines: int = 20) -> str:
        """Retrieves the last N entries from the audit log. Clears RECOVERY_MODE."""
        monitor.exit_recovery()
        path = "/home/bamn/BlenderVibeBridge/logs/vibe_audit.jsonl"
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    all_lines = f.readlines()
                    return "".join(all_lines[-lines:])
            except Exception as e:
                return f"Error reading audit log: {str(e)}"
        return "Audit log missing."

    @mcp.tool()
    def get_blender_errors() -> str:
        """Retrieves the last 20 lines from bridge.log. Clears RECOVERY_MODE."""
        monitor.exit_recovery()
        path = "/home/bamn/BlenderVibeBridge/bridge.log"
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    lines = f.readlines()
                    return "".join(lines[-20:])
            except Exception as e:
                return f"Error reading log: {str(e)}"
        return "Log file missing."

    @mcp.tool()
    def check_heartbeat() -> str:
        """Reads the Blender heartbeat to verify if the main thread is alive."""
        path = "/home/bamn/BlenderVibeBridge/metadata/vibe_health.json"
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    age = time.time() - data.get("timestamp", 0)
                    data["heartbeat_age_seconds"] = round(age, 2)
                    return json.dumps(data, indent=2)
            except Exception as e:
                return f"Error reading heartbeat: {str(e)}"
        return "Heartbeat file missing."
