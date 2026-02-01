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

# BlenderVibeBridge: Infrastructure Tools (v1.5.0)
import os
import json
from ..ipc.blender_interface import blender_request
from security_gate import SecurityGate

from ..core.kernel import system_audit

def register_infrastructure_tools(mcp):
    @mcp.tool()
    def hot_reload_blender_bridge() -> str:
        """Triggers a self-reload within Blender."""
        return str(blender_request("POST", "/command", data={"type": "system_op", "action": "reload", "intent": "GENERAL"}, is_mutation=True))

    @mcp.tool()
    def run_adversarial_preflight() -> str:
        """Performs a deep system audit to detect and resolve instabilities."""
        return json.dumps(system_audit(), indent=2)

    @mcp.tool()
    def secure_write_file(path: str, content: str) -> str:
        """Writes a file ONLY after passing an AST Security Audit."""
        if ".." in path or path.startswith("/"): return "Path traversal blocked."
        if SecurityGate.check_python(content): return "Security Violation."
        
        if "/" not in path and any(path.endswith(ext) for ext in [".json", ".txt", ".log"]):
            path = os.path.join("avatar_scripts", path)

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f: f.write(content)
            return f"Wrote {path}."
        except Exception as e: return f"Failed: {str(e)}"

    @mcp.tool()
    def create_safety_checkpoint(name: str) -> str:
        """Saves a timestamped copy of the blend file."""
        return str(blender_request("POST", "/command", data={"type": "system_op", "action": "checkpoint", "name": name, "intent": "GENERAL"}, is_mutation=True))
