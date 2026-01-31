import bpy
import os
import json
import time
from ..logging.logger import vibe_log
from ..ipc.airlock import poll_airlock

def register_core():
    if not bpy.app.timers.is_registered(poll_airlock):
        bpy.app.timers.register(poll_airlock, first_interval=1.0)
    vibe_log('KERNEL v1.5.0 CORE ACTIVE')

def unregister_core():
    if bpy.app.timers.is_registered(poll_airlock):
        bpy.app.timers.unregister(poll_airlock)
    vibe_log('KERNEL v1.5.0 CORE SHUTDOWN')
