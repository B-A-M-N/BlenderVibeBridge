# BlenderVibeBridge: Crash-Proof Kernel (v1.5.0)
import bpy
from .core.engine import register_core, unregister_core
from .operators.ui_panel import register as register_ui, unregister as unregister_ui

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
    register_ui()

def unregister():
    unregister_ui()
    unregister_core()

if __name__ == "__main__":
    register()