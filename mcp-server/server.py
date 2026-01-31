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

import sys
import requests
import base64
import os
import time
import datetime
import json
import logging
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent
from security_gate import SecurityGate

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [MCP] %(message)s",
    handlers=[
        logging.FileHandler("/home/bamn/BlenderVibeBridge/server.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("MCPServer")

# --- CORE SERVER INITIALIZATION ---
mcp = FastMCP("BlenderVibeBridge")
BLENDER_API_URL = "http://127.0.0.1:22000"
VIBE_TOKEN = "VIBE_777_SECURE"
SESSION_ID = None
AUDIT_LOG_PATH = "/home/bamn/BlenderVibeBridge/logs/vibe_audit.jsonl"
ENTROPY_BUDGET = 100
ENTROPY_USED = 0

# Ensure logs directory exists
os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)

class AuditLogger:
    _last_hash = "ROOT"

    @staticmethod
    def log_mutation(method, path, data, response):
        global ENTROPY_USED
        ENTROPY_USED += 1
        
        # Calculate Chained Hash
        import hashlib
        h = hashlib.sha256()
        h.update(f"{AuditLogger._last_hash}{method}{path}{json.dumps(data)}".encode())
        current_hash = h.hexdigest()
        
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "method": method,
            "path": path,
            "request_data": data,
            "response": response,
            "capability": data.get("capability", "UNKNOWN") if data else "UNKNOWN",
            "entropy_used": ENTROPY_USED,
            "prev_hash": AuditLogger._last_hash,
            "entry_hash": current_hash
        }
        
        AuditLogger._last_hash = current_hash
        
        with open(AUDIT_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")

class SecurityMonitor:
    def __init__(self, threshold=3):
        self.violations = 0
        self.threshold = threshold
        self.panic_mode = False

    def report_violation(self, reason):
        self.violations += 1
        sys.stderr.write(f"\n[!] SECURITY VIOLATION ({self.violations}/{self.threshold}): {reason}\n")
        if self.violations >= self.threshold:
            self.panic_mode = True
            sys.stderr.write("\n[!!!] PANIC MODE ACTIVATED: BRIDGE IS NOW READ-ONLY.\n")

    def is_safe(self, is_mutation):
        if self.panic_mode and is_mutation:
            return False, "PANIC MODE: All mutations blocked."
        return True, None

monitor = SecurityMonitor(threshold=3)

class RateLimiter:
    def __init__(self, max_per_second=5):
        self.max_per_second = max_per_second
        self.requests = []

    def check(self):
        now = time.time()
        self.requests = [r for r in self.requests if now - r < 1.0]
        if len(self.requests) >= self.max_per_second: return False
        self.requests.append(now)
        return True

limiter = RateLimiter()

INBOX_PATH = "/home/bamn/BlenderVibeBridge/vibe_queue/inbox"
OUTBOX_PATH = "/home/bamn/BlenderVibeBridge/vibe_queue/outbox"

def blender_request(method, path, data=None, is_mutation=False):
    global SESSION_ID
    
    if not limiter.check():
        return {"error": "Rate limit exceeded. Max 5 req/s."}

    # Log the intent
    if is_mutation:
        logger.info(f"MUTATION_REQUEST: {method} {path} | Data: {json.dumps(data)}")
    else:
        logger.info(f"READ_REQUEST: {method} {path}")

    safe, reason = monitor.is_safe(is_mutation)
    if not safe: 
        logger.warning(f"BLOCKED: {reason}")
        return {"error": reason}

    # Security Audit for Scripts
    if data and data.get("type") == "exec_script":
        script = data.get("script")
        if script:
            violations = SecurityGate.check_python(script)
            if violations:
                logger.warning(f"SECURITY_VIOLATION blocked script: {violations}")
                monitor.report_violation(f"Script Violation: {violations[0]}")
                return {"error": f"Security Violation: {violations[0]}"}

    # --- HYBRID DISPATCH ---
    if is_mutation:
        import uuid
        cmd_id = str(uuid.uuid4())
        payload = data or {}
        payload["id"] = cmd_id
        if SESSION_ID: payload["vibe_session_id"] = SESSION_ID
        
        # 1. Write to Inbox
        os.makedirs(INBOX_PATH, exist_ok=True)
        inbox_file = os.path.join(INBOX_PATH, f"{cmd_id}.json")
        with open(inbox_file, "w") as f:
            json.dump(payload, f)
            
        # 2. Poll Outbox
        os.makedirs(OUTBOX_PATH, exist_ok=True)
        outbox_file = os.path.join(OUTBOX_PATH, f"res_{cmd_id}.json")
        timeout = 60
        start_time = time.time()
        retries = 0
        
        while time.time() - start_time < timeout:
            if os.path.exists(outbox_file):
                try:
                    with open(outbox_file, "r") as f:
                        resp_json = json.load(f)
                    os.remove(outbox_file)
                    AuditLogger.log_mutation(method, path, data, resp_json)
                    return resp_json
                except Exception as e:
                    retries += 1
                    if retries > 5:
                        return {"error": f"Airlock Corruption: {str(e)}"}
                    time.sleep(0.2)
                    continue
            time.sleep(0.1)
            
        return {"error": f"Airlock Timeout: Blender did not process mutation {cmd_id} within {timeout}s"}

    # --- HTTP READ PATH (is_mutation=False) ---
    headers = {"X-Vibe-Token": VIBE_TOKEN, "Content-Type": "application/json"}
    try:
        resp = requests.request(method, f"{BLENDER_API_URL}{path}", json=data, headers=headers, timeout=10)
        
        # Session tracking
        new_sid = resp.headers.get("X-Vibe-Session")
        try:
            body = resp.json()
            if "session" in body: new_sid = body["session"]
        except: pass

        if new_sid and SESSION_ID and new_sid != SESSION_ID:
            SESSION_ID = new_sid
            return {"error": "STALE_STATE_DETECTED: Refresh belief map."}
        SESSION_ID = new_sid
        
        if resp.status_code == 403: monitor.report_violation("Unauthorized access attempt.")
        if resp.status_code in {200, 202}:
            try: return resp.json()
            except: return {"result": resp.text}
        return {"error": f"Error {resp.status_code}: {resp.text}"}
    except Exception as e: return {"error": f"Failed: {str(e)}"}

# --- TOOL GROUPS ---

@mcp.tool()
def validate_humanoid_rig(armature_name: str) -> str:
    """THE DOCTOR: Validates if a rig follows the standard Humanoid bone structure.
    Essential for ensuring animations work correctly in production environments."""
    return str(blender_request("POST", "/command", data={"type": "unity_op", "action": "validate_humanoid", "target": armature_name, "intent": "RIG"}, is_mutation=True))

@mcp.tool()
def optimize_avatar_mesh(obj_name: str, ratio: float = 0.5) -> str:
    """THE POLISHER: Reduces the polycount of a mesh by a specific ratio (0.0 to 1.0).
    Use this to create optimized versions of high-poly assets."""
    return str(blender_request("POST", "/command", data={"type": "unity_op", "action": "optimize_avatar", "target": obj_name, "ratio": ratio, "intent": "OPTIMIZE"}, is_mutation=True))

@mcp.tool()
def generate_viseme_key(mesh_name: str, viseme: str) -> str:
    """THE VOX: Creates a viseme shape key slot (e.g., 'vrc.v_aa', 'vrc.v_ih') for lip-sync.
    Use this when preparing character meshes for VRChat."""
    return str(blender_request("POST", "/command", data={"type": "viseme_op", "name": mesh_name, "viseme": viseme, "intent": "ANIMATE"}, is_mutation=True))

@mcp.tool()
def begin_transaction() -> str:
    """THE ARCHIVIST: Starts a multi-command transaction. 
    All subsequent mutations will be grouped into a single Undo step."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "begin_transaction", "intent": "GENERAL"}, is_mutation=True))

@mcp.tool()
def commit_transaction(rationale_check: str) -> str:
    """THE ARCHIVIST: Finalizes the current multi-command transaction.
    HARD GATE: Requires a JSON rationale_check containing the current 'scene_hash' 
    to prove the AI has processed the force-fed context."""
    try:
        check = json.loads(rationale_check)
        if "scene_hash" not in check:
            return "Error: Hard Gate Violation. 'scene_hash' missing from rationale_check."
        
        # Verify the hash matches the current state
        current_state = blender_request("GET", "/blender/scene_state")
        if current_state.get("scene_hash") != check["scene_hash"]:
            return f"Error: Hash Mismatch. Action blocked. Expected {current_state.get('scene_hash')}, got {check['scene_hash']}."
            
        return str(blender_request("POST", "/command", data={"type": "system_op", "action": "commit_transaction", "intent": "GENERAL", "rationale": check}, is_mutation=True))
    except Exception as e:
        return f"Error processing Hard Gate: {str(e)}"

@mcp.tool()
def rollback_transaction() -> str:
    """THE ARCHIVIST: Aborts the current transaction and reverts all changes since 'begin_transaction'."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "rollback_transaction", "intent": "GENERAL"}, is_mutation=True))

@mcp.tool()
def hot_reload_blender_bridge() -> str:
    """Triggers a self-reload within Blender to pick up latest code changes."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "reload", "intent": "GENERAL"}, is_mutation=True))

@mcp.tool()
def reconcile_state(assumptions: str) -> str:
    """Verifies agent beliefs against Blender state. assumptions: JSON string."""
    try: return str(blender_request("POST", "/reconcile", data=json.loads(assumptions)))
    except: return "Error: Invalid JSON."

@mcp.tool()
def validate_scene_integrity() -> str:
    """Checks for architectural invariants like scale sanity and missing cameras."""
    return str(blender_request("GET", "/validate"))

@mcp.tool()
def get_scene_telemetry() -> str:
    """Returns structured scene data: poly counts, materials, and hardware stats."""
    return str(blender_request("GET", "/status"))

@mcp.tool()
def inspect_object_forensics(name: str) -> str:
    """Recursive node tree dump for deep material/shader analysis."""
    return str(blender_request("GET", f"/forensic?name={name}"))

@mcp.tool()
def execute_strategic_intent(intent: str) -> str:
    """THE DIRECTOR: Runs high-level atomic artistic recipes like 'RESTORE_AVATAR_COLORS_RED'."""
    return str(blender_request("POST", "/command", data={"type": "macro_op", "intent": intent.upper()}, is_mutation=True))

@mcp.tool()
def manage_modifier(name: str, action: str, modifier_name: str, modifier_type: str = None, properties: str = None) -> str:
    """Manages object modifiers (add, remove, set) with safety rails."""
    payload = {"type": "modifier_op", "name": name, "action": action, "mod_name": modifier_name, "mod_type": modifier_type, "intent": "OPTIMIZE"}
    if properties:
        try:
            props = json.loads(properties)
            payload.update({"action": "set", "props": props})
            return str(blender_request("POST", "/command", data=payload, is_mutation=True))
        except: return "Error: Invalid JSON."
    return str(blender_request("POST", "/command", data=payload, is_mutation=True))

@mcp.tool()
def transform_object(name: str, operation: str, x: float, y: float, z: float) -> str:
    """Moves, rotates, or scales an object. operation: 'translate', 'rotate', 'scale'."""
    return str(blender_request("POST", "/command", data={"type": "transform", "name": name, "op": operation, "value": str((x,y,z)), "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def add_primitive(type: str) -> str:
    """Adds a new primitive (cube, sphere, monkey)."""
    m = {"cube": "mesh.primitive_cube_add", "sphere": "mesh.primitive_uv_sphere_add", "monkey": "mesh.primitive_monkey_add"}
    if type.lower() not in m: return "Unsupported type."
    return str(blender_request("POST", "/command", data={"type": "run_op", "op": m[type.lower()], "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def manage_nodes(name: str, action: str, node_type: str = None, target_type: str = "SHADER", link_data: str = None) -> str:
    """Manages Node Trees (add, link). link_data: JSON string of socket names."""
    payload = {"type": "node_op", "action": action, "name": name, "target_type": target_type.upper(), "node_type": node_type, "intent": "LIGHT"}
    if link_data:
        try: payload.update(json.loads(link_data))
        except: return "Error: Invalid JSON."
    return str(blender_request("POST", "/command", data=payload, is_mutation=True))

@mcp.tool()
def apply_physics(name: str, type: str) -> str:
    """THE SIMULATOR: Applies RIGID_BODY or CLOTH physics to an object.
    Use this to instantly make an object respond to gravity or behave like fabric."""
    return str(blender_request("POST", "/command", data={"type": "physics_op", "name": name, "phys_type": type.upper(), "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def material_preview_sandbox() -> str:
    """THE SHOWROOM: Spawns a temporary preview sphere to test material changes safely.
    Use this to see how a material looks without modifying your main meshes."""
    return str(blender_request("POST", "/command", data={"type": "cleanup_op", "action": "material_preview_sandbox", "intent": "OPTIMIZE"}, is_mutation=True))

@mcp.tool()
def setup_lighting(name: str, type: str = "POINT", energy: float = 10.0, color: str = "(1, 1, 1)") -> str:
    """Configures a light source with safety energy caps."""
    return str(blender_request("POST", "/command", data={"type": "lighting_op", "name": name, "type_light": type.upper(), "energy": energy, "color": color, "intent": "LIGHT"}, is_mutation=True))

@mcp.tool()
def manage_constraints(owner_name: str, action: str, type: str, target_name: str = None, constraint_name: str = None, properties: str = None) -> str:
    """Rigging tools: TRACK_TO, FOLLOW_PATH, COPY_LOCATION. properties: JSON string."""
    payload = {"type": "constraint_op", "action": action, "name": owner_name, "target": target_name, "c_type": type.upper(), "c_name": constraint_name, "intent": "RIG"}
    if properties:
        try: payload["props"] = json.loads(properties)
        except: return "Error: Invalid JSON."
    return str(blender_request("POST", "/command", data=payload, is_mutation=True))

@mcp.tool()
def set_viewport_shading(mode: str = "SOLID") -> str:
    """Changes UI shading: WIREFRAME, SOLID, MATERIAL, RENDERED."""
    return str(blender_request("POST", "/command", data={"type": "viewport_op", "mode": mode.upper(), "intent": "LIGHT"}, is_mutation=True))

@mcp.tool()
def take_viewport_screenshot() -> ImageContent:
    """Captures an OpenGL screenshot for visual feedback."""
    res = blender_request("POST", "/command", data={"type": "render_op", "intent": "GENERAL"}, is_mutation=True)
    if isinstance(res, dict) and "result" in res:
        path = res["result"]
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
                # Determine mime type based on extension
                mime = "image/png" if path.endswith(".png") else "image/jpeg"
                return ImageContent(data=data, mime_type=mime)
    return ImageContent(data=b"", mime_type="image/png")

@mcp.tool()
def scan_external_asset(path: str) -> str:
    """Performs a deep security scan on a .blend, .fbx, or .obj file before use."""
    violations = SecurityGate.check_asset(path)
    if violations:
        return f"❌ SECURITY ALERT: {violations[0]}"
    return f"✅ Asset {path} passed security scan."

@mcp.tool()
def link_external_library(filepath: str, name: str, directory: str = "Object") -> str:
    """Links assets from external .blend files safely. Performs an automatic security scan."""
    violations = SecurityGate.check_asset(filepath)
    if violations:
        return f"❌ LINK BLOCKED: {violations[0]}"
    return str(blender_request("POST", "/command", data={"type": "link_op", "filepath": filepath, "name": name, "directory": directory, "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def secure_write_file(path: str, content: str) -> str:
    """Writes a file ONLY after passing an AST Security Audit. Enforces workspace hygiene."""
    if ".." in path or path.startswith("/"): return "Path traversal blocked."
    if any(fp in path for fp in ["security_gate.py", "server.py", "bridge_logic.py", "__init__.py"]): return "Infrastructure protection."
    if SecurityGate.check_python(content): return "Security Violation."
    
    # --- WORKSPACE HYGIENE ENFORCEMENT ---
    # Automatically route temporary files to avatar_scripts/ if they are in root
    if "/" not in path and any(path.endswith(ext) for ext in [".json", ".txt", ".log"]):
        # Exception: System logs or critical configs might need root, but generally we want them moved.
        # We will move them to avatar_scripts/ automatically.
        original_path = path
        path = os.path.join("avatar_scripts", path)
        redirected = True
    else:
        redirected = False

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f: f.write(content)
        msg = f"Wrote {path}."
        if redirected:
            msg += f" (Auto-sorted from '{original_path}' for hygiene)"
        return msg
    except Exception as e: return f"Failed: {str(e)}"

@mcp.tool()
def protect_object(name: str, protected: bool = True) -> str:
    """THE GUARDIAN: Locks or unlocks an object from deletion.
    locked objects cannot be deleted by the AI until unprotected.
    Set protected=False to unlock."""
    script = f"bpy.data.objects['{name}']['vibe_protected'] = {1 if protected else 0}"
    return str(blender_request("POST", "/command", data={"type": "exec_script", "script": script, "description": f"PROTECT:{name}", "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def undo_last_operation() -> str:
    """Performs a global Blender Undo (Ctrl+Z equivalent). Use this to revert a mistake."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "undo", "intent": "GENERAL"}, is_mutation=True))

@mcp.tool()
def create_safety_checkpoint(name: str) -> str:
    """Saves a timestamped copy of the current .blend file to the 'checkpoints/' folder.
    Use BEFORE performing risky structural changes."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "checkpoint", "name": name, "intent": "GENERAL"}, is_mutation=True))

@mcp.tool()
def manage_collection(name: str, action: str = "add", obj_name: str = None) -> str:
    """THE ORGANIZER: Creates collections or links objects to them. action: 'add' or 'link'."""
    return str(blender_request("POST", "/command", data={"type": "collection_op", "name": name, "action": action, "obj_name": obj_name, "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def manage_material(name: str, obj_name: str = None) -> str:
    """THE SURFACER: Creates a new material and optionally assigns it to an object."""
    return str(blender_request("POST", "/command", data={"type": "material_op", "name": name, "obj_name": obj_name, "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def trigger_bake(resolution: int = 1024) -> str:
    """THE OVEN: Triggers a texture bake with a 2048px hardware safety cap."""
    return str(blender_request("POST", "/command", data={"type": "bake_op", "resolution": resolution, "intent": "OPTIMIZE"}, is_mutation=True))

@mcp.tool()
def set_animation_keyframe(name: str, prop: str = "location", frame: int = 1) -> str:
    """THE ANIMATOR: Inserts a keyframe for a property at a specific frame."""
    return str(blender_request("POST", "/command", data={"type": "animation_op", "name": name, "prop": prop, "frame": frame, "intent": "ANIMATE"}, is_mutation=True))

@mcp.tool()
def manage_camera(name: str, active: bool = True) -> str:
    """THE CINEMATOGRAPHER: Spawns a camera and optionally makes it the active view."""
    return str(blender_request("POST", "/command", data={"type": "camera_op", "name": name, "active": active, "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def set_world_background(color: str = "(0.05, 0.05, 0.05, 1)") -> str:
    """THE STAGEHAND: Sets the global environment background color."""
    return str(blender_request("POST", "/command", data={"type": "world_op", "color": color, "intent": "LIGHT"}, is_mutation=True))

@mcp.tool()
def create_procedural_curve(name: str, coords: str = "[(0,0,0), (1,1,1)]") -> str:
    """THE PATHFINDER: Creates a 3D Poly Curve from a list of (x,y,z) coordinate tuples."""
    return str(blender_request("POST", "/command", data={"type": "curve_op", "name": name, "coords": coords, "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def manage_object_locks(name: str, lock: bool = True) -> str:
    """THE JAILER: Locks or unlocks all transform axes (Loc/Rot/Scale) for an object."""
    return str(blender_request("POST", "/command", data={"type": "lock_op", "name": name, "lock": lock, "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def process_mesh(action: str) -> str:
    """THE BLACKSMITH: shade_smooth, shade_flat, or join selected objects."""
    return str(blender_request("POST", "/command", data={"type": "mesh_op", "action": action, "intent": "OPTIMIZE"}, is_mutation=True))

@mcp.tool()
def manage_vertex_groups(name: str, vg_name: str) -> str:
    """THE WEIGHTER: Creates a new vertex group on a mesh object."""
    return str(blender_request("POST", "/command", data={"type": "vg_op", "name": name, "vg_name": vg_name, "intent": "RIG"}, is_mutation=True))

@mcp.tool()
def setup_spatial_audio(name: str) -> str:
    """THE COMPOSER: Spawns a 3D Speaker object for spatialized sound."""
    return str(blender_request("POST", "/command", data={"type": "audio_op", "name": name, "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def import_export_asset(action: str, filepath: str) -> str:
    """THE GATEKEEPER: action: 'import_fbx' or 'export_fbx'."""
    if action == "import_fbx":
        violations = SecurityGate.check_asset(filepath)
        if violations:
            return f"❌ IMPORT BLOCKED: {violations[0]}"
    return str(blender_request("POST", "/command", data={"type": "io_op", "action": action, "filepath": filepath, "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def create_3d_annotation(text: str) -> str:
    """THE SCRIBBLE: Creates a Grease Pencil object for 3D notes and markup."""
    return str(blender_request("POST", "/command", data={"type": "annotation_op", "text": text, "intent": "SCENE_SETUP"}, is_mutation=True))

@mcp.tool()
def save_as_new_copy(filename: str) -> str:
    """Saves the current blend file as a new copy with the specified filename.
    Useful for versioning (e.g., 'avatar_v3.blend')."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "save_copy", "name": filename, "intent": "GENERAL"}, is_mutation=True))

@mcp.tool()
def reset_material_standard(material_name: str) -> str:
    """THE JANITOR: Wipes a material and resets it to a standard, clean Principled BSDF (Gray).
    Use this to fix broken shaders, pink textures, or corruption."""
    return str(blender_request("POST", "/command", data={"type": "cleanup_op", "action": "reset_material", "target": material_name, "intent": "OPTIMIZE"}, is_mutation=True))

@mcp.tool()
def scan_for_nan_inf() -> str:
    """THE WATCHDOG: Scans all objects for NaN (Not a Number) or Infinite values in transforms and geometry.
    Run this if the physics explode or the viewport glitches."""
    return str(blender_request("POST", "/query", data={"type": "cleanup_op", "action": "scan_nan"}, is_mutation=False))

@mcp.tool()
def audit_external_dependencies() -> str:
    """THE AUDITOR: Checks all external file references (Images, Libraries) to ensure they exist on disk.
    Prevents missing textures and pink materials."""
    return str(blender_request("POST", "/query", data={"type": "audit_op", "action": "check_deps"}, is_mutation=False))

@mcp.tool()
def validate_export_contract() -> str:
    """THE GATEKEEPER: Checks scene validity before Export.
    Flags: Unapplied Scale, Non-Zero Rotation, N-Gons, Loose Geometry.
    Use this BEFORE exporting to external engines."""
    return str(blender_request("POST", "/query", data={"type": "audit_op", "action": "validate_export"}, is_mutation=False))

@mcp.tool()
def audit_rig_integrity() -> str:
    """THE CHIROPRACTOR: Scans all bones and constraints for NaN values, roll corruption, or broken hierarchies.
    Essential for ensuring animations play correctly after export."""
    return str(blender_request("POST", "/query", data={"type": "audit_op", "action": "audit_rig"}, is_mutation=False))

@mcp.tool()
def audit_shape_key_integrity() -> str:
    """THE VISEME GUARD: Scans all meshes for broken or basis-mismatched shape keys.
    Prevents facial expressions from vanishing during asset import in other engines."""
    return str(blender_request("POST", "/query", data={"type": "audit_op", "action": "audit_shape_keys"}, is_mutation=False))

@mcp.tool()
def audit_vertex_groups() -> str:
    """THE WEIGHTING GUARD: Scans for vertices that have NO weight assignments on rigged meshes.
    Prevents the 'Spiking Mesh' bug during deformation."""
    return str(blender_request("POST", "/query", data={"type": "audit_op", "action": "audit_weights"}, is_mutation=False))

@mcp.tool()
def audit_identity(target_name: str = None, depth: str = "SHALLOW") -> str:
    """THE ARCHITECT'S SEAL: Generates a unique signature for an object or the whole scene.
    depth: 'SHALLOW' (fast), 'DEEP' (vertex-level), 'SCENE' (full scene layout).
    Use this to verify if things have moved or changed unexpectedly."""
    return str(blender_request("POST", "/query", data={"type": "audit_op", "action": "identity", "target": target_name, "depth": depth.upper()}, is_mutation=False))

@mcp.tool()
def emergency_viewport_downgrade() -> str:
    """THE PANIC BUTTON: Instantly saves a GPU/UI freeze by switching to Solid Mode and disabling all modifiers.
    Use this if Blender becomes unresponsive or laggy."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "panic_downgrade"}, is_mutation=True))

@mcp.tool()
def generate_forensic_dump() -> str:
    """THE CASE STUDY: Bundles logs, telemetry, and a screenshot into a diagnostic folder.
    Run this after a major failure or before a human review."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "forensic_dump"}, is_mutation=True))

@mcp.tool()
def find_object_by_traits(vertex_count: int = None, material_name: str = None) -> str:
    """THE TRACKER: Finds objects based on physical traits rather than names.
    Use this if you think an object was renamed or to verify identity."""
    return str(blender_request("POST", "/query", data={"type": "audit_op", "action": "find_by_traits", "v_count": vertex_count, "mat_name": material_name}, is_mutation=False))

@mcp.tool()
def sandbox_modify_object(object_name: str, script: str) -> str:
    """THE SURGEON'S TABLE: Clones an object, runs a script on the clone, validates integrity, 
    and only swaps the data back if it passes. Use for risky mesh/rig edits."""
    return str(blender_request("POST", "/command", data={"type": "exec_script", "description": f"SANDBOX:{object_name}", "script": script, "sandbox_target": object_name}, is_mutation=True))

@mcp.tool()
def purge_orphans() -> str:
    """THE GARBAGE COLLECTOR: Recursively deletes unused meshes, materials, and textures.
    Run this to reduce file size and fix 'ghost' data."""
    return str(blender_request("POST", "/command", data={"type": "cleanup_op", "action": "purge_orphans"}, is_mutation=True))

@mcp.tool()
def hard_refresh_depsgraph() -> str:
    """THE DEFIBRILLATOR: Forces a full rebuild of Blender's Dependency Graph.
    Use this if modifiers are stuck, bones aren't moving, or the viewport is lying."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "depsgraph_refresh"}, is_mutation=True))

@mcp.tool()
def check_heartbeat() -> str:
    """Reads the Blender heartbeat. Use this to verify if the Blender main thread is alive."""
    path = "/home/bamn/BlenderVibeBridge/metadata/vibe_health.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                age = time.time() - data.get("timestamp", 0)
                data["heartbeat_age_seconds"] = round(age, 2)
                return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error reading heartbeat: {str(e)}"
    return "Heartbeat file missing. Blender may be hung or bridge not started."

@mcp.tool()
def get_vibe_audit_log(lines: int = 20) -> str:
    """Retrieves the last N entries from the JSONL audit log.
    Essential for verifying why an operation was BLOCKED or failed."""
    path = "/home/bamn/BlenderVibeBridge/logs/vibe_audit.jsonl"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading audit log: {str(e)}"
    return "Audit log missing."

import psutil

# ... (inside existing imports) ...

@mcp.tool()
def run_adversarial_preflight() -> str:
    """THE WARDEN: Performs a deep system audit to detect and resolve zombie processes, 
    port conflicts, and kernel instabilities. Run this BEFORE any major session or 
    if the bridge feels 'stuck'."""
    issues = []
    
    # 1. Zombie Blender Check
    zombies = []
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and "blender" in proc.info['name'].lower():
            try:
                if proc.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_STOPPED):
                    zombies.append(proc.info['pid'])
            except: continue
    
    if zombies:
        issues.append(f"Zombie Blender PIDs detected: {zombies}. Killing...")
        for pid in zombies:
            try: psutil.Process(pid).kill()
            except: pass

    # 2. Port 22000 Cleanup
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", 22000)) == 0:
            # Check if heartbeat is stale
            health_res = check_heartbeat()
            if "Error" in health_res or "missing" in health_res:
                issues.append("Port 22000 is occupied but heartbeat is stale. Releasing port...")
                for proc in psutil.process_iter(['pid', 'connections']):
                    try:
                        for conn in proc.info.get('connections', []):
                            if conn.laddr.port == 22000:
                                psutil.Process(proc.info['pid']).kill()
                    except: continue

    # 3. Airlock Verification
    if not os.path.exists(INBOX_PATH):
        issues.append("Airlock Inbox missing. Creating...")
        os.makedirs(INBOX_PATH, exist_ok=True)

    # 4. Critical Error Scan
    log_errs = get_blender_errors()
    if "ERROR" in log_errs or "CRITICAL" in log_errs:
        issues.append("Recent critical errors detected in bridge.log. Inspecting logs recommended.")

    report = {
        "safe_to_proceed": len(issues) == 0,
        "issues": issues,
        "recommendation": "System healthy. Proceed with orchestration." if len(issues) == 0 else "System cleaned. Restart recommended if issues persist."
    }
    return json.dumps(report, indent=2)

@mcp.tool()
def get_current_beliefs() -> str:
    """THE PHILOSOPHER: Returns the system's current derived beliefs and confidence scores.
    Enforces Epistemic Integrity by showing provenance and expiry for all conclusions."""
    path = "/home/bamn/BlenderVibeBridge/metadata/vibe_beliefs.jsonl"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading belief ledger: {str(e)}"
    return "Belief Ledger missing."

@mcp.tool()
def get_blender_errors() -> str:
    """Retrieves the last 20 lines from the bridge.log file for low-level debugging."""
    path = "/home/bamn/BlenderVibeBridge/bridge.log"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                lines = f.readlines()
                return "".join(lines[-20:])
        except Exception as e:
            return f"Error reading log: {str(e)}"
    return "Log file missing."

@mcp.tool()
def get_blender_invariants(category: str = "scene") -> str:
    """THE SENSOR: Returns deterministic engine facts from Blender.
    Categories: 'heartbeat', 'file', 'scene', 'context', 'datablock', 'error', 'entropy'.
    Use this to verify state before and after any mutation."""
    if category.lower() == "entropy":
        return json.dumps({
            "entropy_budget": ENTROPY_BUDGET,
            "entropy_used": ENTROPY_USED,
            "remaining": ENTROPY_BUDGET - ENTROPY_USED
        })
    
    endpoints = {
...
        "heartbeat": "/blender/heartbeat",
        "file": "/blender/file_state",
        "scene": "/blender/scene_state",
        "context": "/blender/context_state",
        "datablock": "/blender/datablock_state",
        "error": "/blender/error_state"
    }
    path = endpoints.get(category.lower(), "/blender/scene_state")
    return str(blender_request("GET", path))

@mcp.tool()
def get_state_hash() -> str:
    """THE CALCULATOR: Returns a deterministic SHA256 hash of the current scene state."""
    res = blender_request("GET", "/blender/scene_state")
    if isinstance(res, dict) and "scene_hash" in res:
        return res["scene_hash"]
    return "UNKNOWN"

@mcp.tool()
def get_wal_tail(lines: int = 20) -> str:

@mcp.tool()
def force_restart_blender_bridge() -> str:
    """THE DEFIBS: Triggers an out-of-band restart of the Blender timer loop.
    Use this if Blender is online but not processing commands (stuck queue)."""
    return str(blender_request("GET", "/restart", is_mutation=True))

if __name__ == "__main__": mcp.run()
