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

    headers = {"X-Vibe-Token": VIBE_TOKEN, "Content-Type": "application/json"}
    if is_mutation and not limiter.check(): return {"error": "Rate limit exceeded."}

    try:
        resp = requests.request(method, f"{BLENDER_API_URL}{path}", json=data, headers=headers, timeout=10)
        
        # Audit Log for Mutations
        if is_mutation:
            try:
                resp_json = resp.json()
            except:
                resp_json = {"raw": resp.text}
            AuditLogger.log_mutation(method, path, data, resp_json)

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
def link_external_library(filepath: str, name: str, directory: str = "Object") -> str:
    """Links assets from external .blend files safely."""
    return str(blender_request("POST", "/command", data={"type": "link_op", "filepath": filepath, "name": name, "directory": directory}, is_mutation=True))

@mcp.tool()
def secure_write_file(path: str, content: str) -> str:
    """Writes a file ONLY after passing an AST Security Audit."""
    if ".." in path or path.startswith("/"): return "Path traversal blocked."
    if any(fp in path for fp in ["security_gate.py", "server.py", "bridge_logic.py"]): return "Infrastructure protection."
    if SecurityGate.check_python(content): return "Security Violation."
    try:
        with open(path, "w") as f: f.write(content)
        return f"Wrote {path}."
    except Exception as e: return f"Failed: {str(e)}"

if __name__ == "__main__": mcp.run()