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

# BlenderVibeBridge: Hardened Airlock (v1.5.0)
import bpy
import os
import json
import time
from ..logging.logger import vibe_log
from ..handlers.opcodes import OPCODE_MAP
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE_PATH = '/home/bamn/BlenderVibeBridge'
INBOX_PATH = os.path.join(BASE_PATH, 'vibe_queue', 'kernel', 'inbox')
OUTBOX_PATH = os.path.join(BASE_PATH, 'vibe_queue', 'kernel', 'outbox')

class AirlockHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            # Trigger process via timer (main thread safe)
            pass

observer = None

def start_watchdog():
    global observer
    if observer and observer.is_alive(): return
    os.makedirs(INBOX_PATH, exist_ok=True)
    event_handler = AirlockHandler()
    observer = Observer()
    observer.schedule(event_handler, INBOX_PATH, recursive=False)
    observer.daemon = True
    observer.start()
    vibe_log("WATCHDOG: Event-driven airlock active.")

class TransactionGate:
    def __init__(self):
        self.active = False
        self.start_time = 0
        self.timeout = 60
        self.project_path = "/home/bamn/ALCOM/Projects/BAMN-EXTO"

    def begin(self):
        self.active = True
        self.start_time = time.time()
        vibe_log("TRANSACTION STARTED")

    def commit(self, intent="GENERAL"):
        self.active = False
        vibe_log("TRANSACTION COMMITTED")
        self.local_checkpoint(f"Ghost Audit: {intent}")

    def rollback(self):
        self.active = False
        vibe_log("TRANSACTION ROLLED BACK")

    def local_checkpoint(self, message):
        if not os.path.exists(os.path.join(self.project_path, ".git")): return
        try:
            import subprocess
            subprocess.run(["git", "-C", self.project_path, "add", "."], check=True)
            subprocess.run(["git", "-C", self.project_path, "commit", "-m", message], check=True)
        except Exception as e:
            vibe_log(f"GHOST_AUDIT_FAILURE: {e}")

    def check_timeout(self):
        if self.active and (time.time() - self.start_time > self.timeout):
            vibe_log("TRANSACTION TIMEOUT")
            self.rollback()

gate = TransactionGate()

def wait_for_depsgraph():
    """Checks if the dependency graph is currently evaluating."""
    # If Blender is calculating modifiers or physics, this will be busy
    depsgraph = bpy.context.evaluated_depsgraph_get()
    return False # Placeholder for a more complex 'is_evaluating' check if needed

def is_user_busy():
    """Detects if the user is actively clicking or stroking."""
    # Checks if interface is locked by a modal operator (like painting or moving)
    return bpy.context.window_manager.is_interface_locked

def poll_airlock(forced=False):
    """Event-driven opcode dispatcher."""
    try:
        # --- USER INTENT GUARD ---
        if is_user_busy():
            # vibe_log("USER BUSY: Holding mutations...")
            return 0.5

        # --- DEPSGRAPH SENTINEL ---
        # If Blender is busy 'compiling' modifiers, hold mutation
        if wait_for_depsgraph():
            return 0.1

        start_watchdog()
        gate.check_timeout()
        if not os.path.exists(INBOX_PATH): return 0.5
        
        files = [f for f in os.listdir(INBOX_PATH) if f.endswith('.json')]
        if not files: return 0.5
        
        files.sort()
        f = files[0]; path = os.path.join(INBOX_PATH, f)
        
        try:
            with open(path, 'r') as file:
                data = json.load(file)
            
            opcode = data.get('type')
            action = data.get('action')
            
            # --- TRANSACTION GATE ---
            if opcode != 'system_op' and not gate.active:
                raise Exception("UNAUTHORIZED_MUTATION: No transaction active.")

            # --- OPCODE DISPATCH ---
            handler = OPCODE_MAP.get(opcode)
            if handler:
                if opcode == 'system_op':
                    result = handler(data, gate)
                else:
                    result = handler(data)
            else:
                raise Exception(f"INVALID_OPCODE: {opcode}")

            # SUCCESS RESPONSE
            res_file = os.path.join(OUTBOX_PATH, 'res_' + f)
            with open(res_file + ".tmp", 'w') as out_f:
                json.dump({'status': 'SUCCESS', 'result': result}, out_f)
            os.rename(res_file + ".tmp", res_file)
                
        except Exception as e:
            vibe_log(f'KERNEL_ERROR: {e}')
            res_file = os.path.join(OUTBOX_PATH, 'res_' + f)
            with open(res_file + ".tmp", 'w') as out_f:
                json.dump({'status': 'ERROR', 'message': str(e)}, out_f)
            os.rename(res_file + ".tmp", res_file)
        finally:
            if os.path.exists(path): os.remove(path)
                
    except Exception as e:
        vibe_log(f"AIRLOCK_CRITICAL: {e}")
    return 0.1