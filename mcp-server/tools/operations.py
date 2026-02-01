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

# BlenderVibeBridge: Operation Tools (v1.5.0)
import json
from ..ipc.blender_interface import blender_request

def register_operation_tools(mcp):
    @mcp.tool()
    def validate_humanoid_rig(armature_name: str) -> str:
        """Validates if a rig follows standard Humanoid bone structure."""
        return str(blender_request("POST", "/command", data={"type": "unity_op", "action": "validate_humanoid", "target": armature_name, "intent": "RIG"}, is_mutation=True))

    @mcp.tool()
    def optimize_avatar_mesh(obj_name: str, ratio: float = 0.5) -> str:
        """Reduces polycount of a mesh by a specific ratio."""
        return str(blender_request("POST", "/command", data={"type": "unity_op", "action": "optimize_avatar", "target": obj_name, "ratio": ratio, "intent": "OPTIMIZE"}, is_mutation=True))

    @mcp.tool()
    def generate_viseme_key(mesh_name: str, viseme: str) -> str:
        """Creates a viseme shape key slot for lip-sync."""
        return str(blender_request("POST", "/command", data={"type": "viseme_op", "name": mesh_name, "viseme": viseme, "intent": "ANIMATE"}, is_mutation=True))

    @mcp.tool()
    def transform_object(name: str, operation: str, x: float, y: float, z: float) -> str:
        """Moves, rotates, or scales an object."""
        return str(blender_request("POST", "/command", data={"type": "transform", "name": name, "op": operation, "value": str((x,y,z)), "intent": "SCENE_SETUP"}, is_mutation=True))

    @mcp.tool()
    def manage_modifier(name: str, action: str, modifier_name: str, modifier_type: str = None, properties: str = None) -> str:
        """Manages object modifiers with safety rails."""
        payload = {"type": "modifier_op", "name": name, "action": action, "mod_name": modifier_name, "mod_type": modifier_type, "intent": "OPTIMIZE"}
        if properties:
            try: payload.update({"action": "set", "props": json.loads(properties)})
            except: return "Error: Invalid JSON."
        return str(blender_request("POST", "/command", data=payload, is_mutation=True))

    @mcp.tool()
    def manage_material(name: str, obj_name: str = None) -> str:
        """Creates a new material and optionally assigns it."""
        return str(blender_request("POST", "/command", data={"type": "material_op", "name": name, "obj_name": obj_name, "intent": "SCENE_SETUP"}, is_mutation=True))

    @mcp.tool()
    def trigger_bake(resolution: int = 1024) -> str:
        """Triggers a texture bake with a 2048px safety cap."""
        return str(blender_request("POST", "/command", data={"type": "bake_op", "resolution": resolution, "intent": "OPTIMIZE"}, is_mutation=True))
