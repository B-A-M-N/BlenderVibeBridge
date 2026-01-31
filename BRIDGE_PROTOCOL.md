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
