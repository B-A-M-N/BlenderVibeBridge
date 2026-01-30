# BlenderVibeBridge: Dual-License & Maintenance Agreement (v1.2)
# Copyright (C) 2026 B-A-M-N (The "Author")
#
# This software is distributed under a Dual-Licensing Model:
# 1. THE OPEN-SOURCE PATH: GNU AGPLv3 (see LICENSE for details)
# 2. THE COMMERCIAL PATH: "WORK-OR-PAY" MODEL

bl_info = {
    "name": "BlenderVibeBridge",
    "author": "B-A-M-N",
    "version": (1, 2, 1),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Vibe Bridge",
    "description": "Governed Geometry Kernel for AI-Assisted Production",
    "category": "Pipeline",
}

import bpy, os, json, time, math, mathutils, ast, uuid, hashlib, sys

# --- CONFIGURATION ---
VIBE_TOKEN = "VIBE_BRIDGE_SECURE_TOKEN_2026"
BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INBOX_PATH = os.path.join(BASE_PATH, "vibe_queue", "inbox")
OUTBOX_PATH = os.path.join(BASE_PATH, "vibe_queue", "outbox")
LOG_PATH = os.path.join(BASE_PATH, "bridge.log")
METADATA_PATH = os.path.join(BASE_PATH, "metadata", "vibe_health.json")

def get_ctx():
    if not os.path.exists(METADATA_PATH):
        os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
        with open(METADATA_PATH, "w") as f:
            json.dump({"status": "Ready", "progress": 0, "session_id": str(uuid.uuid4()), "current_op": "Idle"}, f)
    try:
        with open(METADATA_PATH, "r") as f: return json.load(f)
    except: return {"status": "Error", "progress": 0}

def vibe_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f: f.write(f"[{ts}] {msg}\n")

class VibeAuditLogger:
    @staticmethod
    def log(cmd_type, status, result=None, msg=None):
        audit_path = os.path.join(BASE_PATH, "logs", "vibe_audit.jsonl")
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        entry = {"ts": time.time(), "cmd": cmd_type, "status": status, "res": result, "msg": msg}
        with open(audit_path, "a") as f: f.write(json.dumps(entry) + "\n")

class TransactionManager:
    _active = False
    @classmethod
    def begin(cls):
        cls._active = True
        bpy.ops.ed.undo_push(message="Vibe Transaction Start")
        vibe_log("TRANSACTION: BEGUN")
    @classmethod
    def commit(cls):
        cls._active = False
        bpy.ops.ed.undo_push(message="Vibe Transaction Commit")
        vibe_log("TRANSACTION: COMMITTED")
    @classmethod
    def rollback(cls):
        cls._active = False
        if bpy.ops.ed.undo.poll(): bpy.ops.ed.undo()
        vibe_log("TRANSACTION: ROLLED BACK")
    @classmethod
    def mark_step(cls): pass

class ContextGuard:
    def __enter__(self):
        self.original_mode = bpy.context.mode
        self.active_name = bpy.context.active_object.name if bpy.context.active_object else None
        if bpy.ops.object.mode_set.poll(): bpy.ops.object.mode_set(mode='OBJECT')
    def __exit__(self, exc_type, exc_value, traceback):
        if self.active_name:
            obj = bpy.data.objects.get(self.active_name)
            if obj: bpy.context.view_layer.objects.active = obj
        if self.original_mode in {'SCULPT', 'EDIT_MESH', 'PAINT_TEXTURE'}:
            try:
                mode_map = {'EDIT_MESH': 'EDIT', 'PAINT_TEXTURE': 'TEXTURE_PAINT'}
                target = mode_map.get(self.original_mode, self.original_mode)
                if bpy.ops.object.mode_set.poll(): bpy.ops.object.mode_set(mode=target)
            except: pass

