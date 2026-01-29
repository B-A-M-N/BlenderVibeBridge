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

# --- Configuration ---
PORT = 22000
VIBE_TOKEN = "VIBE_777_SECURE"
BRIDGE_NAMESPACE = "VIBE_BRIDGE_PRO"

def get_ctx():
    if BRIDGE_NAMESPACE not in bpy.app.driver_namespace:
        bpy.app.driver_namespace[BRIDGE_NAMESPACE] = {}
    ctx = bpy.app.driver_namespace[BRIDGE_NAMESPACE]
    defaults = {"generation": 0, "state": "STOPPED", "server": None, "queue": queue.Queue(), "session_id": None}
    for k, v in defaults.items():
        if k not in ctx: ctx[k] = v
    return ctx

# --- Logging ---
LOG_FILE = os.path.join(os.path.dirname(__file__), "../../bridge.log")
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

class ModelingKernel:
    @staticmethod
    def validate_mutation(data):
        """Hardware Level DoS Protection & Safety Railings"""
        cmd = data.get("type")
        
        # 1. Subdivision Railings
        if cmd == "modifier_op" and data.get("mod_type") == "SUBSURF":
            if data.get("prop") in ["levels", "render_levels"]:
                try:
                    val = int(data.get("value", 0))
                    if val > 3:
                        vibe_log(f"BLOCK: Subdiv levels > 3 ({val}) rejected.")
                        return False, "Hardware Railing: Subdiv levels capped at 3."
                except: pass

        # 2. Array Railings
        if cmd == "modifier_op" and data.get("mod_type") == "ARRAY":
            if data.get("prop") == "count":
                try:
                    val = int(data.get("value", 0))
                    if val > 50:
                        vibe_log(f"BLOCK: Array count > 50 ({val}) rejected.")
                        return False, "Hardware Railing: Array count capped at 50."
                except: pass

        # 3. Light Energy Guard
        if cmd == "lighting_op":
            try:
                energy = float(data.get("energy", 0))
                if energy > 10000:
                    vibe_log(f"BLOCK: Light energy > 10k ({energy}) rejected.")
                    return False, "Hardware Railing: Light energy capped at 10,000."
            except: pass

        return True, None

    @staticmethod
    def handle_macro(intent):
        """Strategic Intent Recipes"""
        vibe_log(f"Executing Macro: {intent}")
        
        if intent == "RESTORE_AVATAR_COLORS_RED":
            # Example implementation of a macro
            for mat in bpy.data.materials:
                if any(k in mat.name.lower() for k in ["metal", "spike", "chain"]):
                    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                    if bsdf:
                        bsdf.inputs[0].default_value = (0.3, 0.0, 0.0, 1.0) # Blood Red
            return True
            
        elif intent == "BLOCKOUT_HUMANOID":
            # Logic for blocking out
            bpy.ops.mesh.primitive_cube_add(size=1.8, location=(0,0,0.9))
            return True

        vibe_log(f"Macro Unknown: {intent}")
        return False

    @staticmethod
    def execute(data):
        cmd = data.get("type")
        vibe_log(f"ACTION_PAYLOAD: {json.dumps(data)}")
        
        # Hardware Railings
        safe, reason = ModelingKernel.validate_mutation(data)
        if not safe:
            vibe_log(f"EXECUTION_BLOCKED: {reason}")
            return

        target_name = data.get("name") or data.get("obj_name")
        obj = bpy.data.objects.get(target_name) if target_name else bpy.context.active_object
        
        # Context Override
        win = bpy.context.window_manager.windows[0]
        area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'), None)
        region = next((r for r in area.regions if r.type == 'WINDOW'), None) if area else None
        override = {'window': win, 'screen': win.screen, 'area': area, 'region': region}

        with bpy.context.temp_override(**override):
            try:
                if cmd == "macro_op":
                    ModelingKernel.handle_macro(data.get("intent"))

                elif cmd == "transform" and obj:
                    val = ast.literal_eval(data.get("value"))
                    op = data.get("op")
                    if op == "translate": obj.location = val
                    elif op == "rotate": obj.rotation_euler = val
                    elif op == "scale": obj.scale = val
                
                elif cmd == "run_op":
                    op_path = data.get("op").split(".")
                    func = bpy.ops
                    for part in op_path: func = getattr(func, part)
                    func()

                elif cmd == "modifier_op" and obj:
                    action, mod_type, mod_name = data.get("action"), data.get("mod_type"), data.get("mod_name")
                    if action == "add":
                        obj.modifiers.new(name=mod_name, type=mod_type)
                    elif action == "remove":
                        m = obj.modifiers.get(mod_name)
                        if m: obj.modifiers.remove(m)
                    
                    if "prop" in data and "value" in data:
                        m = obj.modifiers.get(mod_name)
                        if m:
                            try:
                                setattr(m, data["prop"], ast.literal_eval(data["value"]))
                            except:
                                setattr(m, data["prop"], data["value"])

                elif cmd == "exec_script":
                    # Security Note: This is already audited by the MCP server before reaching here
                    exec(data.get("script"), {"bpy": bpy, "mathutils": mathutils, "vibe_log": vibe_log, "math": __import__("math")})
                
                elif cmd == "render_op":
                    path = "/home/bamn/BlenderVibeBridge/vibe_capture.png"
                    bpy.context.scene.render.filepath = path
                    bpy.ops.render.opengl(write_still=True)
                    vibe_log(f"Rendered viewport to {path}")

                elif cmd == "system_op" and data.get("action") == "reload":
                    vibe_log("RELOAD_SIGNAL_RECEIVED")
                    # Actual reload happens in bootstrap call

            except Exception as e: vibe_log(f"Modeling Error: {e}")

