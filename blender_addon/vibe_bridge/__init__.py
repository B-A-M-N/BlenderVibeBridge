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

bl_info = {
    "name": "BlenderVibeBridge",
    "author": "Vibe Bridge Team",
    "version": (1, 2, 1),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Vibe Bridge",
    "description": "Governed Geometry Kernel for AI-Assisted Production",
    "category": "Pipeline",
}

import bpy
import threading
import queue
import http.server
import socketserver
import ast
import uuid
import os
import sys
import time
import mathutils
import json
import logging
import math
try:
    import psutil
except ImportError:
    psutil = None
import hashlib
from datetime import datetime

try:
    import gpu
except:
    gpu = None

# --- Configuration ---
PORT = 22000
PORT_DATA = 22001
VIBE_TOKEN = "VIBE_777_SECURE"
BRIDGE_NAMESPACE = "VIBE_BRIDGE_PRO"
# Use absolute path relative to the addon folder for maximum portability
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INBOX_PATH = os.path.join(BASE_PATH, "vibe_queue/inbox")
OUTBOX_PATH = os.path.join(BASE_PATH, "vibe_queue/outbox")
LOG_FILE = os.path.join(BASE_PATH, "bridge.log")
AUDIT_LOG = os.path.join(BASE_PATH, "logs/vibe_audit.jsonl")

# --- Context Helper ---
def get_ctx():
    if BRIDGE_NAMESPACE not in bpy.app.driver_namespace:
        bpy.app.driver_namespace[BRIDGE_NAMESPACE] = {}
    ctx = bpy.app.driver_namespace[BRIDGE_NAMESPACE]
    defaults = {"generation": 0, "state": "STOPPED", "server": None, "server_data": None, "queue": queue.Queue(), "sync_queue": queue.Queue(), "session_id": None}
    for k, v in defaults.items():
        if k not in ctx: ctx[k] = v
    return ctx

# --- Structured Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("VibeBridge")

def vibe_log(msg):
    logger.info(msg)

def run_in_main(func):
    ctx = get_ctx()
    if ctx["state"] != "RUNNING":
        return {"error": "Bridge not running"}
    
    # If we are already on main thread (e.g. debugging), just run it
    if threading.current_thread() == threading.main_thread():
        return func()
    
    event = threading.Event()
    holder = {}
    ctx["sync_queue"].put((func, holder, event))
    
    # Wait with timeout to prevent server hang
    if not event.wait(timeout=10.0):
        return {"error": "Main thread dispatch timeout (Blender may be busy or hung)"}
    
    if "error" in holder:
        raise holder["error"]
    return holder["data"]