class ModelingKernel:
    @staticmethod
    def validate_mutation(data):
        cmd, props = data.get("type"), data.get("props", {})
        if cmd == "modifier_op" and data.get("mod_type") == "SUBSURF":
            if int(props.get("levels", 0)) > 3: return False, "Subdiv capped at 3"
        if bpy.context.scene.render.engine == 'CYCLES':
            try: bpy.context.scene.cycles.shading_system = False
            except: pass
        if cmd == "lighting_op" and float(data.get("energy", 0)) > 10000: return False, "Energy cap"
        return True, None

    @staticmethod
    def execute(data):
        cmd = data.get("type")
        vibe_log(f"EXEC: {cmd}")
        safe, reason = ModelingKernel.validate_mutation(data)
        if not safe: return {"status": "BLOCKED", "reason": reason}
        target = data.get("name") or data.get("target")
        if target:
            obj = bpy.data.objects.get(target) or bpy.data.materials.get(target)
            if obj and hasattr(obj, "library") and obj.library: return {"status": "BLOCKED", "reason": "Linked asset"}
        
        with ContextGuard():
            try:
                if cmd == "system_op":
                    action = data.get("action")
                    if action == "begin_transaction": TransactionManager.begin(); return {"status": "SUCCESS"}
                    elif action == "commit_transaction": TransactionManager.commit(); return {"status": "SUCCESS"}
                    elif action == "rollback_transaction": TransactionManager.rollback(); return {"status": "SUCCESS"}
                
                if not TransactionManager._active: bpy.ops.ed.undo_push(message=f"Vibe: {cmd}")
                res = ModelingKernel._dispatch(cmd, data)
                VibeAuditLogger.log(cmd, "SUCCESS", result=res)
                return {"status": "SUCCESS", "result": res}
            except Exception as e:
                vibe_log(f"Kernel Error: {e}")
                return {"status": "ERROR", "message": str(e)}

    @staticmethod
    def _dispatch(cmd, data):
        if cmd == "run_op":
            op_path = data.get("op").split(".")
            func = bpy.ops
            for part in op_path: func = getattr(func, part)
            func(**{k: ast.literal_eval(str(v)) for k, v in data.get("props", {}).items()})
            return "OK"
        elif cmd == "exec_script":
            exec(data.get("script"), {"bpy": bpy, "mathutils": mathutils, "math": math, "vibe_log": vibe_log})
            return "OK"
        elif cmd == "transform":
            obj = bpy.data.objects.get(data.get("name"))
            if obj:
                op, val = data.get("op"), ast.literal_eval(data.get("value"))
                if op == "translate": obj.location = val
                elif op == "rotate": obj.rotation_euler = [math.radians(v) for v in val]
                elif op == "scale": obj.scale = val
            return "OK"
        elif cmd == "modifier_op":
            obj = bpy.data.objects.get(data.get("name"))
            if obj:
                action, mod_name = data.get("action"), data.get("mod_name")
                if action == "add": obj.modifiers.new(name=mod_name, type=data.get("mod_type"))
                elif action == "remove":
                    m = obj.modifiers.get(mod_name); 
                    if m: obj.modifiers.remove(m)
                elif action == "set":
                    m = obj.modifiers.get(mod_name)
                    if m: 
                        for p, v in data.get("props", {}).items(): setattr(m, p, ast.literal_eval(str(v)))
            return "OK"
        elif cmd == "node_op":
            mat = bpy.data.materials.get(data.get("name"))
            if mat:
                mat.use_nodes = True
                if data.get("action") == "add": mat.node_tree.nodes.new(data.get("node_type"))
                elif data.get("action") == "link":
                    t = mat.node_tree
                    t.links.new(t.nodes.get(data.get("from_node")).outputs[0], t.nodes.get(data.get("to_node")).inputs[0])
            return "OK"
        elif cmd == "lighting_op":
            l_data = bpy.data.lights.new(name=data.get("name"), type=data.get("type_light", "POINT"))
            obj = bpy.data.objects.new(name=data.get("name"), object_data=l_data)
            bpy.context.collection.objects.link(obj)
            l_data.energy = float(data.get("energy", 10.0))
            return "OK"
        elif cmd == "material_op":
            mat = bpy.data.materials.new(name=data.get("name"))
            mat.use_nodes = True
            if data.get("obj_name"):
                obj = bpy.data.objects.get(data.get("obj_name")),
                if obj: obj.data.materials.append(mat)
            return "OK"
        elif cmd == "physics_op":
            obj = bpy.data.objects.get(data.get("name")),
            if obj:
                if data.get("phys_type") == "CLOTH": obj.modifiers.new(name="Cloth", type='CLOTH')
                elif data.get("phys_type") == "RIGID_BODY": 
                    bpy.context.view_layer.objects.active = obj; bpy.ops.rigidbody.object_add()
            return "OK"
        elif cmd == "audit_op":
            action = data.get("action")
            if action == "check_deps": return [bpy.path.abspath(img.filepath) for img in bpy.data.images if img.filepath and not os.path.exists(bpy.path.abspath(img.filepath))]
            elif action == "identity":
                obj = bpy.data.objects.get(data.get("target")),
                return f"{len(obj.data.vertices)}_{len(obj.material_slots)}" if obj and hasattr(obj.data, 'vertices') else "N/A"
            return "OK"
        elif cmd == "cleanup_op":
            if data.get("action") == "purge_orphans":
                for _ in range(3):
                    if bpy.ops.outliner.orphans_purge.poll(): bpy.ops.outliner.orphans_purge(do_local_ids=True, do_recursive=True)
            return "OK"
        elif cmd == "viseme_op":
            obj = bpy.data.objects.get(data.get("name")),
            if obj and obj.type == 'MESH':
                if not obj.data.shape_keys: obj.shape_key_add(name="Basis")
                if data.get("viseme") not in obj.data.shape_keys.key_blocks: obj.shape_key_add(name=data.get("viseme")),
            return "OK"
        elif cmd == "unity_op":
            action, target = data.get("action"), data.get("target")
            if action == "validate_humanoid":
                obj = bpy.data.objects.get(target)
                if not obj or obj.type != 'ARMATURE': return "Invalid"
                return "Valid" if all(b in obj.pose.bones for b in ["Hips", "Spine", "Head"]) else "Incomplete"
            return "OK"
        return f"Unhandled: {cmd}"

