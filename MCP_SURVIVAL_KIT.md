# 🛡️ MCP Blender Survival Kit: The Lifesaver Tier

**Core Philosophy:** Blender is a non-deterministic DCC. The MCP transforms it into a controlled, state-managed lab.
**Goal:** Prevent silent corruption, context desync, and "looks fine until export" disasters.

---

## 1. 🧠 State & Context Sanity (The "Hard Refresh")
**Objective:** Fix "Nothing updates unless I restart" and ghost modifiers.

### Tools
*   `reset_blender_context()`: Force-refreshes active object, mode (Object/Edit/Pose), and triggers a viewport redraw.
*   `hard_refresh_depsgraph()`: Toggles visibility, reassigns mesh datablocks, and forces a dependency graph rebuild to clear ghost state.

## 2. 🧹 Datablock Integrity (The Garbage Collector)
**Objective:** Stop orphaned blocks from eating memory and causing instability.

### Tools
*   `scan_orphaned_data()`: Reports unused meshes, materials, and armatures.
*   `purge_orphans()`: Deterministically deletes phantom data.
*   `check_linked_data()`: Warns if the user is about to edit a linked (library) asset and offers "Make Local" + Snapshot.

## 3. 📸 Object-Level Snapshotting (The Surgeon's Undo)
**Objective:** Restore *just* the horns or tail without reverting the whole scene.

### Tools
*   `snapshot_object(obj_name)`: Saves mesh geometry, shape keys, and materials to a temp `.blend` buffer.
*   `restore_object_from_snapshot(obj_name, snapshot_id)`: Swaps the live object with the buffered version.
*   **Auto-Hook**: MCP automatically calls `snapshot_object` before any destructive modifier (Decimate, Remesh) or boolean operation.

## 4. 🚑 Viewport Survival (The Panic Button)
**Objective:** Prevent the viewport from crashing the GPU driver.

### Tools
*   `emergency_viewport_downgrade()`: Instantly switches to Solid Mode, disables Modifiers, Transparency, Shadows, and Overlays.
*   `material_preview_sandbox()`: Spawns a proxy sphere for shader edits, preventing "Live Mesh" corruption during material dev.

## 5. 🦴 Rig & Armature Safeguards (The Chiropractor)
**Objective:** Keep the skeleton valid for game engines.

### Tools
*   `audit_armature_health()`: Checks for bone count drift, hierarchy breaks, and roll corruption vs. baseline.
*   `reset_pose_corruption()`: Clears invalid constraints, NaN transforms, and locked pose states.

## 6. 🎭 Shape Key Lifesavers (The Viseme Guard)
**Objective:** Prevent "Unity Import Failed" due to vertex mismatches.

### Tools
*   `check_shape_key_integrity()`: Scans for mismatched vertex counts and zeroed deltas.
*   `diff_shape_keys()`: Compares current keys against the original import to highlight accidental drifts.

## 7. 📤 Export-Time Reality Checks (The Gatekeeper)
**Objective:** Fail fast in Blender, not slowly in Unity.

### Tools
*   `validate_export_readiness()`: Checks for unapplied scale, non-uniform transforms, inverted normals, and forbidden modifiers.
*   `dry_run_export()`: Simulates the FBX export process to catch crash bugs without writing to disk.

## 8. 🕵️ Crash Forensics (The Black Box)
**Objective:** Turn random crashes into actionable data.

### Logic
*   **Fingerprint Logger**: On every operation, log: `Last_Action`, `Active_Object`, `Poly_Count`, `VRAM_Usage`.
*   **Recovery Manifest**: On startup, check for a "dirty exit" and offer to restore the last auto-snapshot.

---

## 🚀 Implementation Matrix

| Priority | Feature | Complexity | Why? |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | `reset_blender_context` | Low | Fixes 50% of "Blender is broken" issues. |
| **CRITICAL** | `snapshot_object` | Medium | Essential for non-destructive AI editing. |
| **CRITICAL** | `emergency_viewport_downgrade` | Low | Prevents UI freezes/crashes. |
| **HIGH** | `validate_export_readiness` | Medium | Saves hours of engine debugging. |
| **HIGH** | `audit_armature_health` | High | Rigs are the #1 source of pain. |
| **MED** | `purge_orphans` | Low | Keeps file size and RAM sane. |