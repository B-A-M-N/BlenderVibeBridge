# 🛡️ MCP Blender Kernel: The Control Plane Specification

**Philosophy:** Blender is a hostile, non-deterministic environment. This Kernel transforms it into a verified, transactional Control Plane.
**Status:** DEFINITIVE TOOL INVENTORY.

---

## 🟢 1. THE KERNEL (Irreducible Safety Core)
*These must be active for the system to be considered "Safe".*

### 🔒 Execution Safety
*   **Atomic Operation Wrapper**: `begin_transaction()` -> `try` -> `commit` / `rollback`. (**ACTIVE**)
*   **Context Guard**: Snapshots and strict-restores Active Object, Selection, and Mode. Includes **Mode Rubber-Banding** to restore Sculpt/Edit state safely. (**ACTIVE**)
*   **Activity Gating**: Detects active user interaction (strokes). Mutations are held until the user releases the mouse. (**ACTIVE**)
*   **Operation Sandboxing**: Run destructive ops on `object.copy()` first. If successful, swap data. If fail, discard. (**ACTIVE**)

### 🛑 Corruption Defense
*   **NaN / Infinity Watchdog**: Scans Transforms, Bones, and Shape Keys for mathematical voids (`inf`/`nan`). (**ACTIVE**)
*   **Heartbeat & Progress API**: Real-time telemetry export of AI operation status and completion percentage. (**ACTIVE**)
*   **Dependency Graph Hard Refresh**: Forces a full depsgraph rebuild to clear ghost state. (**ACTIVE**)

### 🧹 State Hygiene
*   **Orphaned Datablock Purge**: Deterministically deletes unused meshes/materials.
*   **Dependency Tracker**: Detects missing textures or linked library drift. (**ACTIVE**)
*   **UUID Identity Registry**: Mandatory UUID-based management of all datablocks to survive file reloads and undo/redo cycles as defined in [BLENDER_PROCEDURAL_WORKFLOW.md](./BLENDER_PROCEDURAL_WORKFLOW.md) and [BLENDER_PROCEDURAL_FLOW.md](./BLENDER_PROCEDURAL_FLOW.md). (**ACTIVE**)

### 📤 Pipeline Gate
*   **Export Contract Enforcer**: Hard-fails export if Scale != 1, Normals are inverted, or N-Gons exist. (**ACTIVE**)

---

## 🟡 2. THE SURVIVAL SUIT (Workflow Protection)
*Tools that prevent "lost hours".*

*   **Manual/Auto Checkpoints**: `create_safety_checkpoint()`. (**ACTIVE**)
*   **Object-Level Snapshots**: Backup specific objects before modification.
*   **Janitor Tools**: `reset_material_standard()`, `reset_object_transforms()`. (**ACTIVE**)
*   **Emergency Viewport Downgrade**: Force Solid Mode + No Modifiers.

---

## ⚪ 3. THE INSPECTOR (Forensics & validation)
*Tools that detect "silent" errors.*

*   **Mesh Integrity Validator**: Non-manifold geometry, loose verts.
*   **Armature Health Audit**: Bone hierarchy hash, roll drift.
*   **Shape Key Integrity**: Mismatched vertex counts, zero deltas.
*   **Material Graph Validator**: Disconnected nodes, circular references.

---

## 🔴 4. THE INVENTORY (Full Tool Surface)

### Core Safety
*   Incremental Save Manager
*   Undo Stack Extender
*   Crash Fingerprint Logger

### Context Control
*   Mode Transition Guard
*   TOCTOU Guard
*   UI Lock / Serialized Queue

### Resource Integrity
*   VRAM Threshold Tripwire
*   Vertex Count Guard
*   Texture Resolution Watchdog

### Viewport
*   Material Preview Sandbox (Proxy Mesh)
*   Modifier Freeze Tool

### Geometry & Rig
*   Safe Recenter Tool
*   Pose Mode Corruption Reset
*   Shape Key Diff Tool

### Add-ons
*   Add-on Firewall / Quarantine

---

## 💀 BLENDER PAIN MAP vs. COUNTERMEASURES

| Pain Point | Implemented Countermeasure | Status |
| :--- | :--- | :--- |
| **Silent State Corruption** | **Atomic Execution Wrapper** | ✅ ACTIVE |
| **Undo Is Unreliable** | **Atomic Undo + Checkpoints** | ✅ ACTIVE |
| **Context Poisoning** | **ContextGuard** | ✅ ACTIVE |
| **NaN / Infinity Poisoning** | **NaN Watchdog** | ✅ ACTIVE |
| **Export-Time Betrayal** | **Export Contract Enforcer** | ✅ ACTIVE |
| **Material Mismatch** | **Janitor (Material Reset)** | ✅ ACTIVE |
| **Viewport Crashes** | **Emergency Downgrade** | ✅ ACTIVE |
| **Orphaned Datablocks** | **Orphan Purge** | ✅ ACTIVE |
| **Shape Key Fragility** | **Integrity Checker** | ✅ ACTIVE |
| **Bone Drift** | **Armature Audit** | ✅ ACTIVE |

---

## 🚀 Implementation Priority

1.  **Operation Sandboxing** (✅ COMPLETED).
2.  **Orphan Purge** (✅ COMPLETED).
3.  **Armature Audit** (✅ COMPLETED).