def poll_airlock():
    if not os.path.exists(INBOX_PATH): os.makedirs(INBOX_PATH, exist_ok=True)
    if not os.path.exists(OUTBOX_PATH): os.makedirs(OUTBOX_PATH, exist_ok=True)
    files = [f for f in os.listdir(INBOX_PATH) if f.endswith(".json")]; files.sort()
    if not files: return
    f = files[0]; path = os.path.join(INBOX_PATH, f)
    try:
        with open(path, "r") as file: data = json.load(file)
        result = ModelingKernel.execute(data)
        res_path = os.path.join(OUTBOX_PATH, "res_" + f)
        tmp = res_path + "." + str(uuid.uuid4())[:8] + ".tmp"
        with open(tmp, "w") as rf: json.dump(result, rf)
        os.replace(tmp, res_path)
    except Exception as e: vibe_log(f"Airlock Error: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

def main_loop():
    poll_airlock()
    return 0.1

def register():
    bpy.utils.register_class(VIBE_OT_StartBridge)
    bpy.utils.register_class(VIBE_PT_Panel)
    if not bpy.app.timers.is_registered(main_loop): bpy.app.timers.register(main_loop)

def unregister():
    bpy.utils.unregister_class(VIBE_PT_Panel)
    bpy.utils.unregister_class(VIBE_OT_StartBridge)
    if bpy.app.timers.is_registered(main_loop): bpy.app.timers.unregister(main_loop)

class VIBE_OT_StartBridge(bpy.types.Operator):
    bl_idname = "vibe.start_bridge"; bl_label = "Start Vibe Bridge"
    def execute(self, context):
        if not bpy.app.timers.is_registered(main_loop): bpy.app.timers.register(main_loop)
        return {'FINISHED'}

class VIBE_PT_Panel(bpy.types.Panel):
    bl_label = "Vibe Bridge"; bl_idname = "VIBE_PT_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = 'Vibe'
    def draw(self, context):
        self.layout.label(text=f"Status: Ready"); self.layout.operator("vibe.start_bridge")

if __name__ == "__main__": register()