class VibeAuditLogger:
    @staticmethod
    def log(cmd_type, status, result=None, msg=None):
        entry = {
            "ts": datetime.now().isoformat(),
            "type": cmd_type,
            "status": status,
            "res": result,
            "msg": msg,
            "session": get_ctx().get("session_id")
        }
        os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
        with open(AUDIT_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

# --- Hardware Sentinel ---
class ResourceMonitor:
    @staticmethod
    def get_stats():
        vram_mb = 0
        try:
            if gpu: vram_mb = gpu.capabilities.device_info.get('device_memory', 0)
        except: pass
        return {
            "ram_pct": psutil.virtual_memory().percent if psutil else 0,
            "vram_mb": vram_mb,
            "cpu_pct": psutil.cpu_percent() if psutil else 0
        }

    @staticmethod
    def is_safe(is_heavy=False):
        stats = ResourceMonitor.get_stats()
        if psutil is None:
            vibe_log("WARNING: psutil missing. Resource protection disabled.")

        if stats["ram_pct"] > 90: return False, "RAM CRITICAL (>90%)"
        if is_heavy and stats["vram_mb"] > 0 and stats["vram_mb"] < 512:
            return False, "VRAM LOW (<512MB) - Blocking heavy op"
        return True, None

# --- Transaction Manager (Compound Undo) ---
class TransactionManager:
    _active = False
    _steps = 0

    @classmethod
    def begin(cls):
        cls._active = True
        cls._steps = 0
        bpy.ops.ed.undo_push(message="Vibe Transaction Start")
        vibe_log("TRANSACTION: BEGUN")

    @classmethod
    def commit(cls):
        cls._active = False
        cls._steps = 0
        bpy.ops.ed.undo_push(message="Vibe Transaction Commit")
        vibe_log("TRANSACTION: COMMITTED")

    @classmethod
    def mark_step(cls):
        if cls._active: cls._steps += 1

    @classmethod
    def rollback(cls):
        cls._active = False
        # If we pushed a single "Transaction Start" block, one undo reverts the whole set
        if bpy.ops.ed.undo.poll(): 
            bpy.ops.ed.undo()
        vibe_log("TRANSACTION: ROLLED BACK")

# --- Production & Avatar Pipeline ---
class ProductionPipeline:
    @staticmethod
    def validate_humanoid(armature_name):
        obj = bpy.data.objects.get(armature_name)
        if not obj or obj.type != 'ARMATURE': return False, "Not an armature"
        required_bones = ["Hips", "Spine", "Chest", "Neck", "Head", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot"]
        missing = [b for b in required_bones if b not in obj.pose.bones]
        if missing: return False, f"Missing humanoid bones: {missing}"
        return True, "Humanoid rig valid"

    @staticmethod
    def optimize_mesh(obj_name, ratio=0.5):
        obj = bpy.data.objects.get(obj_name)
        if not obj or obj.type != 'MESH': return False
        mod = obj.modifiers.new(name="VibeOptimize", type='DECIMATE')
        mod.ratio = ratio
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier="VibeOptimize")
        return True

class ContextGuard:
    def __enter__(self):
        self.active_obj = bpy.context.view_layer.objects.active
        self.active_name = self.active_obj.name if self.active_obj else None
        self.selected_names = [o.name for o in bpy.context.selected_objects]
        self.original_mode = bpy.context.mode
        self.original_mesh_version = self._get_mesh_version()
        return self

    def _get_mesh_version(self):
        """Returns a signature of the active mesh to check for structural changes."""
        if self.active_obj and self.active_obj.type == 'MESH':
            return (len(self.active_obj.data.vertices), len(self.active_obj.data.polygons))
        return None

    def __exit__(self, exc_type, exc_value, traceback):
        # 1. Always ensure we drop to Object mode to finish cleanly
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # 2. Restore Selection
        bpy.ops.object.select_all(action='DESELECT')
        for name in self.selected_names:
            obj = bpy.data.objects.get(name)
            if obj: obj.select_set(True)
        
        # 3. Restore Active
        if self.active_name:
            obj = bpy.data.objects.get(self.active_name)
            if obj: bpy.context.view_layer.objects.active = obj

        # 4. MODE RUBBER-BANDING
        # Only attempt to go back to a 'Sensitive' mode if the mesh structure is identical.
        if self.original_mode in {'SCULPT', 'EDIT_MESH', 'PAINT_TEXTURE', 'PAINT_VERTEX'}:
            if self._get_mesh_version() == self.original_mesh_version:
                try:
                    mode_map = {'EDIT_MESH': 'EDIT', 'PAINT_TEXTURE': 'TEXTURE_PAINT', 'PAINT_VERTEX': 'VERTEX_PAINT'}
                    target_mode = mode_map.get(self.original_mode, self.original_mode)
                    bpy.ops.object.mode_set(mode=target_mode)
                    vibe_log(f"Rubber-Banded back to {target_mode}")
                except:
                    pass

class ModelingKernel:
    _handlers = {}

    @classmethod
    def register_handler(cls, cmd_type, func):
        cls._handlers[cmd_type] = func

    @staticmethod
    def get_main_context():
        """Returns a context override, handling Headless/Background mode."""
        if bpy.app.background or not bpy.context.window_manager.windows:
            return None
        
        try:
            win = bpy.context.window_manager.windows[0]
            area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'), None)
            region = next((r for r in area.regions if r.type == 'WINDOW'), None) if area else None
            override = bpy.context.copy()
            override['window'], override['screen'], override['area'], override['region'] = win, win.screen, area, region
            return override
        except:
            return None

    @staticmethod
    def update_progress(val, msg=""):
        ctx = get_ctx()
        ctx["progress"] = val
        ctx["current_op"] = msg

    @staticmethod
    def execute(data):
        cmd = data.get("type")
        vibe_log(f"ACTION: {cmd}")
        ModelingKernel.update_progress(0, f"Executing {cmd}")
        
        # 0. Mode Airlock
        try:
            if bpy.ops.object.mode_set.poll(): bpy.ops.object.mode_set(mode='OBJECT')
        except: pass

        # 0.5. Session Guard
        expected_sid = get_ctx().get("session_id")
        provided_sid = data.get("vibe_session_id")
        if provided_sid and expected_sid and provided_sid != expected_sid:
            reason = f"STALE_SESSION: {provided_sid} != {expected_sid}"
            return {"status": "BLOCKED", "reason": reason}

        # 1. Hardware Guard
        is_heavy = cmd in ["bake_op", "unity_op", "physics_op", "exec_script", "io_op"]
        safe, reason = ResourceMonitor.is_safe(is_heavy=is_heavy)
        if not safe: return {"status": "BLOCKED", "reason": reason}

        # 2. Transaction Control
        if cmd == "system_op":
            action = data.get("action")
            if action == "begin_transaction": TransactionManager.begin(); return {"status": "SUCCESS"}
            elif action == "commit_transaction": TransactionManager.commit(); return {"status": "SUCCESS"}
            elif action == "rollback_transaction": TransactionManager.rollback(); return {"status": "SUCCESS"}

        # 3. Registry Dispatch
        override = ModelingKernel.get_main_context()
        
        with ContextGuard():
            # Use temp_override if we have one (UI mode), else standard context (Headless)
            context_manager = bpy.context.temp_override(**override) if override else ModelingKernel._null_context()
            with context_manager:
                try:
                    if not TransactionManager._active:
                        bpy.ops.ed.undo_push(message=f"Vibe: {cmd}")
                    
                    # --- NEW REGISTRY-BASED DISPATCH ---
                    # For compatibility, we keep the old logic but modularize it
                    result_data = ModelingKernel._dispatch(cmd, data)
                    
                    ModelingKernel.update_progress(100, "Done")
                    VibeAuditLogger.log(cmd, "SUCCESS", result=result_data)
                    return {"status": "SUCCESS", "result": result_data}
                except Exception as e:
                    vibe_log(f"Kernel Error: {e}")
                    ModelingKernel.update_progress(0, f"Error: {e}")
                    if not TransactionManager._active: bpy.ops.ed.undo()
                    return {"status": "ERROR", "message": str(e)}

    @staticmethod
    def _null_context():
        """Empty context manager for headless modes."""
        class NullContext:
            def __enter__(self): pass
            def __exit__(self, *args): pass
        return NullContext()

    @staticmethod
    def _dispatch(cmd, data):
        """Core command router. Returns result_data."""
        if cmd == "run_op":
            TransactionManager.mark_step()
            op_path = data.get("op").split(".")
            func = bpy.ops
            for part in op_path: func = getattr(func, part)
            op_args = data.get("props", {})
            obs_before = set(bpy.data.objects.keys())
            func(**{k: ast.literal_eval(str(v)) for k, v in op_args.items()})
            for name in (set(bpy.data.objects.keys()) - obs_before): 
                ModelingKernel.tag_object(bpy.data.objects[name])
            return "OK"

        elif cmd == "exec_script":
            # RE-VALIDATE IN KERNEL (Defense in depth)
            try:
                from security_gate import SecurityGate
                violations = SecurityGate.check_python(data.get("script"))
                if violations: raise Exception(f"Security Violation: {violations[0]}")
            except Exception as e: 
                vibe_log(f"CRITICAL: Security Audit Failure: {e}")
                raise Exception(f"Infrastructure failure (Security Audit Required): {e}")

            sandbox_target = data.get("sandbox_target")
            if sandbox_target:
                orig_obj = bpy.data.objects.get(sandbox_target)
                if orig_obj:
                    bpy.ops.object.select_all(action='DESELECT')
                    orig_obj.select_set(True)
                    bpy.context.view_layer.objects.active = orig_obj
                    bpy.ops.object.duplicate()
                    sandbox_obj = bpy.context.active_object
                    try:
                        exec(data.get("script"), {"bpy": bpy, "mathutils": mathutils, "vibe_log": vibe_log, "math": math, "target": sandbox_obj})
                        orig_obj.data = sandbox_obj.data.copy()
                        res = "Sandbox Success"
                    finally: bpy.data.objects.remove(sandbox_obj, do_unlink=True)
                    return res
            
            exec(data.get("script"), {"bpy": bpy, "mathutils": mathutils, "vibe_log": vibe_log, "math": math})
            return "OK"

        elif cmd == "transform":
            obj = bpy.data.objects.get(data.get("name"))
            if obj:
                val_str = data.get("value")
                if val_str is None: return "Error: Missing transform value"
                op, val = data.get("op"), ast.literal_eval(val_str)
                if op == "translate": obj.location = val
                elif op == "rotate": obj.rotation_euler = [math.radians(v) for v in val]
                elif op == "scale": obj.scale = val
            return "OK"
                            op, val = data.get("op"), ast.literal_eval(val_str)
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
                                                mod = obj.modifiers.get(mod_name)
                                                if mod: obj.modifiers.remove(mod)
                                            elif action == "set":
                                                mod = obj.modifiers.get(mod_name)
                                                if mod:
                                                    props = data.get("props", {})
                                                    for p, v in props.items():
                                                        try: val = ast.literal_eval(str(v))
                                                        except: val = str(v)
                                                        setattr(mod, p, val)
                                        return "OK"
                            
                                    elif cmd == "node_op":
                                        target_name, action = data.get("name"), data.get("action")
                                        target_type = data.get("target_type", "SHADER")
                                        obj = bpy.data.objects.get(target_name)
                                        tree = None
                                        if target_type == "GEOMETRY":
                                            if not obj or obj.type != 'MESH': return "Error: Mesh required"
                                            mod = next((m for m in obj.modifiers if m.type == 'NODES'), None)
                                            if not mod: mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
                                            if not mod.node_group: mod.node_group = bpy.data.node_groups.new("VibeGeoNodes", 'GeometryNodeTree')
                                            tree = mod.node_group
                                        else:
                                            mat = bpy.data.materials.get(target_name) or (obj.active_material if obj and hasattr(obj, "active_material") else None)
                                            if not mat: return "Error: Material required"
                                            mat.use_nodes = True; tree = mat.node_tree
                                        if tree:
                                            if action == "add": tree.nodes.new(data.get("node_type"))
                                            elif action == "link":
                                                tree.links.new(tree.nodes.get(data.get("from_node")).outputs[data.get("from_socket")], 
                                                               tree.nodes.get(data.get("to_node")).inputs[data.get("to_socket")])
                                        return f"Node {action} success"
                            
                                    elif cmd == "lighting_op":
                                        light_data = bpy.data.lights.new(name=data.get("name"), type=data.get("type_light"))
                                        obj = bpy.data.objects.new(name=data.get("name"), object_data=light_data)
                                        bpy.context.collection.objects.link(obj)
                                        light_data.energy = data.get("energy", 10.0)
                                        light_data.color = ast.literal_eval(data.get("color", "(1,1,1)"))
                                        ModelingKernel.tag_object(obj)
                                        return "OK"
                                                elif cmd == "constraint_op":
                        obj = bpy.data.objects.get(data.get("name"))
                        if obj:
                            action, c_type, c_name = data.get("action"), data.get("c_type"), data.get("c_name")
                            if action == "add":
                                con = obj.constraints.new(type=c_type)
                                if data.get("target"): con.target = bpy.data.objects.get(data.get("target"))
                            elif action == "remove":
                                con = obj.constraints.get(c_name) or next((c for c in obj.constraints if c.type == c_type), None)
                                if con: obj.constraints.remove(con)
                            elif action == "set":
                                con = obj.constraints.get(c_name) or next((c for c in obj.constraints if c.type == c_type), None)
                                if con:
                                    props = data.get("props", {})
                                    for p, v in props.items():
                                        try: setattr(con, p, ast.literal_eval(str(v)))
                                        except: setattr(con, p, str(v))

                    elif cmd == "viewport_op":
                        for area in bpy.context.screen.areas:
                            if area.type == 'VIEW_3D': area.spaces.active.shading.type = data.get("mode", "SOLID")

                    elif cmd == "physics_op":
                        TransactionManager.mark_step()
                        obj = bpy.data.objects.get(data.get("name"))
                        if obj:
                            p_type = data.get("phys_type")
                            if p_type == "RIGID_BODY":
                                bpy.context.view_layer.objects.active = obj
                                bpy.ops.rigidbody.object_add()
                            elif p_type == "CLOTH": obj.modifiers.new(name="Cloth", type='CLOTH')
                            result_data = f"Applied {p_type} to {obj.name}"

                    elif cmd == "collection_op":
                        action, name = data.get("action"), data.get("name")
                        if action == "add":
                            col = bpy.data.collections.new(name)
                            bpy.context.scene.collection.children.link(col)
                        elif action == "link":
                            obj, col = bpy.data.objects.get(data.get("obj_name")), bpy.data.collections.get(name)
                            if obj and col: col.objects.link(obj)

                    elif cmd == "material_op":
                        mat = bpy.data.materials.new(name=data.get("name"))
                        mat.use_nodes = True
                        if data.get("obj_name"):
                            obj = bpy.data.objects.get(data.get("obj_name"))
                            if obj: obj.data.materials.append(mat)

                    elif cmd == "bake_op":
                        obj = bpy.context.active_object
                        if not obj or obj.type != 'MESH':
                            return {"status": "ERROR", "message": "No active mesh object for baking."}
                        
                        if not obj.data.uv_layers:
                            return {"status": "ERROR", "message": "Mesh has no UV coordinates."}

                        res = min(int(data.get("resolution", 1024)), 2048)
                        vibe_log(f"Baking {obj.name} at {res}px...")
                        
                        # Force Cycles for baking
                        bpy.context.scene.render.engine = 'CYCLES'
                        
                        # Create/Get Image
                        img_name = f"VibeBake_{obj.name}"
                        img = bpy.data.images.get(img_name) or bpy.data.images.new(img_name, res, res)
                        img.generated_width = res
                        img.generated_height = res
                        
                        # Material Node Setup
                        if not obj.active_material:
                            mat = bpy.data.materials.new(name=f"Mat_{obj.name}")
                            obj.data.materials.append(mat)
                        
                        mat = obj.active_material
                        mat.use_nodes = True
                        nodes = mat.node_tree.nodes
                        
                        # Create bake target node and make it active
                        bake_node = nodes.get("VIBE_BAKE_NODE") or nodes.new('ShaderNodeTexImage')
                        bake_node.name = "VIBE_BAKE_NODE"
                        bake_node.image = img
                        nodes.active = bake_node
                        
                        # Perform Bake
                        TransactionManager.mark_step()
                                    bpy.ops.object.bake(type='COMBINED')
                                    return f"Bake completed: {img.name}"
                        
                                elif cmd == "animation_op":
                                    obj = bpy.data.objects.get(data.get("name"))
                                    if obj: obj.keyframe_insert(data_path=data.get("prop"), frame=data.get("frame", 1))
                                    return "OK"
                        
                                elif cmd == "camera_op":
                                    cam_data = bpy.data.cameras.new(name=data.get("name"))
                                    cam_obj = bpy.data.objects.new(name=data.get("name"), object_data=cam_data)
                                    bpy.context.collection.objects.link(cam_obj)
                                    if data.get("active"): bpy.context.scene.camera = cam_obj
                                    return "OK"
                        
                                elif cmd == "world_op":
                                    bpy.context.scene.world.use_nodes = True
                                    bg = bpy.context.scene.world.node_tree.nodes.get("Background")
                                    if bg: bg.inputs[0].default_value = ast.literal_eval(data.get("color", "(0.05, 0.05, 0.05, 1)"))
                                    return "OK"
                        
                                elif cmd == "curve_op":
                                    curve_data = bpy.data.curves.new(name=data.get("name"), type='CURVE')
                                    curve_data.dimensions = '3D'
                                    polyline = curve_data.splines.new('POLY')
                                    coords = ast.literal_eval(data.get("coords", "[(0,0,0), (1,1,1)]"))
                                    polyline.points.add(len(coords)-1)
                                    for i, coord in enumerate(coords): polyline.points[i].co = (coord[0], coord[1], coord[2], 1)
                                    obj = bpy.data.objects.new(data.get("name"), curve_data)
                                    bpy.context.collection.objects.link(obj)
                                    return "OK"
                        
                                elif cmd == "lock_op":
                                    obj = bpy.data.objects.get(data.get("name"))
                                    if obj:
                                        for axis in data.get("axes", ["location", "rotation_euler", "scale"]):
                                            setattr(obj, f"lock_{axis}", data.get("lock", True))
                                    return "OK"
                        
                                elif cmd == "mesh_op":
                                    TransactionManager.mark_step()
                                    action = data.get("action")
                                    if action == "shade_smooth": bpy.ops.object.shade_smooth()
                                    elif action == "shade_flat": bpy.ops.object.shade_flat()
                                    elif action == "join": bpy.ops.object.join()
                                    return "OK"
                        
                                elif cmd == "vg_op":
                                    obj = bpy.data.objects.get(data.get("name"))
                                    if obj and obj.type == 'MESH': obj.vertex_groups.new(name=data.get("vg_name"))
                                    return "OK"
                        
                                elif cmd == "audio_op":
                                    speaker_data = bpy.data.speakers.new(name=data.get("name"))
                                    obj = bpy.data.objects.new(name=data.get("name"), object_data=speaker_data)
                                    bpy.context.collection.objects.link(obj)
                                    return "OK"
                        
                                elif cmd == "io_op":
                                    TransactionManager.mark_step()
                                    action, path = data.get("action"), data.get("filepath")
                                    if action == "export_fbx": bpy.ops.export_scene.fbx(filepath=path)
                                    elif action == "import_fbx": bpy.ops.import_scene.fbx(filepath=path)
                                    return "OK"
                        
                                elif cmd == "annotation_op":
                                    gp = bpy.data.grease_pencils.new("VibeNotes")
                                    obj = bpy.data.objects.new("VibeNotes", gp)
                                    bpy.context.collection.objects.link(obj)
                                    layer_name = data.get("text", "Note")[:32]
                                    gp.layers.new(layer_name).frames.new(1).strokes.new().points.add(1)
                                                return f"Annotation {obj.name} created."
                                    
                                            elif cmd == "link_op":
                                                with bpy.data.libraries.load(data.get("filepath"), link=True) as (data_from, data_to):
                                                    setattr(data_to, data.get("directory").lower() + "s", [data.get("name")])
                                                for obj in data_to.objects:
                                                    if obj: bpy.context.collection.objects.link(obj)
                                                return "OK"
                                    
                                            elif cmd == "macro_op":
                                                intent = data.get("intent")
                                                if intent == "RESTORE_AVATAR_COLORS_RED":
                                                    for mat in bpy.data.materials:
                                                        if "EXTO" in mat.name and mat.use_nodes:
                                                            bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                                                            if bsdf: bsdf.inputs['Base Color'].default_value = (1, 0, 0, 1)
                                                    return "OK"
                                                return "Unknown macro"
                                    
                                            elif cmd == "render_op":
                                                path = os.path.join(BASE_PATH, "vibe_capture.png")
                                                bpy.context.scene.render.filepath = path
                                                bpy.ops.render.opengl(write_still=True)
                                                return f"Saved to {path}"
                                    
                                            elif cmd == "cleanup_op":
                                                action = data.get("action")
                                                if action == "reset_material":
                                                    mat = bpy.data.materials.get(data.get("target"))
                                                    if mat:
                                                        mat.use_nodes = True; mat.node_tree.nodes.clear()
                                                        out = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
                                                        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
                                                        mat.node_tree.links.new(bsdf.outputs[0], out.inputs[0])
                                                elif action == "purge_orphans":
                                                    for _ in range(3):
                                                        if bpy.ops.outliner.orphans_purge.poll(): bpy.ops.outliner.orphans_purge(do_local_ids=True, do_recursive=True)
                                                return "OK"
                                    
                                            elif cmd == "audit_op":
                                                action = data.get("action")
                                                if action == "check_deps":
                                                    return [bpy.path.abspath(img.filepath) for img in bpy.data.images if img.filepath and not os.path.exists(bpy.path.abspath(img.filepath))]
                                                return "OK"
                                    
                                                    elif cmd == "unity_op":
                                                        action = data.get("action")
                                                        if action == "validate_humanoid": return ProductionPipeline.validate_humanoid(data.get("target"))
                                                        elif action == "optimize_avatar": return ProductionPipeline.optimize_mesh(data.get("target"), float(data.get("ratio", 0.5)))
                                                        return "OK"
                                                                                        elif cmd == "viseme_op":
                                                obj = bpy.data.objects.get(data.get("name"))
                                                if obj and obj.type == 'MESH':
                                                    if not obj.data.shape_keys: obj.shape_key_add(name="Basis")
                                                    if data.get("viseme") not in obj.data.shape_keys.key_blocks: obj.shape_key_add(name=data.get("viseme"))
                                                return "OK"
                                    
                                            elif cmd == "system_op":
                                                action = data.get("action")
                                                if action == "panic_downgrade":
                                                    for area in bpy.context.screen.areas:
                                                        if area.type == 'VIEW_3D': area.spaces.active.shading.type = 'SOLID'
                                                    return "Panic Active"
                                                return "OK"
                                            
                                            return "Unknown Command"
                                    
                    
                    VibeAuditLogger.log(cmd, "SUCCESS", result=result_data)
                    return {"status": "SUCCESS", "result": result_data}

                except Exception as e: 
                    vibe_log(f"Kernel Error: {e}")
                    VibeAuditLogger.log(cmd, "ERROR", msg=str(e))
                    return {"status": "ERROR", "message": str(e)}

def poll_airlock():
    if not os.path.exists(INBOX_PATH): return
    files = [f for f in os.listdir(INBOX_PATH) if f.endswith(".json")]; files.sort()
    if not files: return
    
    # Process only ONE file per tick to keep Blender UI responsive
    f = files[0]
    path = os.path.join(INBOX_PATH, f)
    try:
        with open(path, "r") as file: data = json.load(file)
        result = ModelingKernel.execute(data)
        
        # Atomic Write: Write to unique .tmp then rename to prevent MCP from reading partial JSON
        res_path = os.path.join(OUTBOX_PATH, "res_" + f)
        tmp_res_path = res_path + "." + str(uuid.uuid4())[:8] + ".tmp"
        try:
            with open(tmp_res_path, "w") as rf: json.dump(result, rf)
            os.replace(tmp_res_path, res_path)
        finally:
            if os.path.exists(tmp_res_path): os.remove(tmp_res_path)
    except Exception as e: vibe_log(f"Airlock Error: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

def main_loop():
    ctx = get_ctx()
    if ctx["state"] != "RUNNING" or bpy.app.is_animation_playing: return 0.1
    
    # ACTIVITY GATING: Do not process queue if the user is in the middle of a stroke
    # (Checking for 'GRAB' or 'SCULPT' status prevents interrupting a mouse-down session)
    if bpy.context.screen.is_animation_playing or (bpy.context.area and bpy.context.area.type == 'VIEW_3D' and bpy.context.mode in {'SCULPT', 'PAINT_TEXTURE'} and bpy.context.window_manager.is_interface_locked):
        return 0.1

    try:
        stats = ResourceMonitor.get_stats()
        with open(os.path.join(BASE_PATH, "metadata/vibe_health.json"), "w") as f: 
            json.dump({"status": "READY", "timestamp": time.time(), "session": ctx["session_id"], "hw": stats, "progress": ctx.get("progress", 0), "op": ctx.get("current_op", "")}, f)
    except: pass
    poll_airlock()
    
    # Process Sync Queue (Read Requests)
    while not ctx["sync_queue"].empty():
        func, holder, event = ctx["sync_queue"].get()
        try:
            holder["data"] = func()
        except Exception as e:
            holder["error"] = e
        event.set()
        ctx["sync_queue"].task_done()

    # Process Mutation Queue
    if not ctx["queue"].empty():
        ModelingKernel.execute(ctx["queue"].get())
        ctx["queue"].task_done()
    return 0.1

class VibeHandler(http.server.SimpleHTTPRequestHandler):
    def check_auth(self): return self.headers.get('X-Vibe-Token') == VIBE_TOKEN
    def do_GET(self):
        if self.path == "/status" and self.check_auth():
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            def _task():
                return {
                    "online": True,
                    "telemetry": [{"name": o.name, "type": o.type, "polys": len(o.data.polygons) if o.type=='MESH' else 0, "location": list(o.location), "dimensions": list(o.dimensions)} for o in bpy.data.objects],
                    "hw": ResourceMonitor.get_stats(),
                    "session": get_ctx().get("session_id")
                }
            self.wfile.write(json.dumps(run_in_main(_task)).encode())
        elif self.path == "/validate" and self.check_auth():
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            def _task():
                issues = []
                if not bpy.context.scene.camera: issues.append("Missing active camera")
                for o in bpy.data.objects:
                    if o.type == 'MESH' and any(s < 0.9 or s > 1.1 for s in o.scale): issues.append(f"Unapplied scale: {o.name}")
                return {"status": "OK" if not issues else "WARN", "issues": issues}
            self.wfile.write(json.dumps(run_in_main(_task)).encode())
        elif self.path.startswith("/forensic") and self.check_auth():
            import urllib.parse
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name = query.get("name", [None])[0]
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            def _task():
                obj = bpy.data.objects.get(name) if name else None
                if obj:
                    dump = {"name": obj.name, "type": obj.type, "location": list(obj.location)}
                    if obj.type == 'MESH': dump["verts"] = len(obj.data.vertices)
                    return dump
                return {"error": "Object not found"}
            self.wfile.write(json.dumps(run_in_main(_task)).encode())
        elif self.path == "/restart" and self.check_auth():
            self.send_response(202); self.end_headers(); threading.Thread(target=bootstrap).start()
        else: self.send_response(403); self.end_headers()
    def do_POST(self):
        if not self.check_auth(): self.send_response(403); self.end_headers(); return
        try:
            data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
            if self.path == "/command": get_ctx()["queue"].put(data); self.send_response(202); self.end_headers()
            elif self.path == "/query":
                self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps(run_in_main(lambda: ModelingKernel.execute(data))).encode())
            elif self.path == "/reconcile":
                self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
                def _task():
                    results = {}
                    for n, v in data.items():
                        obj = bpy.data.objects.get(n)
                        if not obj: continue
                        match = True
                        if "location" in v: match &= list(obj.location) == v["location"]
                        if "rotation" in v: match &= [round(math.degrees(a), 2) for a in obj.rotation_euler] == [round(a, 2) for a in v["rotation"]]
                        if "scale" in v: match &= [round(s, 3) for s in obj.scale] == [round(s, 3) for s in v["scale"]]
                        results[n] = {"match": match}
                    return results
                self.wfile.write(json.dumps(run_in_main(_task)).encode())
        except: self.send_response(400); self.end_headers()

class VibeDataHandler(http.server.SimpleHTTPRequestHandler):
    def log_request(self, *args): pass 
    def check_auth(self): return self.headers.get('X-Vibe-Token') == VIBE_TOKEN
    def do_GET(self):
        if not self.check_auth(): self.send_response(403); self.end_headers(); return
        if self.path == "/view":
            p = os.path.join(BASE_PATH, "vibe_capture.png")
            if os.path.exists(p):
                self.send_response(200); self.send_header('Content-type', 'image/png'); self.end_headers()
                with open(p, "rb") as f: self.wfile.write(f.read())
            else: self.send_response(404); self.end_headers()
        elif self.path == "/telemetry":
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            def _task():
                return {"hw": ResourceMonitor.get_stats(), "objs": len(bpy.data.objects)}
            self.wfile.write(json.dumps(run_in_main(_task)).encode())
        else: self.send_response(404); self.end_headers()

def bootstrap():
    ctx = get_ctx()
    # Ensure security gate is accessible to the kernel
    mcp_path = os.path.join(BASE_PATH, "mcp-server")
    if mcp_path not in sys.path: sys.path.append(mcp_path)

    if ctx.get("server"): 
        try: ctx["server"].shutdown(); ctx["server"].server_close()
        except: pass
    if ctx.get("server_data"): 
        try: ctx["server_data"].shutdown(); ctx["server_data"].server_close()
        except: pass
    ctx["generation"] += 1; ctx["session_id"] = str(uuid.uuid4())
    try:
        if not bpy.app.timers.is_registered(main_loop): bpy.app.timers.register(main_loop)
        socketserver.TCPServer.allow_reuse_address = True
        ctx["server"] = socketserver.TCPServer(("127.0.0.1", PORT), VibeHandler)
        threading.Thread(target=ctx["server"].serve_forever, daemon=True).start()
        socketserver.TCPServer.allow_reuse_address = True
        ctx["server_data"] = socketserver.TCPServer(("127.0.0.1", PORT_DATA), VibeDataHandler)
        threading.Thread(target=ctx["server_data"].serve_forever, daemon=True).start()
        ctx["state"] = "RUNNING"; vibe_log(f"VIBE KERNEL ONLINE (GEN {ctx['generation']})")
    except Exception as e: print(f"BOOT FAIL: {e}")

class VIBE_OT_StartBridge(bpy.types.Operator):
    bl_idname = "vibe.start_bridge"
    bl_label = "Start Vibe Bridge"
    def execute(self, context): bootstrap(); return {'FINISHED'}

class VIBE_PT_Panel(bpy.types.Panel):
    bl_label = "Vibe Bridge Control"
    bl_idname = "VIBE_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Vibe Bridge'
    def draw(self, context):
        layout, ctx = self.layout, get_ctx()
        layout.label(text=f"Status: {ctx['state']}")
        layout.operator("vibe.start_bridge")

def register():
    bpy.utils.register_class(VIBE_OT_StartBridge); bpy.utils.register_class(VIBE_PT_Panel); bootstrap()

def unregister():
    bpy.utils.unregister_class(VIBE_OT_StartBridge); bpy.utils.unregister_class(VIBE_PT_Panel)
    ctx = get_ctx()
    if ctx["server"]: ctx["server"].shutdown()
    if ctx["server_data"]: ctx["server_data"].shutdown()

if __name__ == "__main__": register()