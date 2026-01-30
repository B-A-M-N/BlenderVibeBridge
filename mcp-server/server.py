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

# Ensure logs directory exists
os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)

class AuditLogger:
    @staticmethod
    def log_mutation(method, path, data, response):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "method": method,
            "path": path,
            "request_data": data,
            "response": response,
            "capability": data.get("capability", "UNKNOWN") if data else "UNKNOWN"
        }
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
    
    # Log the intent
    if is_mutation:
        logger.info(f"MUTATION_REQUEST: {method} {path} | Data: {json.dumps(data)}")
    else:
        logger.info(f"READ_REQUEST: {method} {path}")

    safe, reason = monitor.is_safe(is_mutation)
    if not safe: 
        logger.warning(f"BLOCKED: {reason}")
        return {"error": reason}

    # Semantic Enforcement
    if is_mutation and data:
        target_name = data.get("name") or data.get("obj_name")
        if target_name:
            reg_path = "metadata/vibe_registry.json"
            if os.path.exists(reg_path):
                try:
                    with open(reg_path, "r") as f:
                        registry = json.load(f)
                        role = registry.get(target_name, {}).get("role", "").upper()
                        if role in ["PRIMARY_LIGHT", "MAIN_CAMERA"] and data.get("type") in ["run_op", "mesh_op"]:
                            monitor.report_violation(f"Attempt to delete locked object: {target_name}")
                            return {"error": f"Role Locked: {target_name}"}
                except: pass

    # Security Audit for Scripts
    if data and data.get("type") == "exec_script":
        script = data.get("script")
        if script:
            violations = SecurityGate.check_python(script)
            if violations:
                logger.warning(f"SECURITY_VIOLATION blocked script: {violations}")
                return {"error": f"Security Violation: {violations[0]}"}

    # --- HYBRID DISPATCH ---
    if is_mutation:
        import uuid
        cmd_id = str(uuid.uuid4())
        payload = data or {}
        payload["id"] = cmd_id
        
        # 1. Write to Inbox
        os.makedirs(INBOX_PATH, exist_ok=True)
        inbox_file = os.path.join(INBOX_PATH, f"{cmd_id}.json")
        with open(inbox_file, "w") as f:
            json.dump(payload, f)
            
        # 2. Poll Outbox
        os.makedirs(OUTBOX_PATH, exist_ok=True)
        outbox_file = os.path.join(OUTBOX_PATH, f"res_{cmd_id}.json")
        timeout = 15
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if os.path.exists(outbox_file):
                try:
                    with open(outbox_file, "r") as f:
                        response_content = f.read()
                    os.remove(outbox_file)
                    resp_json = json.loads(response_content)
                    AuditLogger.log_mutation(method, path, data, resp_json)
                    return resp_json
                except Exception as e:
                    return {"error": f"Airlock Read Error: {str(e)}"}
            time.sleep(0.1)
            
        return {"error": f"Airlock Timeout: Blender did not process mutation {cmd_id} within {timeout}s"}

    # --- HTTP READ PATH (is_mutation=False) ---
    headers = {"X-Vibe-Token": VIBE_TOKEN, "Content-Type": "application/json"}
    try:
        resp = requests.request(method, f"{BLENDER_API_URL}{path}", json=data, headers=headers, timeout=10)
        
        new_sid = resp.headers.get("X-Vibe-Session")
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
def hot_reload_blender_bridge() -> str:
    """Triggers a self-reload within Blender to pick up latest code changes."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "reload"}, is_mutation=True))

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
    """Runs atomic artistic recipes like 'RESTORE_AVATAR_COLORS_RED'."""
    return str(blender_request("POST", "/command", data={"type": "macro_op", "intent": intent.upper()}, is_mutation=True))

@mcp.tool()
def manage_modifier(name: str, action: str, modifier_name: str, modifier_type: str = None, properties: str = None) -> str:
    """Manages object modifiers (add, remove, set) with safety rails."""
    payload = {"type": "modifier_op", "name": name, "action": action, "mod_name": modifier_name, "mod_type": modifier_type}
    if properties:
        try:
            props = json.loads(properties)
            for k, v in props.items():
                payload.update({"prop": k, "value": str(v)})
                blender_request("POST", "/command", data=payload, is_mutation=True)
            return f"✅ {modifier_name} updated."
        except: return "Error: Invalid JSON."
    return str(blender_request("POST", "/command", data=payload, is_mutation=True))

@mcp.tool()
def transform_object(name: str, operation: str, x: float, y: float, z: float) -> str:
    """Moves, rotates, or scales an object. operation: 'translate', 'rotate', 'scale'."""
    return str(blender_request("POST", "/command", data={"type": "transform", "name": name, "op": operation, "value": str((x,y,z))}, is_mutation=True))

@mcp.tool()
def add_primitive(type: str) -> str:
    """Adds a new primitive (cube, sphere, monkey)."""
    m = {"cube": "mesh.primitive_cube_add", "sphere": "mesh.primitive_uv_sphere_add", "monkey": "mesh.primitive_monkey_add"}
    if type.lower() not in m: return "Unsupported type."
    return str(blender_request("POST", "/command", data={"type": "run_op", "op": m[type.lower()]}, is_mutation=True))

@mcp.tool()
def manage_nodes(name: str, action: str, node_type: str = None, target_type: str = "SHADER", link_data: str = None) -> str:
    """Manages Node Trees (add, link). link_data: JSON string of socket names."""
    payload = {"type": "node_op", "action": action, "name": name, "target_type": target_type.upper(), "node_type": node_type}
    if link_data:
        try: payload.update(json.loads(link_data))
        except: return "Error: Invalid JSON."
    return str(blender_request("POST", "/command", data=payload, is_mutation=True))

@mcp.tool()
def apply_physics(name: str, type: str) -> str:
    """Applies RIGID_BODY or CLOTH physics."""
    return str(blender_request("POST", "/command", data={"type": "physics_op", "name": name, "phys_type": type.upper()}, is_mutation=True))

@mcp.tool()
def setup_lighting(name: str, type: str = "POINT", energy: float = 10.0, color: str = "(1, 1, 1)") -> str:
    """Configures a light source with safety energy caps."""
    return str(blender_request("POST", "/command", data={"type": "lighting_op", "name": name, "type_light": type.upper(), "energy": energy, "color": color}, is_mutation=True))

@mcp.tool()
def manage_constraints(owner_name: str, action: str, type: str, target_name: str = None) -> str:
    """Rigging tools: TRACK_TO, FOLLOW_PATH, COPY_LOCATION."""
    return str(blender_request("POST", "/command", data={"type": "constraint_op", "action": action, "name": owner_name, "target": target_name, "c_type": type.upper()}, is_mutation=True))

@mcp.tool()
def set_viewport_shading(mode: str = "SOLID") -> str:
    """Changes UI shading: WIREFRAME, SOLID, MATERIAL, RENDERED."""
    return str(blender_request("POST", "/command", data={"type": "viewport_op", "mode": mode.upper()}, is_mutation=True))

@mcp.tool()
def take_viewport_screenshot() -> str:
    """Captures an OpenGL screenshot for visual feedback."""
    return str(blender_request("POST", "/command", data={"type": "render_op"}, is_mutation=True))

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
    return str(blender_request("POST", "/command", data={"type": "link_op", "filepath": filepath, "name": name, "directory": directory}, is_mutation=True))

@mcp.tool()
def secure_write_file(path: str, content: str) -> str:
    """Writes a file ONLY after passing an AST Security Audit. Enforces workspace hygiene."""
    if ".." in path or path.startswith("/"): return "Path traversal blocked."
    if any(fp in path for fp in ["security_gate.py", "server.py", "bridge_logic.py"]): return "Infrastructure protection."
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
def undo_last_operation() -> str:
    """Performs a global Blender Undo (Ctrl+Z equivalent). Use this to revert a mistake."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "undo"}, is_mutation=True))

