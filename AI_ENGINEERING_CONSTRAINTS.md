# AI Engineering Constraints & Safety Contract (Blender Edition)

This document defines the non-negotiable structural constraints for AI-generated code in this project. All contributions must adhere to these rules. Violations are considered critical bugs.

## 1. The "Iron Box" (Capability Scoping)
*   **Principle of Least Privilege**: All bridge requests MUST specify a required capability (e.g., `READ`, `MUTATE_SCENE`, `MUTATE_DATA`, `STRUCTURAL_CHANGE`).
*   **Non-Composition**: Capabilities are single-use and non-composable.
*   **Implicit Deny**: Any request lacking the necessary capability token is rejected before processing.

## 2. Forensic Audit & Replay
*   **Immutable Log**: Every mutation must be logged to `logs/vibe_audit.jsonl` with: `Timestamp`, `RequestID`, `Capability`, `TargetName/Path`, and `SerializedDelta`.
*   **State Checkpointing**: Strategic Actions must be reproducible via the audit log on a clean session.

## 3. Serialization & Data Paranoia
*   **Data Validation**: All `bpy.data` mutations must be validated against expected types.
*   **Name Integrity**: Avoid name collisions in `bpy.data` blocks (Meshes, Materials, Objects). Use unique naming conventions or check for existence before creation.
*   **Type Matching**: Strictly enforce that values match the field type in the target `bpy` struct (e.g., float vs int).

## 4. The Persistence Boundary
*   **Session Isolation**: MCP-originated changes are in-memory (RAM) until a human performs a `Save File` action.
*   **No Auto-Save**: The bridge must NEVER call `bpy.ops.wm.save_mainfile()` automatically.
*   **Undo Stack**: All mutations must be wrapped in `bpy.ops.ed.undo_push()` where applicable or be inherently reversible.

## 5. Human-in-the-Loop (HITL)
*   **Structural Triggers**: The following require explicit, out-of-band human confirmation:
    *   Creation/Deletion of any `.py` file outside the addon directory.
    *   Modification of User Preferences (`bpy.context.preferences`).
    *   Execution of arbitrary Python scripts via `exec()` or `eval()` (Strictly Forbidden usually, requires massive warning if bypassed).

## 6. Emergency Kill Switch
*   **The Red Button**: A mechanism (or `KILL_VIBE` env var) that instantly places the bridge in a read-only state and stops the HTTP server.
*   **Self-Destruct**: The bridge must stop if it detects internal inconsistency.

## 7. Active Development (Unfrozen)
*   **The Add-on (Python)**: **ACTIVE DEVELOPMENT**. Modifications to the `blender_addon/` directory are permitted to build the bridge.
*   **Heuristics**: Search logic should use `bpy.data` lookups effectively.

## 8. Fingerprinting & Verification
*   **Trait Signatures**: Targets should be verified where possible (e.g., verify Object name + Type).
*   **Ambiguity**: If multiple objects share the same name (Blender allows this in some contexts, or across scenes), the AI must ask for clarification or use the specific object reference.

## 9. Single Narrow API Layer
*   All Blender mutations must go through the designated `BlenderVibeBridge` server logic.
*   **Main Thread Dispatch**: All `bpy` API calls must be executed on the main thread via `bpy.app.timers`. NEVER call `bpy` from the HTTP thread.

## 10. Mandatory Transactions
*   **Implicit Wrapping**: Complex mutations should be grouped.
*   **Exception Handling**: On any server-side exception, log the error and attempt to leave the state clean.

## 11. Identity Stability
*   **References**: `bpy.types.Object` references in Python can become invalid if the object is deleted or the file is reloaded. Use names or persistent pointers if available/safe.

## 12. No Blender Tricks (Persistence Ban)
*   **No Handlers**: Registration of `bpy.app.handlers` (e.g., `load_post`, `save_pre`, `frame_change_post`) is STRICTLY FORBIDDEN.
*   **No Background Timers**: Unauthorized use of `bpy.app.timers` to create persistent background processes is blocked.

## 13. Idempotence & Read-Before-Write
*   **Atomic Idempotence**: All mutation tools MUST be idempotent. Repeating a request should have no side effects beyond the first successful application.
*   **RBW Loop**: Every mutation must follow the sequence: `Inspect (Tool)` -> `Validate (Logic)` -> `Mutate (Tool)` -> `Verify (Tool)`.

## 14. Asset Integrity & Scanning
*   **Mandatory Scan**: All external assets (`.blend`, `.fbx`, `.obj`, `.glb`, etc.) MUST be scanned via `scan_external_asset` before any import or link operation.
*   **No Auto-Run**: The bridge MUST NOT enable Blender's "Auto-run Python Scripts" preference.
*   **Script Block**: Any asset found containing embedded Python `import` or `exec` signatures must be rejected.

## The Meta-Rule
If a proposed solution is unusually short, clever, or bypasses a limitation, assume it is wrong. Prioritize safety and explicit verification over brevity.
