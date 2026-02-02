# BlenderVibeBridge: Reflex Arc Operator (v1.0.0)
# Copyright (C) 2026 B-A-M-N (The "Author")
#
# This script acts as the "Reflex" execution arm.
# It polls for Intents, generates bpy code, and triggers the Kernel.

import os
import time
import json
import requests
import subprocess

# --- CONFIGURATION ---
BASE_PATH = "/home/bamn/BlenderVibeBridge"
INTENT_INBOX = os.path.join(BASE_PATH, "vibe_queue", "intents", "inbox")
INTENT_OUTBOX = os.path.join(BASE_PATH, "vibe_queue", "intents", "outbox")
KERNEL_INBOX = os.path.join(BASE_PATH, "vibe_queue", "kernel", "inbox")
KERNEL_OUTBOX = os.path.join(BASE_PATH, "vibe_queue", "kernel", "outbox")

BRIDGE_URL = "http://localhost:22000" # Blender Bridge Port
# Gemini API Configuration
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
API_KEY = os.getenv("VIBE_API_KEY") 

def poll_intents():
    if not os.path.exists(INTENT_INBOX): return None
    files = sorted([f for f in os.listdir(INTENT_INBOX) if f.endswith(".json")])
    return os.path.join(INTENT_INBOX, files[0]) if files else None

def get_blender_status():
    try:
        # Check kernel heartbeat for stability
        res = requests.get(f"{BRIDGE_URL}/blender/heartbeat", timeout=1)
        return res.json()
    except:
        return {"responsive": False}

def execute_intent(order):
    print(f"📦 Processing Intent: {order['intent']} (Opcode: {order['opcode']})")

    # Load the Operator Gem BIOS
    gem_path = os.path.join(BASE_PATH, ".gemini", "gems", "blender-operator.md")
    try:
        with open(gem_path, "r") as f:
            system_instruction = f.read()
    except:
        return {"status": "ERROR", "message": "Gem BIOS missing: blender-operator.md"}

    # Construct the payload with system_instruction (Gems method)
    prompt = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{
            "parts": [{
                "text": f"TASK: {order['intent']}\nOpcode: {order['opcode']}\nUUID: {order.get('uuid')}\nDescription: {order['description']}"
            }]
        }]
    }

    # 1. Generate Script via Gemini Flash
    try:
        res = requests.post(f"{API_URL}?key={API_KEY}", json=prompt, timeout=10)
        if res.status_code != 200:
            # Redact key if it appears in error text
            err_msg = res.text.replace(API_KEY, "[REDACTED]")
            return {"status": "ERROR", "message": f"API Error ({res.status_code}): {err_msg}"}
        
        res_json = res.json()
        script = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        # Clean markdown if present
        if script.startswith("```python"): script = script[9:-3].strip()
        elif script.startswith("```"): script = script[3:-3].strip()
    except Exception as e:
        return {"status": "ERROR", "message": f"Flash Generation Failed: {e}"}

    # 2. Wait for Kernel Stability (Sentinel)
    while True:
        status = get_blender_status()
        if status.get("responsive"):
            # Optional: Check if depsgraph is busy
            break
        print("🧊 Blender Kernel Busy or Offline... waiting.")
        time.sleep(1.0)

    # 3. Push to Kernel Airlock
    payload = {
        "type": "exec_script", # Or specific opcode if fully mapped
        "intent": order['intent'],
        "script": script,
        "opcode": order['opcode'],
        "uuid": order.get('uuid')
    }
    
    cmd_id = order.get('id', str(time.time()))
    kernel_file = os.path.join(KERNEL_INBOX, f"reflex_{cmd_id}.json")
    
    with open(kernel_file + ".tmp", "w") as f:
        json.dump(payload, f)
    os.rename(kernel_file + ".tmp", kernel_file)
    
    # 4. Wait for Kernel Result
    kernel_res_file = os.path.join(KERNEL_OUTBOX, f"res_reflex_{cmd_id}.json")
    start_time = time.time()
    while time.time() - start_time < 60:
        if os.path.exists(kernel_res_file):
            with open(kernel_res_file, "r") as f:
                res = json.load(f)
            os.remove(kernel_res_file)
            return res
        time.sleep(0.1)
        
    return {"status": "ERROR", "message": "Kernel Timeout"}

def main():
    if not API_KEY:
        print("❌ Error: VIBE_API_KEY environment variable not set.")
        return

    print("🤖 Blender Operator (Reflex Arc) Online. Watching intent queue...")
    while True:
        task_path = poll_intents()
        if task_path:
            try:
                with open(task_path, 'r') as f:
                    order = json.load(f)

                result = execute_intent(order)

                # Write results to intent outbox
                out_name = "res_" + os.path.basename(task_path)
                with open(os.path.join(INTENT_OUTBOX, out_name), 'w') as f:
                    json.dump(result, f)

                os.remove(task_path)
                print(f"✅ Intent Complete: {out_name}")
            except Exception as e:
                print(f"❌ Critical Operator Error: {e}")

        time.sleep(0.5)

if __name__ == "__main__":
    main()
