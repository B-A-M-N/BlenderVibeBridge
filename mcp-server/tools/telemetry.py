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

# BlenderVibeBridge: Telemetry Tools (v1.5.0)
import json
from ..ipc.blender_interface import blender_request

def register_telemetry_tools(mcp):
    @mcp.tool()
    def validate_scene_integrity() -> str:
        """Checks for architectural invariants like scale sanity."""
        return str(blender_request("GET", "/validate"))

    @mcp.tool()
    def get_scene_telemetry() -> str:
        """Returns structured scene data: poly counts, materials, etc."""
        return str(blender_request("GET", "/status"))

    @mcp.tool()
    def inspect_object_forensics(name: str) -> str:
        """Recursive node tree dump for deep material analysis."""
        return str(blender_request("GET", f"/forensic?name={name}"))

    @mcp.tool()
    def find_object_by_traits(vertex_count: int = None, material_name: str = None) -> str:
        """Finds objects based on vertex count or material name."""
        return str(blender_request("POST", "/query", data={"type": "audit_op", "action": "find_by_traits", "v_count": vertex_count, "mat_name": material_name}, is_mutation=False))

    @mcp.tool()
    def get_state_hash() -> str:
        """Returns a deterministic SHA256 hash of the current scene state."""
        res = blender_request("GET", "/blender/scene_state")
        if isinstance(res, dict) and "scene_hash" in res:
            return res["scene_hash"]
        return "UNKNOWN"
