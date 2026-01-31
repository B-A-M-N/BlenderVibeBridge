# BlenderVibeBridge: Dual-License & Maintenance Agreement (v1.2)
# Copyright (C) 2026 B-A-M-N (The "Author")
#
# This software is distributed under a Dual-Licensing Model:
# 1. THE OPEN-SOURCE PATH: GNU AGPLv3 (see LICENSE for details)
# 2. THE COMMERCIAL PATH: "WORK-OR-PAY" MODEL

bl_info = {
    "name": "BlenderVibeBridge",
    "author": "B-A-M-N",
    "version": (1, 3, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Vibe",
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

# --- UTILITIES ---
def get_host_fingerprint():
    """Pillar 7: Detects environment drift."""
    data = {
        "blender": bpy.app.version_string,
        "platform": sys.platform,
        "addons": sorted([m.bl_info.get("name") for m in bpy.context.preferences.addons if hasattr(m, "bl_info")]),
        "python": sys.version
    }
    return hashlib.sha256(json.dumps(data).encode()).hexdigest()

def get_ctx():
    if not os.path.exists(METADATA_PATH):
        os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
        with open(METADATA_PATH, "w") as f:
            json.dump({
                "status": "Ready", "progress": 0, "session_id": str(uuid.uuid4()), 
                "current_op": "Idle", "host_fingerprint": get_host_fingerprint(),
                "governance_tier": "FULL", "mutation_budget": 100, "last_replenish": time.time(),
                "failure_count": 0, "last_mutation_time": 0
            }, f)
    try:
        with open(METADATA_PATH, "r") as f: ctx = json.load(f)
        # Pillar 4: Time-based Budget Replenishment (+10 per 10 mins, cap 100)
        now = time.time()
        mins_passed = (now - ctx.get("last_replenish", now)) / 60
        if mins_passed >= 10:
            replenish = int(mins_passed / 10) * 10
            ctx["mutation_budget"] = min(100, ctx.get("mutation_budget", 100) + replenish)
            ctx["last_replenish"] = now
            with open(METADATA_PATH, "w") as f: json.dump(ctx, f)
        return ctx
    except: return {"status": "Error", "progress": 0}

def vibe_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f: f.write(f"[{ts}] {msg}\n")

class VibeAuditLogger:
    @staticmethod
    def log(cmd_type, status, result=None, msg=None, pre_hash=None, post_hash=None):
        audit_path = os.path.join(BASE_PATH, "logs", "vibe_audit.jsonl")
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        entry = {"ts": time.time(), "cmd": cmd_type, "status": status, "res": result, "msg": msg, "pre": pre_hash, "post": post_hash}
        with open(audit_path, "a") as f: f.write(json.dumps(entry) + "\n")

class TransactionManager:
    _active = False
    @classmethod
    def begin(cls):
        cls._active = True; bpy.ops.ed.undo_push(message="Vibe Transaction Start")
    @classmethod
    def commit(cls):
        cls._active = False; bpy.ops.ed.undo_push(message="Vibe Transaction Commit")
    @classmethod
    def rollback(cls):
        cls._active = False; 
        if bpy.ops.ed.undo.poll(): bpy.ops.ed.undo()

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
    INTENT_MAP = {
        "OPTIMIZE": ["modifier_op", "mesh_op", "cleanup_op", "audit_op"],
        "RIG": ["constraint_op", "vg_op", "unity_op", "audit_op"],
        "LIGHT": ["lighting_op", "world_op", "viewport_op", "node_op"],
        "ANIMATE": ["animation_op", "viseme_op", "system_op"],
        "SCENE_SETUP": ["run_op", "io_op", "collection_op", "camera_op", "link_op", "curve_op", "material_op", "audio_op", "lock_op"],
        "GENERAL": ["audit_op", "system_op", "render_op"]
    }

    @staticmethod
    def get_scene_hash():
        data = sorted([(o.name, o.type, list(o.location)) for o in bpy.data.objects])
        return hashlib.sha256(json.dumps(data).encode()).hexdigest()

    @staticmethod
    def validate_semantic_sanity(val):
        if isinstance(val, (list, tuple, mathutils.Vector, mathutils.Euler)):
            return all(ModelingKernel.validate_semantic_sanity(x) for x in val)
        if isinstance(val, (int, float)):
            if math.isnan(val) or math.isinf(val): return False
            if abs(val) > 1000000: return False
        return True

    @staticmethod
    def validate_mutation(data):
        cmd, props = data.get("type"), data.get("props", {})
        ctx = get_ctx()
        if ctx.get("governance_tier") == "BLOCKED": return False, "REVOKED_BLOCKED"
        if ctx.get("governance_tier") == "READ_ONLY" and cmd != "audit_op": return False, "REVOKED_READ_ONLY"
        
        if cmd not in ["audit_op", "system_op"]:
            if ctx.get("mutation_budget", 0) <= 0: return False, "BUDGET_EXHAUSTED"
        
        intent = data.get("intent", "GENERAL")
        if cmd not in ModelingKernel.INTENT_MAP.get(intent, ["audit_op"]):
            return False, f"INTENT_MISMATCH: {cmd} not in {intent}"

        now = time.time()
        if now - ctx.get("last_mutation_time", 0) < 0.2: return False, "RATE_LIMIT"
        if ctx.get("host_fingerprint") != get_host_fingerprint(): return False, "ENVIRONMENT_DRIFT"

        for k, v in data.items():
            if k in ["value", "location", "rotation", "scale", "energy"]:
                try:
                    if not ModelingKernel.validate_semantic_sanity(ast.literal_eval(str(v))): return False, f"SEMANTIC_REJECTION: {k}"
                except: pass
        
        if cmd == "modifier_op" and data.get("mod_type") == "SUBSURF":
            if int(props.get("levels", 0)) > 3: return False, "Subdiv capped at 3"
        if bpy.context.scene.render.engine == 'CYCLES': bpy.context.scene.cycles.shading_system = False
        return True, None

    @staticmethod
    def execute(data):
        cmd = data.get("type")
        ctx = get_ctx()
        pre_hash = ModelingKernel.get_scene_hash()
        is_dry_run = data.get("dry_run", False)

        safe, reason = ModelingKernel.validate_mutation(data)
        if not safe:
            ctx["failure_count"] = ctx.get("failure_count", 0) + 1
            if ctx["failure_count"] > 10: ctx["governance_tier"] = "READ_ONLY"
            if ctx["failure_count"] > 20: ctx["governance_tier"] = "BLOCKED"
            with open(METADATA_PATH, "w") as f: json.dump(ctx, f)
            VibeAuditLogger.log(cmd, "BLOCKED", msg=reason)
            return {"status": "BLOCKED", "reason": reason}

        with ContextGuard():
            try:
                if is_dry_run:
                    bpy.ops.ed.undo_push(message="Vibe Dry Run")
                    try:
                        res = ModelingKernel._dispatch(cmd, data)
                        post_hash = ModelingKernel.get_scene_hash()
                        delta = "Change" if pre_hash != post_hash else "NoChange"
                        return {"status": "SUCCESS", "dry_run": True, "delta": delta, "result": res}
                    finally:
                        if bpy.ops.ed.undo.poll(): bpy.ops.ed.undo()

                if cmd == "system_op":
                    action = data.get("action")
                    if action == "begin_transaction": TransactionManager.begin(); return {"status": "SUCCESS"}
                    elif action == "commit_transaction": TransactionManager.commit(); return {"status": "SUCCESS"}
                    elif action == "rollback_transaction": TransactionManager.rollback(); return {"status": "SUCCESS"}

                if not TransactionManager._active: bpy.ops.ed.undo_push(message=f"Vibe: {cmd}")
                res = ModelingKernel._dispatch(cmd, data)
                
                ctx["last_mutation_time"] = time.time()
                if cmd not in ["audit_op", "system_op"]: ctx["mutation_budget"] = max(0, ctx.get("mutation_budget", 100) - 1)
                with open(METADATA_PATH, "w") as f: json.dump(ctx, f)

                VibeAuditLogger.log(cmd, "SUCCESS", result=res, pre_hash=pre_hash, post_hash=ModelingKernel.get_scene_hash())
                return {"status": "SUCCESS", "result": res}
            except Exception as e:
                VibeAuditLogger.log(cmd, "ERROR", msg=str(e))
                return {"status": "ERROR", "message": str(e)}

    @staticmethod
    def _dispatch(cmd, data):
        props = data.get("props", {})
        if cmd == "run_op":
            op_path = data.get("op").split(".")
            func = bpy.ops
            for part in op_path: func = getattr(func, part)
            func(**{k: ast.literal_eval(str(v)) for k, v in props.items()})
            return "OK"
        elif cmd == "exec_script":
            try:
                sys.path.append(os.path.join(BASE_PATH, "mcp-server"))
                from security_gate import SecurityGate
                if SecurityGate.check_python(data.get("script")): raise Exception("Security Block")
            except: raise Exception("Audit Fail")
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
            obj = bpy.data.objects.get(data.get("name")),
            if obj:
                action, mod_name = data.get("action"), data.get("mod_name")
                if action == "add": obj.modifiers.new(name=mod_name, type=data.get("mod_type"))
                elif action == "remove":
                    m = obj.modifiers.get(mod_name); 
                    if m: obj.modifiers.remove(m)
                elif action == "set":
                    m = obj.modifiers.get(mod_name)
                    if m: 
                        for p, v in props.items(): setattr(m, p, ast.literal_eval(str(v)))
            return "OK"
        elif cmd == "node_op":
            mat = bpy.data.materials.get(data.get("name")),
            if mat:
                mat.use_nodes = True
                if data.get("action") == "add": mat.node_tree.nodes.new(data.get("node_type"))
                elif data.get("action") == "link":
                    t = mat.node_tree
                    t.links.new(t.nodes.get(data.get("from_node")).outputs[0], t.nodes.get(data.get("to_node")).inputs[0])
            return "OK"
        elif cmd == "lighting_op":
            l_data = bpy.data.lights.new(name=data.get("name"), type=data.get("type_light", "POINT")),
            obj = bpy.data.objects.new(name=data.get("name"), object_data=l_data)
            bpy.context.collection.objects.link(obj); l_data.energy = float(data.get("energy", 10.0))
            return "OK"
        elif cmd == "material_op":
            mat = bpy.data.materials.new(name=data.get("name")),
            mat.use_nodes = True
            if data.get("obj_name"):
                obj = bpy.data.objects.get(data.get("obj_name"))
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
                if data.get("viseme") not in obj.data.shape_keys.key_blocks: obj.shape_key_add(name=data.get("viseme"))
            return "OK"
        elif cmd == "unity_op":
            action, target = data.get("action"), data.get("target")
            if action == "validate_humanoid":
                obj = bpy.data.objects.get(target)
                if not obj or obj.type != 'ARMATURE': return "Invalid"
                return "Valid" if all(b in obj.pose.bones for b in ["Hips", "Spine", "Head"]) else "Incomplete"
            return "OK"
        elif cmd == "animation_op":
            obj = bpy.data.objects.get(data.get("name")),
            if obj: obj.keyframe_insert(data_path=data.get("prop"), frame=data.get("frame", 1))
            return "OK"
        elif cmd == "camera_op":
            c_data = bpy.data.cameras.new(name=data.get("name")),
            obj = bpy.data.objects.new(name=data.get("name"), object_data=c_data)
            bpy.context.collection.objects.link(obj)
            return "OK"
        elif cmd == "io_op":
            if data.get("action") == "export_fbx": bpy.ops.export_scene.fbx(filepath=data.get("filepath"))
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
    poll_airlock(); return 0.1

def register():
    bpy.utils.register_class(VIBE_OT_StartBridge); bpy.utils.register_class(VIBE_PT_Panel)
    if not bpy.app.timers.is_registered(main_loop): bpy.app.timers.register(main_loop)

def unregister():
    bpy.utils.unregister_class(VIBE_PT_Panel); bpy.utils.unregister_class(VIBE_OT_StartBridge)
    if bpy.app.timers.is_registered(main_loop): bpy.app.timers.unregister(main_loop)

class VIBE_OT_StartBridge(bpy.types.Operator):
    bl_idname = "vibe.start_bridge"; bl_label = "Start Vibe Bridge"
    def execute(self, context):
        if not bpy.app.timers.is_registered(main_loop): bpy.app.timers.register(main_loop)
        return {'FINISHED'}

class VIBE_PT_Panel(bpy.types.Panel):
    bl_label = "Vibe Bridge Kernel"; bl_idname = "VIBE_PT_panel"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = 'Vibe'
    def draw(self, context):
        layout, ctx = self.layout, get_ctx()
        box = layout.box()
        tier = ctx.get("governance_tier", "UNKNOWN")
        row = box.row(); row.label(text=f"Tier: {tier}")
        box.label(text=f"Budget: {ctx.get('mutation_budget', 0)} / 100", icon='FUND')
        box.label(text=f"Failures: {ctx.get('failure_count', 0)}", icon='ERROR')
        box.label(text=f"Task: {ctx.get('current_op', 'Idle')}")
        layout.operator("vibe.start_bridge", icon='PLAY')

if __name__ == "__main__": register()