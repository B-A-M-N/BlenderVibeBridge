# BlenderVibeBridge: Dependency Manifest (v1.5.0)
import subprocess
import sys
import importlib

def ensure_dependencies():
    """Ensures Blender's internal Python has the required modules."""
    required = ["watchdog", "pydantic"]
    for module in required:
        try:
            importlib.import_module(module)
        except ImportError:
            print(f"[VIBE] INSTALLING MISSING DEPENDENCY: {module}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])

if __name__ == "__main__":
    ensure_dependencies()
