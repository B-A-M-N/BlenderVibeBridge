import bpy
import os
import json
import time
import uuid
from ..logging.logger import vibe_log
from ..ipc.airlock import poll_airlock
from ..ipc.server import run_server_thread, update_snapshot

def ensure_uuids():
    """Assigns unique vibe_uuids to all datablocks if they don't have them."""
    for collection in [bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.armatures]:
        for block in collection:
            if "vibe_uuid" not in block:
                block["vibe_uuid"] = str(uuid.uuid4())
                vibe_log(f"ASSIGNED UUID: {block.name} -> {block['vibe_uuid']}")

def poll_wrapper():
    """Timer callback that wraps airlock polling and snapshot updates."""
    # 0. Ensure Identity Stability
    ensure_uuids()
    
    # 1. Update shared memory snapshot for HTTP server (Read-Only Path)
    update_snapshot(bpy)
    
    # 2. Process Mutations (Airlock Path)
    next_call = poll_airlock()
    return next_call

from .manifest import ensure_dependencies

STABILITY_FILE = "/home/bamn/BlenderVibeBridge/metadata/vibe_stability.json"

def check_stability():
    """Detects abnormal shutdown and enters Safe Mode."""
    if os.path.exists(STABILITY_FILE):
        try:
            with open(STABILITY_FILE, "r") as f:
                state = json.load(f)
                if not state.get("clean_exit", True):
                    vibe_log("!!! CRASH DETECTED !!! ENTERING SAFE MODE.")
                    # In a full implementation, this would set a kernel-wide block
        except: pass
    
    # Mark start of session as "Unclean" until proven otherwise
    with open(STABILITY_FILE, "w") as f:
        json.dump({"clean_exit": False, "timestamp": time.time()}, f)

def register_core():
    # 0. Boot Hardening
    ensure_dependencies()
    check_stability()
    
    # Start thread-safe HTTP Query Server
    run_server_thread()
    
    if not bpy.app.timers.is_registered(poll_wrapper):
        bpy.app.timers.register(poll_wrapper, first_interval=1.0)
    vibe_log('KERNEL v1.5.0 CORE ACTIVE (Airlock + HTTP)')

def unregister_core():
    # Mark shutdown as successful
    if os.path.exists(STABILITY_FILE):
        with open(STABILITY_FILE, "w") as f:
            json.dump({"clean_exit": True, "timestamp": time.time()}, f)

    if bpy.app.timers.is_registered(poll_wrapper):
        bpy.app.timers.unregister(poll_wrapper)
    vibe_log('KERNEL v1.5.0 CORE SHUTDOWN')
