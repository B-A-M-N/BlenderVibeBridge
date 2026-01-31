import os
import time

LOG_PATH = '/home/bamn/BlenderVibeBridge/bridge.log'

def vibe_log(msg):
    """Structured logging for VibeBridge."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f'[{timestamp}] [VIBE-KERNEL] {msg}\n'
    try:
        with open(LOG_PATH, 'a') as f:
            f.write(formatted_msg)
    except:
        # Fail silently to avoid freezing the main thread if disk is full/locked
        pass
