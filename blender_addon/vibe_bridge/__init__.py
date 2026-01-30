bl_info = {
    "name": "BlenderVibeBridge",
    "author": "Vibe Bridge Team",
    "version": (1, 0, 0),
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

# --- Configuration ---
PORT = 22000
VIBE_TOKEN = "VIBE_777_SECURE"
BRIDGE_NAMESPACE = "VIBE_BRIDGE_PRO"
BASE_PATH = "/home/bamn/BlenderVibeBridge"
INBOX_PATH = os.path.join(BASE_PATH, "vibe_queue/inbox")
OUTBOX_PATH = os.path.join(BASE_PATH, "vibe_queue/outbox")

def get_ctx():
    if BRIDGE_NAMESPACE not in bpy.app.driver_namespace:
        bpy.app.driver_namespace[BRIDGE_NAMESPACE] = {}
    ctx = bpy.app.driver_namespace[BRIDGE_NAMESPACE]
    defaults = {"generation": 0, "state": "STOPPED", "server": None, "queue": queue.Queue(), "session_id": None}
    for k, v in defaults.items():
        if k not in ctx: ctx[k] = v
    return ctx

# --- Logging ---
LOG_FILE = os.path.join(BASE_PATH, "bridge.log")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("VibeBridge")

def vibe_log(msg):
    logger.info(msg)

class ContextGuard:
    """OS-Level Selection & Mode Protection."""
    def __enter__(self):
        self.active_name = bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None
        self.selected_names = [o.name for o in bpy.context.selected_objects]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for name in self.selected_names:
            obj = bpy.data.objects.get(name)
            if obj: obj.select_set(True)
        if self.active_name:
            obj = bpy.data.objects.get(self.active_name)
            if obj: bpy.context.view_layer.objects.active = obj
        vibe_log("ContextGuard: Restored.")

class ModelingKernel:
    @staticmethod
    def validate_mutation(data):
        """Hardware Level DoS Protection"""
        cmd = data.get("type")
        if cmd == "modifier_op" and data.get("mod_type") == "SUBSURF":
            if data.get("prop") in ["levels", "render_levels"]:
                try:
                    if int(data.get("value", 0)) > 3: return False, "Subdiv capped at 3"
                except: pass
        if cmd == "modifier_op" and data.get("mod_type") == "ARRAY":
            if data.get("prop") == "count":
                try:
                    if int(data.get("value", 0)) > 50: return False, "Array capped at 50"
                except: pass
        return True, None

    @staticmethod
    def tag_object(obj):
        ctx = get_ctx()
        obj["vibe_session_id"] = ctx.get("session_id", "UNKNOWN")

    @staticmethod
    def execute(data):
        cmd = data.get("type")
        vibe_log(f"ACTION: {cmd}")
        
        safe, reason = ModelingKernel.validate_mutation(data)
        if not safe:
            vibe_log(f"BLOCKED: {reason}")
            return

        target_name = data.get("name") or data.get("obj_name") or data.get("target")
        if target_name:
            obj = bpy.data.objects.get(target_name) or bpy.data.materials.get(target_name)
            if obj and obj.library:
                vibe_log(f"BLOCK: {target_name} is LINKED.")
                return

        if cmd == "run_op" and data.get("op") == "object.delete":
            for obj in bpy.context.selected_objects:
                if "vibe_session_id" not in obj or obj["vibe_session_id"] != get_ctx()["session_id"]:
                    vibe_log(f"BLOCK: Deletion of {obj.name} rejected.")
                    return

        win = bpy.context.window_manager.windows[0]
        area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'), None)
        region = next((r for r in area.regions if r.type == 'WINDOW'), None) if area else None
        override = bpy.context.copy()
        override['window'], override['screen'], override['area'], override['region'] = win, win.screen, area, region

        with ContextGuard():
            with bpy.context.temp_override(**override):
                try:
                    if cmd == "run_op":
                        op_path = data.get("op").split(".")
                        func = bpy.ops
                        for part in op_path: func = getattr(func, part)
                        obs_before = set(bpy.data.objects.keys())
                        func()
                        for name in (set(bpy.data.objects.keys()) - obs_before): ModelingKernel.tag_object(bpy.data.objects[name])

                    elif cmd == "exec_script":
                        # --- SANDBOXING LOGIC ---
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
                                    vibe_log("Sandbox Success")
                                except Exception as e: vibe_log(f"Sandbox Fail: {e}")
                                finally: bpy.data.objects.remove(sandbox_obj, do_unlink=True)
                                return

                        bpy.ops.ed.undo_push(message=f"Vibe: {data.get('description', 'Script')}")
                        try:
                            exec(data.get("script"), {"bpy": bpy, "mathutils": mathutils, "vibe_log": vibe_log, "math": math})
                        except Exception as e:
                            bpy.ops.ed.undo()
                            raise e

                    elif cmd == "render_op":
                        path = os.path.join(BASE_PATH, "vibe_capture.png")
                        bpy.context.scene.render.filepath = path
                        bpy.ops.render.opengl(write_still=True)

                    elif cmd == "cleanup_op":
                        action = data.get("action")
                        if action == "reset_material":
                            mat = bpy.data.materials.get(data.get("target"))
                            if mat:
                                mat.use_nodes = True; mat.node_tree.nodes.clear()
                                out = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
                                bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
                                mat.node_tree.links.new(bsdf.outputs[0], out.inputs[0])
                        elif action == "scan_nan":
                            corrupt = [o.name for o in bpy.data.objects if any(math.isnan(v) or math.isinf(v) for v in list(o.location) + list(o.scale))]
                            vibe_log(f"NaN Check: {corrupt if corrupt else 'CLEAN'}")
                        elif action == "purge_orphans":
                            for _ in range(3):
                                if bpy.ops.outliner.orphans_purge.poll(): bpy.ops.outliner.orphans_purge(do_local_ids=True, do_recursive=True)
                        elif action == "material_preview_sandbox":
                            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(2, 0, 1))
                            proxy = bpy.context.active_object
                            proxy.name = "_MAT_PREVIEW_PROXY"; ModelingKernel.tag_object(proxy)

                    elif cmd == "audit_op":
                        action = data.get("action")
                        if action == "check_deps":
                            missing = [bpy.path.abspath(img.filepath) for img in bpy.data.images if img.filepath and not img.packed_file and not os.path.exists(bpy.path.abspath(img.filepath))]
                            vibe_log(f"DEPS: {missing if missing else 'OK'}")
                        elif action == "validate_export":
                            violations = [o.name for o in bpy.data.objects if o.type == 'MESH' and (any(abs(s-1.0)>0.001 for s in o.scale) or any(len(p.vertices)>4 for p in o.data.polygons))]
                            vibe_log(f"EXPORT CONTRACT: {violations if violations else 'PASS'}")
                        elif action == "audit_rig":
                            corrupt = [f"{arm.name}:{bone.name}" for arm in bpy.data.objects if arm.type == 'ARMATURE' for bone in arm.pose.bones if any(math.isnan(v) or math.isinf(v) for v in list(bone.location)+list(bone.scale))]
                            vibe_log(f"RIG AUDIT: {corrupt if corrupt else 'CLEAN'}")
                        elif action == "audit_shape_keys":
                            fails = [o.name for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys and any(len(k.data)!=len(o.data.shape_keys.reference_key.data) for k in o.data.shape_keys.key_blocks)]
                            vibe_log(f"SHAPE KEY AUDIT: {fails if fails else 'CLEAN'}")
                        elif action == "audit_weights":
                            unweighted = [o.name for o in bpy.data.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers) and any(not v.groups for v in o.data.vertices)]
                            vibe_log(f"WEIGHT AUDIT: {unweighted if unweighted else 'CLEAN'}")
                        elif action == "vertex_hash":
                            obj = bpy.data.objects.get(data.get("target"))
                            if obj and obj.type == 'MESH':
                                vibe_log(f"VERTEX HASH [{obj.name}]: {hash(tuple([tuple(v.co) for v in obj.data.vertices]))}")

                    elif cmd == "system_op":
                        action = data.get("action")
                        if action == "undo": bpy.ops.ed.undo()
                        elif action == "panic_downgrade":
                            for area in bpy.context.screen.areas:
                                if area.type == 'VIEW_3D': area.spaces.active.shading.type = 'SOLID'; area.spaces.active.overlay.show_overlays = False
                            for obj in bpy.data.objects:
                                if obj.type == 'MESH':
                                    for mod in obj.modifiers:
                                        if mod.type in ['SUBSURF', 'ARRAY', 'BOOLEAN']: mod.show_viewport = False
                        elif action == "checkpoint":
                            path = os.path.join(BASE_PATH, "checkpoints", data.get("name", "safe") + ".blend")
                            os.makedirs(os.path.dirname(path), exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
                        elif action == "reload": vibe_log("RELOAD_SIGNAL")

                except Exception as e: vibe_log(f"Kernel Error: {e}")

def poll_airlock():
    if not os.path.exists(INBOX_PATH): return
    files = [f for f in os.listdir(INBOX_PATH) if f.endswith(".json")]
    if not files: return
    files.sort()
    for f in files:
        path = os.path.join(INBOX_PATH, f)
        try:
            with open(path, "r") as file: data = json.load(file)
            ModelingKernel.execute(data)
            res_path = os.path.join(OUTBOX_PATH, "res_" + f)
            with open(res_path, "w") as res_file: json.dump({"status": "SUCCESS", "id": data.get("id")}, res_file)
        except Exception as e: vibe_log(f"Airlock Error: {e}")
        finally:
            if os.path.exists(path): os.remove(path)

def main_loop():
    ctx = get_ctx()
    if ctx["state"] != "RUNNING": return None
    try:
        hb_path = os.path.join(BASE_PATH, "metadata/vibe_health.json")
        os.makedirs(os.path.dirname(hb_path), exist_ok=True)
        with open(hb_path, "w") as f: json.dump({"status": "READY", "timestamp": time.time(), "session": ctx["session_id"], "queue_size": ctx["queue"].qsize()}, f)
    except: pass
    poll_airlock()
    while not ctx["queue"].empty():
        ModelingKernel.execute(ctx["queue"].get())
        ctx["queue"].task_done()
    return 0.1

class VibeHandler(http.server.SimpleHTTPRequestHandler):
    def check_auth(self): return self.headers.get('X-Vibe-Token') == VIBE_TOKEN
    def do_GET(self):
        if self.path == "/monitor":
            self.send_response(200); self.send_header('Content-type', 'text/html'); self.end_headers()
            self.wfile.write(b"<html><head><meta http-equiv='refresh' content='2'></head><body style='background:#111;text-align:center'><img src='/image' style='max-width:90%'></body></html>")
        elif self.path == "/image":
            path = os.path.join(BASE_PATH, "vibe_capture.png")
            if os.path.exists(path):
                self.send_response(200); self.send_header('Content-type', 'image/png'); self.end_headers()
                with open(path, "rb") as f: self.wfile.write(f.read())
            else: self.send_response(404); self.end_headers()
        elif self.path == "/status" and self.check_auth():
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            telemetry = [{"name": o.name, "polys": len(o.data.polygons) if o.type=='MESH' else 0} for o in bpy.data.objects]
            self.wfile.write(json.dumps({"online": True, "telemetry": telemetry}).encode())
        elif self.path == "/restart" and self.check_auth():
            self.send_response(202); self.end_headers(); threading.Thread(target=bootstrap).start()
        else: self.send_response(403); self.end_headers()
    def do_POST(self):
        if not self.check_auth(): self.send_response(403); self.end_headers(); return
        try:
            data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
            get_ctx()["queue"].put(data)
            self.send_response(202); self.end_headers()
        except: self.send_response(400); self.end_headers()

def bootstrap():
    ctx = get_ctx()
    ctx["generation"] += 1; ctx["session_id"] = str(uuid.uuid4())
    try:
        if not bpy.app.timers.is_registered(main_loop): bpy.app.timers.register(main_loop)
        if not ctx["server"]:
            socketserver.TCPServer.allow_reuse_address = True
            ctx["server"] = socketserver.TCPServer(("127.0.0.1", PORT), VibeHandler)
            threading.Thread(target=ctx["server"].serve_forever, daemon=True).start()
        ctx["state"] = "RUNNING"; print(f"VIBE KERNEL ONLINE (GEN {ctx['generation']})")
    except Exception as e: print(f"BOOT FAIL: {e}")

# --- Addon Registration ---
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
        layout = self.layout; ctx = get_ctx()
        layout.label(text=f"Status: {ctx['state']}")
        layout.label(text=f"Generation: {ctx['generation']}")
        layout.operator("vibe.start_bridge")

def register():
    bpy.utils.register_class(VIBE_OT_StartBridge)
    bpy.utils.register_class(VIBE_PT_Panel)
    bootstrap()

def unregister():
    bpy.utils.unregister_class(VIBE_OT_StartBridge)
    bpy.utils.unregister_class(VIBE_PT_Panel)
    ctx = get_ctx(); 
    if ctx["server"]: ctx["server"].shutdown()

if __name__ == "__main__": register()