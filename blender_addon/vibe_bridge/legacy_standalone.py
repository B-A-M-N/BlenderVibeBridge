import bpy, threading, queue, http.server, socketserver, ast, uuid, os, sys, time, mathutils, re, json, logging
from datetime import datetime

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

# --- Logging Configuration ---
LOG_FILE = "/home/bamn/BlenderVibeBridge/bridge.log"
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
    def execute(data):
        cmd = data.get("type")
        vibe_log(f"ACTION_PAYLOAD: {json.dumps(data)}")
        
        target_name = data.get("name") or data.get("obj_name")
        obj = bpy.data.objects.get(target_name) if target_name else bpy.context.active_object
        
        win = bpy.context.window_manager.windows[0]
        area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'), None)
        region = next((r for r in area.regions if r.type == 'WINDOW'), None) if area else None
        override = {'window': win, 'screen': win.screen, 'area': area, 'region': region}

        with bpy.context.temp_override(**override):
            try:
                if cmd == "transform" and obj:
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
                        if m: setattr(m, data["prop"], ast.literal_eval(data["value"]))

                elif cmd == "exec_script":
                    exec(data.get("script"), {"bpy": bpy, "mathutils": mathutils, "vibe_log": vibe_log})
                
                elif cmd == "render_op":
                    bpy.context.scene.render.filepath = "/home/bamn/BlenderVibeBridge/vibe_capture.png"
                    bpy.ops.render.opengl(write_still=True)

            except Exception as e: vibe_log(f"Modeling Error: {e}")

def main_loop():
    ctx = get_ctx()
    if ctx["state"] != "RUNNING" or vibe_timer_loop.session != ctx["session_id"]: return None
    while not ctx["queue"].empty():
        ModelingKernel.execute(ctx["queue"].get())
        ctx["queue"].task_done()
    return 0.1

vibe_timer_loop = main_loop # Alias for compatibility

class VibeHandler(http.server.SimpleHTTPRequestHandler):
    def check_auth(self): return self.headers.get('X-Vibe-Token') == VIBE_TOKEN
    def log_request(self, *args): pass
    def do_GET(self):
        ctx = get_ctx()
        if not self.check_auth(): self.send_response(403); self.end_headers(); return
        
        self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
        
        # Build Telemetry Report
        telemetry = []
        for o in bpy.data.objects:
            if o.type == 'MESH':
                telemetry.append({
                    "name": o.name,
                    "polys": len(o.data.polygons),
                    "mats": len(o.material_slots),
                    "visible": not o.hide_viewport
                })
        
        self.wfile.write(json.dumps({
            "online": True, 
            "gen": ctx["generation"], 
            "telemetry": telemetry
        }).encode())

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
    vibe_timer_loop.session = ctx["session_id"]
    try:
        socketserver.TCPServer.allow_reuse_address = True
        ctx["server"] = socketserver.TCPServer(("0.0.0.0", PORT), VibeHandler)
        threading.Thread(target=ctx["server"].serve_forever, daemon=True).start()
        ctx["state"] = "RUNNING"
        bpy.app.timers.register(vibe_timer_loop)
        print(f"--- VIBE OPTIMIZATION KERNEL V12 (UNBOUND) ONLINE ---")
    except Exception as e: print(f"Boot Fail: {e}")

if __name__ == "__main__": bootstrap()
