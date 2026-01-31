import bpy
import os
import json
import time
from ..logging.logger import vibe_log

BASE_PATH = '/home/bamn/BlenderVibeBridge'
INBOX_PATH = os.path.join(BASE_PATH, 'vibe_queue', 'inbox')
OUTBOX_PATH = os.path.join(BASE_PATH, 'vibe_queue', 'outbox')

def poll_airlock():
    """Non-blocking polling of the filesystem airlock."""
    try:
        if not os.path.exists(INBOX_PATH):
            os.makedirs(INBOX_PATH, exist_ok=True)
            
        files = [f for f in os.listdir(INBOX_PATH) if f.endswith('.json')]
        if not files:
            return 0.1 # High-frequency polling when idle
            
        files.sort()
        f = files[0]
        path = os.path.join(INBOX_PATH, f)
        
        # LOG CONSULTATION GATE would happen here in a full implementation
        # For now, we follow the basic airlock protocol
        
        try:
            with open(path, 'r') as file:
                data = json.load(file)
            
            # Intent Verification
            intent = data.get('intent', 'GENERAL')
            vibe_log(f"PROCESSING INTENT: {intent} (File: {f})")
            
            if data.get('type') == 'exec_script':
                # TRANSACTION BEGIN
                exec(data.get('script'), {'bpy': bpy, 'vibe_log': vibe_log})
                # TRANSACTION COMMIT
                
            with open(os.path.join(OUTBOX_PATH, 'res_' + f), 'w') as out_f:
                json.dump({'status': 'SUCCESS', 'intent': intent}, out_f)
                
        except Exception as e:
            vibe_log(f'ERROR: {e}')
            with open(os.path.join(OUTBOX_PATH, 'res_' + f), 'w') as out_f:
                json.dump({'status': 'ERROR', 'message': str(e)}, out_f)
        finally:
            if os.path.exists(path):
                os.remove(path)
                
    except Exception as e:
        vibe_log(f"CRITICAL AIRLOCK FAILURE: {e}")
        
    return 0.1 # Keep polling cadence