def main_loop():
    ctx = get_ctx()
    if ctx["state"] != "RUNNING" or main_loop.session != ctx["session_id"]: return None
    while not ctx["queue"].empty():
        ModelingKernel.execute(ctx["queue"].get())
        ctx["queue"].task_done()
    return 0.1

class VibeHandler(http.server.SimpleHTTPRequestHandler):
    def check_auth(self): return self.headers.get('X-Vibe-Token') == VIBE_TOKEN
    def log_request(self, *args): pass
    def do_GET(self):
        ctx = get_ctx()
        if not self.check_auth(): self.send_response(403); self.end_headers(); return
        
        if self.path == "/status":
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            telemetry = []
            for o in bpy.data.objects:
                if o.type == 'MESH':
                    telemetry.append({
                        "name": o.name,
                        "polys": len(o.data.polygons),
                        "mats": len(o.material_slots),
                        "visible": not o.hide_viewport
                    })
            self.wfile.write(json.dumps({"online": True, "gen": ctx["generation"], "telemetry": telemetry}).encode())
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        ctx = get_ctx()
        if not self.check_auth() or ctx["state"] != "RUNNING": self.send_response(403); self.end_headers(); return
        try:
            data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
            ctx["queue"].put(data)
            self.send_response(202); self.end_headers()
        except: self.send_response(400); self.end_headers()

def bootstrap():
    ctx = get_ctx()
    ctx["state"] = "STOPPED"
    if ctx["server"]:
        try: ctx["server"].shutdown(); ctx["server"].server_close()
        except: pass
    time.sleep(0.2)
    ctx["generation"] += 1
    ctx["session_id"] = str(uuid.uuid4())
    main_loop.session = ctx["session_id"]
    try:
        socketserver.TCPServer.allow_reuse_address = True
        ctx["server"] = socketserver.TCPServer(("0.0.0.0", PORT), VibeHandler)
        threading.Thread(target=ctx["server"].serve_forever, daemon=True).start()
        ctx["state"] = "RUNNING"
        if not bpy.app.timers.is_registered(main_loop):
            bpy.app.timers.register(main_loop)
        print(f"--- VIBE BRIDGE ADDON ONLINE (GEN {ctx['generation']}) ---")
    except Exception as e: print(f"Boot Fail: {e}")

# --- Addon Registration ---

class VIBE_OT_StartBridge(bpy.types.Operator):
    bl_idname = "vibe.start_bridge"
    bl_label = "Start Vibe Bridge"
    def execute(self, context):
        bootstrap()
        return {'FINISHED'}

class VIBE_PT_Panel(bpy.types.Panel):
    bl_label = "Vibe Bridge Control"
    bl_idname = "VIBE_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Vibe Bridge'

    def draw(self, context):
        layout = self.layout
        ctx = get_ctx()
        layout.label(text=f"Status: {ctx['state']}")
        layout.label(text=f"Generation: {ctx['generation']}")
        layout.operator("vibe.start_bridge")

def register():
    bpy.utils.register_class(VIBE_OT_StartBridge)
    bpy.utils.register_class(VIBE_PT_Panel)
    # Start automatically if in headless mode or standard?
    # For now, we rely on the button or manual script call
    bootstrap()

def unregister():
    bpy.utils.unregister_class(VIBE_OT_StartBridge)
    bpy.utils.unregister_class(VIBE_PT_Panel)
    ctx = get_ctx()
    if ctx["server"]:
        ctx["server"].shutdown()
        ctx["server"].server_close()

if __name__ == "__main__":
    register()
