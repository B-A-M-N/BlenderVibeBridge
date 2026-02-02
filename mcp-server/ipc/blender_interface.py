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

# BlenderVibeBridge: Hardened IPC Dispatcher (v1.5.0)
import os
import json
import time
import uuid
import requests
import logging
from ..core.kernel import monitor, limiter, logger, SESSION_ID, BLENDER_API_URL, VIBE_TOKEN, AuditLogger
from ..core.schemas import TransformData, TransactionOp, VibeCommand, ModifierData, MaterialData, IOData
from security_gate import SecurityGate

INBOX_PATH = "/home/bamn/BlenderVibeBridge/vibe_queue/kernel/inbox"
OUTBOX_PATH = "/home/bamn/BlenderVibeBridge/vibe_queue/kernel/outbox"

def blender_request(method, path, data=None, is_mutation=False):
    global SESSION_ID
    
    # 1. Rate Limiting & Security Check
    if not limiter.check():
        return {"error": "Rate limit exceeded (5Hz)."}
    
    safe, reason = monitor.is_safe(is_mutation)
    if not safe:
        return {"error": reason}

    # 2. Data Hardening (Pydantic Validation)
    if is_mutation and data:
        cmd_id = str(uuid.uuid4())
        data["id"] = cmd_id
        try:
            t = data.get("type")
            if t == "transform": TransformData(**data)
            elif t == "system_op": TransactionOp(**data)
            elif t == "modifier_op": ModifierData(**data)
            elif t == "material_op": MaterialData(**data)
            elif t == "io_op": IOData(**data)
            else: VibeCommand(**data)
        except Exception as e:
            logger.error(f"SCHEMA_VIOLATION: {e}")
            return {"error": f"Iron Box Violation: {str(e)}"}

    # 3. Hybrid Dispatch Logic
    if is_mutation:
        os.makedirs(INBOX_PATH, exist_ok=True)
        inbox_file = os.path.join(INBOX_PATH, f"{data['id']}.json")
        
        # Atomic Write Pattern
        temp_file = inbox_file + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.rename(temp_file, inbox_file)
        
        # Poll Outbox with 60s Timeout
        outbox_file = os.path.join(OUTBOX_PATH, f"res_{data['id']}.json")
        start = time.time()
        while time.time() - start < 60:
            if os.path.exists(outbox_file):
                try:
                    with open(outbox_file, "r") as f:
                        resp = json.load(f)
                    os.remove(outbox_file)
                    AuditLogger.log_mutation(method, path, data, resp)
                    if resp.get("status") == "ERROR":
                        # Automatic Forensic Ingestion
                        try:
                            log_path = "/home/bamn/BlenderVibeBridge/bridge.log"
                            with open(log_path, "r") as log_f:
                                resp["forensic_context"] = "".join(log_f.readlines()[-5:])
                        except: pass
                        monitor.enter_recovery()
                    return resp
                except:
                    time.sleep(0.1)
            time.sleep(0.1)
        
        monitor.enter_recovery()
        return {"error": "IPC_TIMEOUT: Blender is unresponsive or kernel is deadlocked."}

    # HTTP Read Path (Read-Only)
    try:
        headers = {"X-Vibe-Token": VIBE_TOKEN, "Content-Type": "application/json"}
        resp = requests.request(method, f"{BLENDER_API_URL}{path}", json=data, headers=headers, timeout=5)
        return resp.json()
    except Exception as e:
        return {"error": f"READ_FAILURE: {str(e)}"}