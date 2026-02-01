# BlenderVibeBridge: Operational Protocol (v1.0)

## 1. Intent Alignment (The Handshake)
All mutation requests MUST include a valid `intent` string. The Kernel will reject any opcode not mapped to the declared intent.
- **OPTIMIZE**: modifier_op, mesh_op, cleanup_op, bake_op.
- **RIG**: constraint_op, vg_op, unity_op.
- **LIGHT**: lighting_op, world_op, viewport_op, node_op.
- **ANIMATE**: animation_op, viseme_op.
- **SCENE_SETUP**: run_op, io_op, collection_op, camera_op, link_op, curve_op, material_op, audio_op, lock_op, physics_op, transform, exec_script.
- **GENERAL**: audit_op, system_op, render_op, macro_op.

## 2. Workspace Hygiene (Redirection)
Files created in the root directory with `.json`, `.txt`, or `.log` extensions are automatically redirected to `avatar_scripts/`.
- **Rule**: Always check `avatar_scripts/` before reporting a file-write failure.

## 3. Failure Recovery
If a tool returns an error, the agent MUST call `get_vibe_audit_log` immediately to identify the specific security rule (e.g., `INTENT_MISMATCH`, `BUDGET_EXHAUSTED`) before attempting a workaround.

## 4. Transaction Management
For complex operations, use `begin_transaction()` and `commit_transaction()` to preserve the Mutation Budget and ensure atomic undo states.

## 5. Blender AI Procedural Workflow
All operations must strictly adhere to the [BLENDER_PROCEDURAL_WORKFLOW.md](./BLENDER_PROCEDURAL_WORKFLOW.md) and [BLENDER_PROCEDURAL_FLOW.md](./BLENDER_PROCEDURAL_FLOW.md) to ensure identity stability across file reloads and undo/redo cycles. Use UUIDs as the primary key for all datablock references.

## 6. Vibe Lifecycle Discipline
Strict adherence to [LIFECYCLE_DISCIPLINE.md](./LIFECYCLE_DISCIPLINE.md) is required for lifecycle, IO safety, and crash recovery. AI agents must pause automation during user manipulation and respect the failure thresholds.

## 7. Environment & Unit Validation
Agents MUST normalize all transform data to SI Meters before transmission. The Bridge Kernel will reject any payload that violates the declared dependency manifest or unit normalization contract.

## 8. Ghost Audit Protocol (Forensic Sync)
To prevent irreversible data loss and provide high-fidelity session history, the bridge enforces the **Ghost Audit Protocol**:
- **Local Isolation**: Every project folder SHOULD be initialized as a local-only Git repository.
- **Commit-on-Commit**: Every successful `commit_transaction` within Blender triggers an automatic `git add . && git commit` in the project directory.
- **LFS Tracking**: Large assets (.fbx, .blend, .png) MUST be tracked via Git LFS to maintain repository performance.
- **Integrity Gating**: The Security Gate (`--integrity`) verifies that the project's disk state is clean before finalizing any AI task.

## 9. Reflex Arc Architecture (2-Agent System)
To prevent engine-sync deadlocks and maintain a clean creative context, the bridge utilizes a **Reflex Arc**:
- **Foreman (Gemini CLI)**: Handles high-level strategy and issues structured intents to `vibe_queue/intents/`.
- **Operator (scripts/operator.py)**: A dedicated low-level slave that polls for intents, generates `bpy` code via Gemini Flash, and handles the engine-sync waiting logic.
- **Kernel Airlock**: The Operator pushes processed commands to `vibe_queue/kernel/`, which the Blender Kernel processes only when the engine is stable.
