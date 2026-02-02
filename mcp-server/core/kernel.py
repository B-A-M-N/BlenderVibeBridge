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

# BlenderVibeBridge: Core Kernel (v1.5.0)
import os
import sys
import logging
import json
import time
import datetime
import requests

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

# --- CORE STATE ---
BLENDER_API_URL = "http://127.0.0.1:22000"
VIBE_TOKEN = "VIBE_777_SECURE"
SESSION_ID = None
AUDIT_LOG_PATH = "/home/bamn/BlenderVibeBridge/logs/vibe_audit.jsonl"
ENTROPY_BUDGET = 100
ENTROPY_USED = 0

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any, Union

# --- ISA SCHEMAS ---
class VibeMutation(BaseModel):
    id: Optional[str] = None
    type: str
    intent: str
    action: Optional[str] = None
    target: Optional[str] = None
    vibe_session_id: Optional[str] = None

    @validator('intent')
    def validate_intent(cls, v):
        allowed = {"OPTIMIZE", "RIG", "LIGHT", "ANIMATE", "SCENE_SETUP", "GENERAL", "AUDIT"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid intent: {v}")
        return v.upper()

class TransformMutation(VibeMutation):
    op: str # translate, rotate, scale
    value: str # "(x, y, z)"

    @validator('value')
    def validate_geometry(cls, v):
        # Prevent "geometrically insane" values
        import ast
        try:
            coords = ast.literal_eval(v)
            if any(abs(c) > 1000000 for c in coords):
                raise ValueError("Geometric magnitude exceeds 1M limit.")
        except:
            raise ValueError("Invalid coordinate format.")
        return v

import psutil
import socket

def discover_blender():
    """THE TRACKER: Automatically finds the Blender executable path across OSs."""
    import platform
    system = platform.system()
    if system == "Windows":
        paths = ["C:\\Program Files\\Blender Foundation\\Blender 3.6\\blender.exe", "C:\\Program Files\\Blender Foundation\\Blender 4.0\\blender.exe"]
    elif system == "Darwin": # macOS
        paths = ["/Applications/Blender.app/Contents/MacOS/Blender"]
    else: # Linux
        paths = ["/usr/bin/blender", "/usr/local/bin/blender", "blender"]
        
    for path in paths:
        try:
            # Check if command exists
            subprocess.run([path, "--version"], capture_output=True, check=True)
            return path
        except: continue
    return None

def get_api_sentinel():
    """THE SENTRY: Returns specific API mandates based on the Blender version."""
    # This information is injected into the AI BIOS to prevent 2.7x hallucinations
    return {
        "engine": "Blender",
        "version_target": "3.6 LTS",
        "mandates": [
            "Use 'bpy.ops.object.modifier_add(type=\"BOOLEAN\")' instead of legacy intersect tools.",
            "Use 'context.evaluated_depsgraph_get()' for current scene data.",
            "Material inputs must use 'nodes[\"Principled BSDF\"].inputs[\"Base Color\"]'."
        ]
    }

def system_audit():
    """THE WARDEN: Detects and resolves zombie processes and port conflicts."""
    issues = []
    
    # 1. Zombie Blender Check
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and "blender" in proc.info['name'].lower():
            try:
                if proc.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_STOPPED):
                    issues.append(f"Zombie Blender PID detected: {proc.info['pid']}. Killing...")
                    psutil.Process(proc.info['pid']).kill()
            except: continue

    # 2. Port 22000 Cleanup
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", 22000)) == 0:
                issues.append("Port 22000 is occupied. Attempting to identify owner...")
                for proc in psutil.process_iter(['pid', 'connections']):
                    try:
                        for conn in proc.info.get('connections', []):
                            if conn.laddr.port == 22000:
                                issues.append(f"Releasing port held by PID {proc.info['pid']}.")
                                psutil.Process(proc.info['pid']).kill()
                    except: continue
    except: pass

    return {
        "safe_to_proceed": len(issues) == 0 or "cleaned" in str(issues),
        "issues": issues,
        "status": "CLEAN" if not issues else "FIXED"
    }

class AuditLogger:
    _last_hash = "ROOT"

    @staticmethod
    def log_mutation(method, path, data, response):
        global ENTROPY_USED
        ENTROPY_USED += 1
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
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
        with open(AUDIT_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")

class SecurityMonitor:
    def __init__(self, threshold=3):
        self.violations = 0
        self.threshold = threshold
        self.panic_mode = False
        self.recovery_mode = False

    def report_violation(self, reason):
        self.violations += 1
        sys.stderr.write(f"\n[!] SECURITY VIOLATION ({self.violations}/{self.threshold}): {reason}\n")
        if self.violations >= self.threshold:
            self.panic_mode = True
            sys.stderr.write("\n[!!!] PANIC MODE ACTIVATED: BRIDGE IS NOW READ-ONLY.\n")

    def enter_recovery(self):
        self.recovery_mode = True
        logger.warning("RECOVERY_MODE ACTIVATED: State reconciliation required via log ingestion.")

    def exit_recovery(self):
        if self.recovery_mode:
            self.recovery_mode = False
            logger.info("RECOVERY_MODE DEACTIVATED: State reconciled.")

    def is_safe(self, is_mutation):
        if self.panic_mode and is_mutation:
            return False, "PANIC MODE: All mutations blocked."
        if self.recovery_mode and is_mutation:
            return False, "RECOVERY_MODE_ACTIVE: Mutation blocked. You MUST call 'get_blender_errors' or 'get_vibe_audit_log' to ingest the failure traceback before retrying."
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
