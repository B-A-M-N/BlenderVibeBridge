# 🛡️ MCP Blender Control Plane: Deep Safety Primitives

**Core Philosophy:** Blender is a hostile environment for automation. It is stateful, leaky, and non-deterministic.
**Goal:** Transform Blender from a chaotic workshop into a verified, transactional Control Plane.

---

## 1. 🔒 Deterministic Operation Boundaries
**Objective:** Prevent silent partial failure and "leaky" state changes.

### Mechanism: Operation Sandboxing
*   **Copy-on-Write**: Destructive ops (Decimate, Remesh) run on a *duplicate datablock* first.
*   **Explicit Commit**: The result is only swapped in if the operation succeeds and passes validation.
*   **Zero Tolerance**: Any "leak" to the original object triggers a rollback.

## 2. ⚛️ Atomic Actions (All-or-Nothing)
**Objective:** No broken rigs or half-applied modifiers left behind.

### Mechanism: Atomic Execution Wrapper
*   **Transaction Block**: `begin_transaction()` -> [Ops] -> `commit_transaction()`.
*   **Auto-Rollback**: If step N fails, steps 1...(N-1) are reverted instantly.
*   **Stack Integrity**: Ensures the Undo Stack is never left in a dirty state.

## 3. 🚩 Dirty State & Baseline Hashing
**Objective:** Catch corruption *before* it ruins the file.

### Mechanism: Scene Dirty Flag Scanner
*   **State Hash**: Calculates a hash of vertex counts, bone hierarchies, and shape key deltas.
*   **Drift Alert**: Compares current state vs. `import_baseline_hash`. If they drift without authorization, the system locks.
*   **Compiler Warnings**: Reports unapplied transforms or depsgraph desyncs *before* save/export.

## 4. 🛡️ Non-Undoable Action Shield
**Objective:** Protect the Undo Stack from invalidation.

### Mechanism: Undo Guard
*   **Snapshot-on-Danger**: Forces a full file snapshot before any operation known to bypass/corrupt Undo (e.g., Python `bpy.data` deletes).
*   **Stack Watchdog**: Warns if the undo history is about to be cleared.

## 5. ⚡ Resource Tripwires
**Objective:** Turn crashes into recoverable events.

### Mechanism: Hard Limits
*   **VRAM Ceiling**: If usage > 90%, force viewport to Solid/Wireframe.
*   **Poly-Count Cap**: Reject sub-division commands that would exceed system limits.
*   **Texture Watchdog**: Auto-downscale 8k textures to 2k in viewport.

## 6. 🧩 Add-on Firewall
**Objective:** Stop untrusted code from breaking the scene.

### Mechanism: Isolation
*   **Touch Tracking**: Logs which add-on modified which datablock.
*   **Quarantine**: Automatically disables an add-on if it throws uncaught exceptions during an MCP operation.

## 7. 📤 Export Contract Enforcement
**Objective:** Fail fast in Blender, not slowly in Unity/Unreal.

### Mechanism: The Contract
*   **Strict Validators**: Checks for N-Gons, Zero-Area Faces, Loose Verts, and Bone Naming Conventions.
*   **Loud Failure**: Refuses to export FBX/GLB if the contract is violated. No silent coercion.

## 8. 🕰️ Forensic Rewind
**Objective:** Recover from "unknown" catastrophes.

### Mechanism: Event Timeline
*   **Timestamped Actions**: Every tool call is logged with a timestamp and state hash.
*   **Time Travel**: Ability to revert to the state *before* the last crash using the auto-snapshots.

---

## 🚀 The Minimal Viable Core (MVC)

To build this without boiling the ocean, we prioritize:

1.  **Atomic Wrapper**: Wrap all `execute_script` calls in `try/except` with auto-undo.
2.  **Snapshot-on-Danger**: Auto-checkpoint before `decimate`, `remesh`, or `join`.
3.  **Export Contract**: A simple script to validate mesh integrity before export.
