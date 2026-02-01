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

# BlenderVibeBridge: Opcode Handlers (v1.5.0)
import bpy
import bmesh
from ..logging.logger import vibe_log

def resolve_by_uuid(collection, target_uuid):
    """Authoritative lookup by vibe_uuid."""
    for block in collection:
        if block.get("vibe_uuid") == target_uuid:
            return block
    return None

def handle_transform(data):
    """Opcode 0x03: Precise Loc/Rot/Scale."""
    obj = resolve_by_uuid(bpy.data.objects, data.get("uuid"))
    if not obj:
        # Fallback to name if UUID resolution fails
        obj = bpy.data.objects.get(data.get("name"))
    
    if not obj:
        raise Exception(f"IDENTITY_LOST: Could not resolve object {data.get('name')}")

    import ast
    val = ast.literal_eval(data.get("value"))
    op = data.get("op")
    
    if op == "translate":
        obj.location = val
    elif op == "rotate":
        obj.rotation_euler = val
    elif op == "scale":
        obj.scale = val
    
    vibe_log(f"TRANSFORM SUCCESS: {obj.name} -> {op}:{val}")
    return {"name": obj.name, "status": "OK"}

def handle_system_op(data, gate):
    """Opcode 0x0F: Transaction & Kernel Management."""
    action = data.get("action")
    if action == "begin_transaction":
        gate.begin()
    elif action == "commit_transaction":
        gate.commit(intent=data.get("intent"))
    elif action == "rollback_transaction":
        gate.rollback()
    return {"status": "ACK", "action": action}

def handle_modifier(data):
    """Opcode 0x04: Add/Remove/Set Modifiers."""
    obj = resolve_by_uuid(bpy.data.objects, data.get("uuid")) or bpy.data.objects.get(data.get("name"))
    if not obj: raise Exception("TARGET_LOST")
    
    action = data.get("action")
    mod_name = data.get("mod_name")
    
    if action == "add":
        obj.modifiers.new(name=mod_name, type=data.get("mod_type"))
    elif action == "set":
        mod = obj.modifiers.get(mod_name)
        props = data.get("props", {})
        for k, v in props.items():
            setattr(mod, k, v)
    elif action == "remove":
        mod = obj.modifiers.get(mod_name)
        obj.modifiers.remove(mod)
    return {"status": "OK", "modifier": mod_name}

def handle_material(data):
    """Opcode 0x09: Material creation and assignment."""
    mat_name = data.get("name")
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
    
    obj_name = data.get("obj_name")
    if obj_name:
        obj = bpy.data.objects.get(obj_name)
        if obj and obj.type == 'MESH':
            if not obj.data.materials:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat
    return {"status": "OK", "material": mat.name}

def handle_mesh_op(data):
    """Opcode 0x11: BMesh-based surgical operations."""
    # Placeholder for complex bmesh logic
    return {"status": "ACK", "action": data.get("action")}

def handle_lighting(data):
    """Opcode 0x06: Light source configuration."""
    name = data.get("name")
    light_data = bpy.data.lights.get(name) or bpy.data.lights.new(name=name, type=data.get("type_light", "POINT"))
    obj = bpy.data.objects.get(name) or bpy.data.objects.new(name=name, object_data=light_data)
    if obj.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(obj)
    
    obj.data.energy = data.get("energy", 10.0)
    import ast
    obj.data.color = ast.literal_eval(data.get("color", "(1, 1, 1)"))
    return {"status": "OK", "light": obj.name}

def handle_constraint(data):
    """Opcode 0x07: Object rigging and constraints."""
    obj = resolve_by_uuid(bpy.data.objects, data.get("uuid")) or bpy.data.objects.get(data.get("name"))
    if not obj: raise Exception("TARGET_LOST")
    
    con = obj.constraints.new(type=data.get("c_type"))
    con.name = data.get("c_name", con.name)
    target = bpy.data.objects.get(data.get("target"))
    if target: con.target = target
    return {"status": "OK", "constraint": con.name}

def handle_physics(data):
    """Opcode 0x08: Physics application."""
    obj = bpy.data.objects.get(data.get("name"))
    if not obj: raise Exception("TARGET_LOST")
    bpy.context.view_layer.objects.active = obj
    phys_type = data.get("phys_type")
    if phys_type == "RIGID_BODY":
        bpy.ops.rigidbody.object_add()
    elif phys_type == "CLOTH":
        bpy.ops.object.modifier_add(type='CLOTH')
    return {"status": "OK", "physics": phys_type}

def handle_io(data):
    """Opcode 0x0B: Import/Export."""
    action = data.get("action")
    path = data.get("filepath")
    if action == "import_fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif action == "export_fbx":
        bpy.ops.export_scene.fbx(filepath=path)
    return {"status": "OK", "path": path}

# Registry of audited handlers
OPCODE_MAP = {
    "transform": handle_transform,
    "system_op": handle_system_op,
    "modifier_op": handle_modifier,
    "material_op": handle_material,
    "mesh_op": handle_mesh_op,
    "lighting_op": handle_lighting,
    "constraint_op": handle_constraint,
    "physics_op": handle_physics,
    "io_op": handle_io,
    "viseme_op": lambda d: {"status": "VOX_ACK"},
    "bake_op": lambda d: {"status": "OVEN_ACK"}
}
