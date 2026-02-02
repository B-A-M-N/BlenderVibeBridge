# BlenderVibeBridge: Dependency Manifest (v1.5.0)
import subprocess
import sys
import importlib
import os

def ensure_dependencies():
    """Ensures Blender's internal Python has the required modules in a local lib folder."""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    lib_path = os.path.join(base_path, "lib")
    os.makedirs(lib_path, exist_ok=True)
    
    if lib_path not in sys.path:
        sys.path.append(lib_path)
        
    required = ["watchdog", "pydantic"]
    for module in required:
        try:
            importlib.import_module(module)
        except ImportError:
            print(f"[VIBE] INSTALLING ISOLATED DEPENDENCY: {module}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--target", lib_path, module])

if __name__ == "__main__":
    ensure_dependencies()
