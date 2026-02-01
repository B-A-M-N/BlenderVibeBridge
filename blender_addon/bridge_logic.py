# BlenderVibeBridge: Crash-Proof Kernel (v1.3.4)
import bpy, os, json, time, threading, http.server, socket

BASE_PATH = '/home/bamn/BlenderVibeBridge'
INBOX_PATH = os.path.join(BASE_PATH, 'vibe_queue', 'inbox')
OUTBOX_PATH = os.path.join(BASE_PATH, 'vibe_queue', 'outbox')
LOG_PATH = os.path.join(BASE_PATH, 'bridge.log')

def vibe_log(msg):
    try:
        with open(LOG_PATH, 'a') as f:
            f.write(f'[{time.strftime("%H:%M:%S")}] [VIBE-FIX] {msg}\n')
    except: pass

def poll_airlock():
    try:
        if not os.path.exists(INBOX_PATH): os.makedirs(INBOX_PATH, exist_ok=True)
        files = [f for f in os.listdir(INBOX_PATH) if f.endswith('.json')]
        if files:
            files.sort(); f = files[0]; path = os.path.join(INBOX_PATH, f)
            try:
                with open(path, 'r') as file: data = json.load(file)
                result = None
                if data.get('type') == 'exec_script':
                    local_scope = {'bpy': bpy, 'vibe_log': vibe_log, 'result': None}
                    exec(data.get('script'), globals(), local_scope)
                    result = local_scope.get('result')
                
                response = {'status': 'SUCCESS'}
                if result is not None: response['result'] = result

                with open(os.path.join(OUTBOX_PATH, 'res_' + f), 'w') as out_f:
                    json.dump(response, out_f)
            except Exception as e:
                vibe_log(f'ERROR: {e}')
                with open(os.path.join(OUTBOX_PATH, 'res_' + f), 'w') as out_f:
                    json.dump({'status': 'ERROR', 'message': str(e)}, out_f)
            finally:
                if os.path.exists(path): os.remove(path)
    except: pass
    return 0.5

def register():
    if not bpy.app.timers.is_registered(poll_airlock):
        bpy.app.timers.register(poll_airlock, first_interval=1.0)
    vibe_log('KERNEL v1.3.4 ACTIVE')

def unregister():
    if bpy.app.timers.is_registered(poll_airlock):
        bpy.app.timers.unregister(poll_airlock)

