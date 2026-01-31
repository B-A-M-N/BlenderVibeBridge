# BlenderVibeBridge: Crash-Proof Kernel (v1.5.0)
import bpy
from .core.engine import register_core, unregister_core

bl_info = {
    "name": "BlenderVibeBridge",
    "author": "B-A-M-N",
    "version": (1, 5, 0),
    "blender": (3, 6, 0),
    "location": "System > BlenderVibeBridge",
    "description": "Governed Geometry Kernel for AI Orchestration",
    "category": "System",
}

def register():
    register_core()

def unregister():
    unregister_core()

if __name__ == "__main__":
    register()