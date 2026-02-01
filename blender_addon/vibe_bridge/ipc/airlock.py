import bpy
import os
import json
import time
from ..logging.logger import vibe_log

BASE_PATH = '/home/bamn/BlenderVibeBridge'
INBOX_PATH = os.path.join(BASE_PATH, 'vibe_queue', 'inbox')
OUTBOX_PATH = os.path.join(BASE_PATH, 'vibe_queue', 'outbox')

class TransactionGate:
    def __init__(self):
        self.active = False
        self.start_time = 0
        self.timeout = 60 # Seconds
        self.project_path = "/home/bamn/ALCOM/Projects/BAMN-EXTO"

    def begin(self):
        self.active = True
        self.start_time = time.time()
        vibe_log("TRANSACTION STARTED")

    def commit(self, intent="GENERAL"):
        self.active = False
        vibe_log("TRANSACTION COMMITTED")
        self.local_checkpoint(f"Bridge Audit: {intent}")

    def rollback(self):
        self.active = False
        vibe_log("TRANSACTION ROLLED BACK")

    def local_checkpoint(self, message):
        """Creates a local-only git commit in the project folder."""
        if not os.path.exists(os.path.join(self.project_path, ".git")):
            return
        
        try:
            import subprocess
            # Ensure LFS is tracking what it needs
            subprocess.run(["git", "-C", self.project_path, "add", "."], check=True)
            subprocess.run(["git", "-C", self.project_path, "commit", "-m", message], check=True)
            vibe_log(f"GHOST AUDIT: Checkpoint created - {message}")
        except Exception as e:
            vibe_log(f"GHOST AUDIT FAILURE: {e}")

    def check_timeout(self):
        if self.active and (time.time() - self.start_time > self.timeout):
            vibe_log("TRANSACTION TIMEOUT - AUTO ROLLBACK")
            self.rollback()
            return True
        return False

    def is_safe(self, cmd_type, action):
        # Transaction management ops are always safe
        if cmd_type == 'system_op' and action in ['begin_transaction', 'rollback_transaction', 'commit_transaction']:
            return True
        # Read ops (queries) would normally be safe, but airlock is primarily for mutations
        if not self.active:
            return False
        return True

gate = TransactionGate()

def poll_airlock():
    """Non-blocking polling of the filesystem airlock."""
    try:
        # Check for Transaction Timeout
        gate.check_timeout()

        if not os.path.exists(INBOX_PATH):
            os.makedirs(INBOX_PATH, exist_ok=True)
            
        files = [f for f in os.listdir(INBOX_PATH) if f.endswith('.json')]
        if not files:
            return 0.1 # High-frequency polling when idle
            
        files.sort()
        f = files[0]
        path = os.path.join(INBOX_PATH, f)
        
        try:
            with open(path, 'r') as file:
                data = json.load(file)
            
            cmd_type = data.get('type')
            action = data.get('action')
            intent = data.get('intent', 'GENERAL')

            # --- TRANSACTION GATE ---
            if not gate.is_safe(cmd_type, action):
                vibe_log(f"BLOCKED: Mutation attempted outside of transaction. Type: {cmd_type}, Action: {action}")
                raise Exception("MUTATION_BLOCKED: Active transaction required for write operations.")

            # Handle Transaction Ops
            if cmd_type == 'system_op':
                if action == 'begin_transaction':
                    gate.begin()
                elif action == 'commit_transaction':
                    gate.commit(intent=intent)
                elif action == 'rollback_transaction':
                    gate.rollback()

            vibe_log(f"PROCESSING INTENT: {intent} (File: {f})")
            
            if data.get('type') == 'exec_script':
                exec(data.get('script'), {'bpy': bpy, 'vibe_log': vibe_log})
                
            res_file = os.path.join(OUTBOX_PATH, 'res_' + f)
            temp_res = res_file + ".tmp"
            
            with open(temp_res, 'w') as out_f:
                json.dump({'status': 'SUCCESS', 'intent': intent}, out_f)
                out_f.flush()
            os.rename(temp_res, res_file)
                
        except Exception as e:
            vibe_log(f'ERROR: {e}')
            res_file = os.path.join(OUTBOX_PATH, 'res_' + f)
            temp_res = res_file + ".tmp"
            with open(temp_res, 'w') as out_f:
                json.dump({'status': 'ERROR', 'message': str(e)}, out_f)
                out_f.flush()
            os.rename(temp_res, res_file)
        finally:
            if os.path.exists(path):
                os.remove(path)
                
    except Exception as e:
        vibe_log(f"CRITICAL AIRLOCK FAILURE: {e}")
        
    return 0.1 # Keep polling cadence
