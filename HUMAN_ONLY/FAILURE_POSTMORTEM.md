# BlenderVibeBridge: Failure Post-Mortem & Forensic Analysis

This document provides a guide for analyzing and recovering from common failure scenarios in the Blender-AI interface.

---

## 🔍 Forensic Artifacts
When a failure occurs, the following artifacts must be inspected:
1.  **`logs/vibe_audit.jsonl`**: The immutable record of what the AI sent and what the kernel received.
2.  **`bridge.log`**: The real-time output of the Python listener thread.
3.  **Blender System Console**: The terminal where Blender was launched (shows raw `bpy` tracebacks).

---

## 📉 Common Failure Signatures

### 1. The "Invalid Context" Crash
- **Symptom**: `RuntimeError: Operator bpy.ops.mesh.primitive_cube_add.poll() failed, context is incorrect`.
- **Root Cause**: The command was executed on a background thread or without a valid `VIEW_3D` window context.
- **Recovery**: The bridge automatically attempts a Context Override. If it fails, restart the bridge and ensure a 3D Viewport is visible in Blender.

### 2. The "Orphaned Data-Block" Leak
- **Symptom**: Objects are deleted, but Meshes/Materials remain in the file (visible in the Outliner under "Orphan Data").
- **Root Cause**: Blender logic: `bpy.data.objects.remove()` does not automatically remove the underlying mesh data.
- **Recovery**: Run the `maintenance_purge.sh` script or call the `purge_orphans` tool.

### 3. The "Python Sandbox" Block
- **Symptom**: `Security Block: Forbidden module import detected`.
- **Root Cause**: The AI attempted to use `os`, `subprocess`, or `sys` to interact with the host system.
- **Recovery**: This is a security feature. The AI must be re-instructed to use authorized VibeBridge tools instead of raw scripting.

---

## 🛠️ Recovery Procedures

### Level 1: Soft Reset (AI-Driven)
- Use `bpy.ops.ed.undo()` via the `system_op` opcode to revert the last transaction.
- Call `reconcile_state` to re-sync the AI's world-model.

### Level 2: Hard Reset (Human-Driven)
1.  **Stop**: Terminate the `start_bridge.sh` process.
2.  **Clean**: Manually delete any partial geometry or malformed objects in the Blender scene.
3.  **Bootstrap**: Restart the bridge.

---
**Copyright (C) 2026 B-A-M-N**
