import http.server
import socketserver
import json
import threading
import time
import os
import hashlib
from ..logging.logger import vibe_log

PORT = 22000
SESSION_ID = str(int(time.time()))

# Global state for thread-safe reading (Updated by main thread poll_wrapper)
SCENE_SNAPSHOT = {
    "hash": "INIT",
    "objects": [],
    "object_count": 0,
    "meshes": 0,
    "armatures": 0,
    "materials": 0,
    "timestamp": 0,
    "engine_time_ms": 0,
    "monotonic_tick": 0,
    "filepath": "",
    "is_dirty": False,
    "mode": "UNKNOWN",
    "active_object": None,
    "errors": [],
    "modal_active": False
}

class VibeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence standard HTTP logging to keep console clean
        pass

    def do_GET(self):
        routes = {
            "/blender/heartbeat": self.get_heartbeat,
            "/blender/file_state": self.get_file_state,
            "/blender/scene_state": self.get_scene_state,
            "/blender/context_state": self.get_context_state,
            "/blender/datablock_state": self.get_datablock_state,
            "/blender/error_state": self.get_error_state,
            "/status": self.get_status # Legacy support
        }
        
        handler = routes.get(self.path)
        if handler:
            self.send_json_response(handler())
        else:
            self.send_error(404)

    def send_json_response(self, data):
        # Inject schema version into every response
        data["schema_version"] = "vibe.blender.v1.5.0"
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    # --- INVARIANT HANDLERS ---

    def get_heartbeat(self):
        return {
            "blender_pid": os.getpid(),
            "responsive": True,
            "modal_operator_active": SCENE_SNAPSHOT["modal_active"],
            "session_hash": SESSION_ID,
            "engine_time_ms": SCENE_SNAPSHOT["engine_time_ms"],
            "monotonic_tick": SCENE_SNAPSHOT["monotonic_tick"],
            "timestamp": time.time()
        }

    def get_file_state(self):
        return {
            "filepath": SCENE_SNAPSHOT["filepath"],
            "is_dirty": SCENE_SNAPSHOT["is_dirty"],
            "is_saved": bool(SCENE_SNAPSHOT["filepath"]),
            "autosave_active": True
        }

    def get_scene_state(self):
        return {
            "scene_hash": SCENE_SNAPSHOT["hash"],
            "object_count": SCENE_SNAPSHOT["object_count"],
            "objects": SCENE_SNAPSHOT["objects"][:10] # Limit for performance
        }

    def get_context_state(self):
        return {
            "active_object": SCENE_SNAPSHOT["active_object"],
            "object_mode": SCENE_SNAPSHOT["mode"]
        }

    def get_datablock_state(self):
        return {
            "meshes": SCENE_SNAPSHOT["meshes"],
            "armatures": SCENE_SNAPSHOT["armatures"],
            "materials": SCENE_SNAPSHOT["materials"],
            "datablock_hash": SCENE_SNAPSHOT["hash"]
        }

    def get_error_state(self):
        return {
            "errors": SCENE_SNAPSHOT["errors"],
            "error_hash": hashlib.md5(str(SCENE_SNAPSHOT["errors"]).encode()).hexdigest()
        }

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        # All responses include schema version for Version Drift Invariance
        schema_info = {"schema_version": "vibe.blender.v1.5.0"}
        
        if self.path == "/query":
            # For now, return the latest cached hash
            response = {
                "hash": SCENE_SNAPSHOT["hash"],
                "status": "SUCCESS",
                "monotonic_tick": SCENE_SNAPSHOT["monotonic_tick"]
            }
            response.update(schema_info)
            self.send_json_response(response)
        else:
            self.send_error(404)

    def get_status(self):
        return {
            "session": SESSION_ID,
            "objects": SCENE_SNAPSHOT["object_count"],
            "snapshot_age": time.time() - SCENE_SNAPSHOT["timestamp"],
            "schema_version": "vibe.blender.v1.5.0"
        }    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("127.0.0.1", PORT), VibeHandler) as server:
            vibe_log(f"INVARIANCE SERVER STARTED ON PORT {PORT}")
            server.serve_forever()
    except Exception as e:
        vibe_log(f"SERVER CRITICAL FAILURE: {e}")

def run_server_thread():
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()
    return thread

def update_snapshot(bpy):
    """Refreshes the deterministic snapshot. Called from MAIN THREAD."""
    global SCENE_SNAPSHOT
    
    h = hashlib.sha256()
    obj_list = []
    
    # Monotonic progression
    current_tick = SCENE_SNAPSHOT.get("monotonic_tick", 0) + 1
    engine_time = int(time.perf_counter() * 1000)
    
    # Deterministic sort
    objs = sorted(bpy.data.objects, key=lambda o: o.name)
    for obj in objs:
        uuid = obj.get("uuid", "NO_UUID")
        obj_info = {"name": obj.name, "type": obj.type, "uuid": uuid}
        obj_list.append(obj_info)
        
        # State Hashing
        h.update(f"{obj.name}:{uuid}:{obj.location}".encode())

    SCENE_SNAPSHOT.update({
        "hash": h.hexdigest(),
        "objects": obj_list,
        "object_count": len(bpy.data.objects),
        "meshes": len(bpy.data.meshes),
        "armatures": len(bpy.data.armatures),
        "materials": len(bpy.data.materials),
        "filepath": bpy.data.filepath,
        "is_dirty": bpy.data.is_dirty,
        "mode": str(bpy.context.mode) if bpy.context else "UNKNOWN",
        "active_object": bpy.context.active_object.name if bpy.context and bpy.context.active_object else None,
        "timestamp": time.time(),
        "engine_time_ms": engine_time,
        "monotonic_tick": current_tick
    })