@mcp.tool()
def create_safety_checkpoint(name: str) -> str:
    """Saves a timestamped copy of the current .blend file to the 'checkpoints/' folder.
    Use BEFORE performing risky structural changes."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "checkpoint", "name": name}, is_mutation=True))

@mcp.tool()
def save_as_new_copy(filename: str) -> str:
    """Saves the current blend file as a new copy with the specified filename.
    Useful for versioning (e.g., 'avatar_v3.blend')."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "save_copy", "name": filename}, is_mutation=True))

@mcp.tool()
def reset_material_standard(material_name: str) -> str:
    """THE JANITOR: Wipes a material and resets it to a standard, clean Principled BSDF (Gray).
    Use this to fix broken shaders, pink textures, or corruption."""
    return str(blender_request("POST", "/command", data={"type": "cleanup_op", "action": "reset_material", "target": material_name}, is_mutation=True))

@mcp.tool()
def scan_for_nan_inf() -> str:
    """THE WATCHDOG: Scans all objects for NaN (Not a Number) or Infinite values in transforms and geometry.
    Run this if the physics explode or the viewport glitches."""
    return str(blender_request("POST", "/command", data={"type": "cleanup_op", "action": "scan_nan"}, is_mutation=False))

@mcp.tool()
def audit_external_dependencies() -> str:
    """THE AUDITOR: Checks all external file references (Images, Libraries) to ensure they exist on disk.
    Prevents missing textures and pink materials."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "check_deps"}, is_mutation=False))

@mcp.tool()
def validate_export_contract() -> str:
    """THE GATEKEEPER: Checks scene validity before Export.
    Flags: Unapplied Scale, Non-Zero Rotation, N-Gons, Loose Geometry.
    Use this BEFORE exporting to Unity/Unreal."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "validate_export"}, is_mutation=False))

