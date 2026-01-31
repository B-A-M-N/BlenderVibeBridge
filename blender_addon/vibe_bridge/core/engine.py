import bpy
import os
import json
import time
from ..logging.logger import vibe_log
from ..ipc.airlock import poll_airlock
from ..ipc.server import run_server_thread, update_snapshot

def poll_wrapper():
    """Timer callback that wraps airlock polling and snapshot updates."""
    # 1. Update shared memory snapshot for HTTP server (Read-Only Path)
    update_snapshot(bpy)
    
    # 2. Process Mutations (Airlock Path)
    next_call = poll_airlock()
    return next_call

def register_core():
    # Start thread-safe HTTP Query Server
    run_server_thread()
    
    if not bpy.app.timers.is_registered(poll_wrapper):
        bpy.app.timers.register(poll_wrapper, first_interval=1.0)
    vibe_log('KERNEL v1.5.0 CORE ACTIVE (Airlock + HTTP)')

def unregister_core():
    if bpy.app.timers.is_registered(poll_wrapper):
        bpy.app.timers.unregister(poll_wrapper)
    vibe_log('KERNEL v1.5.0 CORE SHUTDOWN')
