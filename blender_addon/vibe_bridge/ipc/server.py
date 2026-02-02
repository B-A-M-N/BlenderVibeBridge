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

                "/blender/addon_state": self.get_addon_state,

                "/blender/integrity_test": self.get_integrity_test,

                "/status": self.get_status # Legacy support

            }

            

            # Handle query parameters

            path_base = self.path.split('?')[0]

            handler = routes.get(path_base)

            

            if handler:

                self.send_json_response(handler())

            else:

                self.send_error(404)

    

        def send_json_response(self, data):

            # Inject schema version into every response

            if isinstance(data, dict):

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

    

        def get_addon_state(self):

            import addon_utils

            from urllib.parse import urlparse, parse_qs

            params = parse_qs(urlparse(self.path).query)

            name = params.get('name', [None])[0]

            if not name: return {"error": "NAME_REQUIRED"}

            enabled = any(a.bl_info.get('name') == name or a.__name__ == name for a in addon_utils.modules() if addon_utils.check(a.__name__)[0])

            return {"addon": name, "enabled": enabled}

    

        def get_integrity_test(self):

            import bpy

            from urllib.parse import urlparse, parse_qs

            params = parse_qs(urlparse(self.path).query)

            uuid = params.get('uuid', [None])[0]

            obj = next((o for o in bpy.data.objects if o.get("vibe_uuid") == uuid), None)

            if not obj: return {"status": "LOST"}

            return {"status": "STABLE", "location": list(obj.location)}

    

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

                "hash": SCENE_SNAPSHOT["hash"],

                "objects": SCENE_SNAPSHOT["objects"],

                "dirty_objects": SCENE_SNAPSHOT["dirty_objects"],

                "overlaps": SCENE_SNAPSHOT["overlaps"],

                "blender_version": SCENE_SNAPSHOT.get("blender_version", []),

                "snapshot_age": time.time() - SCENE_SNAPSHOT["timestamp"],

                "schema_version": "vibe.blender.v1.5.0"

            }

        socketserver.TCPServer.allow_reuse_address = True
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

import mathutils

LAST_STATE_HASH = {}

def get_overlaps(objs):
    """Calculates bounding box overlaps for metadata enrichment."""
    overlaps = []
    for i, obj_a in enumerate(objs):
        if obj_a.type != 'MESH': continue
        bbox_a = [obj_a.matrix_world @ mathutils.Vector(v) for v in obj_a.bound_box]
        min_a = mathutils.Vector((min(v[0] for v in bbox_a), min(v[1] for v in bbox_a), min(v[2] for v in bbox_a)))
        max_a = mathutils.Vector((max(v[0] for v in bbox_a), max(v[1] for v in bbox_a), max(v[2] for v in bbox_a)))
        
        for obj_b in objs[i+1:]:
            if obj_b.type != 'MESH': continue
            bbox_b = [obj_b.matrix_world @ mathutils.Vector(v) for v in obj_b.bound_box]
            min_b = mathutils.Vector((min(v[0] for v in bbox_b), min(v[1] for v in bbox_b), min(v[2] for v in bbox_b)))
            max_b = mathutils.Vector((max(v[0] for v in bbox_b), max(v[1] for v in bbox_b), max(v[2] for v in bbox_b)))
            
            # Simple AABB check
            if (min_a.x <= max_b.x and max_a.x >= min_b.x and
                min_a.y <= max_b.y and max_a.y >= min_b.y and
                min_a.z <= max_b.z and max_a.z >= min_b.z):
                overlaps.append((obj_a.name, obj_b.name))
    return overlaps

def update_snapshot(bpy):
    global SCENE_SNAPSHOT, LAST_STATE_HASH
    obj_list = []
    diff_list = []
    h = hashlib.sha256()
    
    # Deterministic sort
    objs = sorted(bpy.data.objects, key=lambda o: o.name)
    for obj in objs:
        v_uuid = obj.get("vibe_uuid", "NO_UUID")
        # Generate hash for this specific object's state
        obj_hash = hashlib.sha256(f"{obj.name}:{v_uuid}:{obj.location}:{obj.rotation_euler}:{obj.scale}".encode()).hexdigest()
        
        obj_info = {
            "name": obj.name, 
            "type": obj.type, 
            "uuid": v_uuid, 
            "loc": list(obj.location),
            "rot": list(obj.rotation_euler),
            "scale": list(obj.scale)
        }
        
        # Differential logic: Only add to diff_list if state changed
        if LAST_STATE_HASH.get(v_uuid) != obj_hash:
            diff_list.append(obj_info)
            LAST_STATE_HASH[v_uuid] = obj_hash
            
        obj_list.append(obj_info)
        h.update(obj_hash.encode())

    SCENE_SNAPSHOT.update({
        "hash": h.hexdigest(),
        "objects": obj_list,
        "dirty_objects": diff_list,
        "overlaps": get_overlaps(objs),
        "blender_version": list(bpy.app.version),
        "timestamp": time.time()
    })