@mcp.tool()
def audit_rig_integrity() -> str:
    """THE CHIROPRACTOR: Scans all bones and constraints for NaN values, roll corruption, or broken hierarchies.
    Essential for ensuring animations play correctly in Unity."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "audit_rig"}, is_mutation=False))

@mcp.tool()
def audit_shape_key_integrity() -> str:
    """THE VISEME GUARD: Scans all meshes for broken or basis-mismatched shape keys.
    Prevents facial expressions from vanishing during Unity import."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "audit_shape_keys"}, is_mutation=False))

@mcp.tool()
def audit_vertex_groups() -> str:
    """THE WEIGHTING GUARD: Scans for vertices that have NO weight assignments on rigged meshes.
    Prevents the 'Spiking Mesh' bug in Unity."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "audit_weights"}, is_mutation=False))

@mcp.tool()
def get_trait_fingerprint(object_name: str) -> str:
    """THE IDENTITY LOCK: Generates a unique fingerprint based on mesh traits (verts, mats, bounds).
    Use this to verify you are still editing the same object after a rename or reload."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "fingerprint", "target": object_name}, is_mutation=False))

@mcp.tool()
def emergency_viewport_downgrade() -> str:
    """THE PANIC BUTTON: Instantly saves a GPU/UI freeze by switching to Solid Mode and disabling all modifiers.
    Use this if Blender becomes unresponsive or laggy."""
    return str(blender_request("POST", "/command", data={"type": "system_op", "action": "panic_downgrade"}, is_mutation=True))

@mcp.tool()
def get_scene_hash() -> str:
    """THE REALITY ANCHOR: Generates a hash of all object transforms and vertex counts.
    Use this to detect if the user (or another addon) has moved things while the AI was processing."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "scene_hash"}, is_mutation=False))

@mcp.tool()
def generate_forensic_dump() -> str:
    """THE CASE STUDY: Bundles logs, telemetry, and a screenshot into a diagnostic folder.
    Run this after a major failure or before a human review."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "forensic_dump"}, is_mutation=True))

@mcp.tool()
def find_object_by_traits(vertex_count: int = None, material_name: str = None) -> str:
    """THE TRACKER: Finds objects based on physical traits rather than names.
    Use this if you think an object was renamed or to verify identity."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "find_by_traits", "v_count": vertex_count, "mat_name": material_name}, is_mutation=False))

@mcp.tool()
def sandbox_modify_object(object_name: str, script: str) -> str:
    """THE SURGEON'S TABLE: Clones an object, runs a script on the clone, validates integrity, 
    and only swaps the data back if it passes. Use for risky mesh/rig edits."""
    return str(blender_request("POST", "/command", data={"type": "exec_script", "description": f"SANDBOX:{object_name}", "script": script, "sandbox_target": object_name}, is_mutation=True))

@mcp.tool()
def get_vertex_order_hash(object_name: str) -> str:
    """THE BASIS SHIELD: Generates a unique hash of the vertex index mapping.
    Use this BEFORE and AFTER an operation to ensure Shape Keys/Blendshapes won't break in Unity."""
    return str(blender_request("POST", "/command", data={"type": "audit_op", "action": "vertex_hash", "target": object_name}, is_mutation=False))

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
def get_blender_errors() -> str:
    """Retrieves the last 20 lines from the bridge log to debug script failures."""
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
def force_restart_blender_bridge() -> str:
    """THE DEFIBS: Triggers an out-of-band restart of the Blender timer loop.
    Use this if Blender is online but not processing commands (stuck queue)."""
    return str(blender_request("GET", "/restart", is_mutation=True))

if __name__ == "__main__": mcp.run()