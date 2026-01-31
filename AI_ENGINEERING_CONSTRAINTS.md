# AI Engineering Constraints & Safety Contract (Blender Edition)

This document defines the non-negotiable structural constraints for AI-generated code in this project. All contributions must adhere to these rules. Violations are considered critical bugs.

## 1. The "Iron Box" (Capability Scoping)
*   **Principle of Least Privilege**: All bridge requests MUST specify a required capability (e.g., `READ`, `MUTATE_SCENE`, `MUTATE_DATA`, `STRUCTURAL_CHANGE`).
*   **Non-Composition**: Capabilities are single-use and non-composable.
*   **Implicit Deny**: Any request lacking the necessary capability token is rejected before processing.

## 2. Forensic Audit & Log-Driven Decisions
*   **Immutable Log**: Every mutation must be logged to `logs/vibe_audit.jsonl` with: `Timestamp`, `RequestID`, `Capability`, `TargetName/Path`, and `SerializedDelta`.
*   **Log-AS-STATE**: Logs are an input, not just an output. The AI MUST consult the log index before any mutation as defined in [LIFECYCLE_DISCIPLINE.md](./LIFECYCLE_DISCIPLINE.md).
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
*   **Implicit Wrapping**: Complex mutations should be grouped using `begin_transaction` and `commit_transaction`.
*   **Exception Handling**: On any server-side exception, log the error, consult the audit log, and attempt to leave the state clean via `rollback_transaction`.

## 11. Identity Stability
*   **References**: `bpy.types.Object` references in Python can become invalid if the object is deleted or the file is reloaded. Use names or persistent pointers if available/safe. Use `audit_identity` to verify state.
*   **UUID Enforcement**: All datablocks must be managed via UUIDs as defined in [BLENDER_PROCEDURAL_WORKFLOW.md](./BLENDER_PROCEDURAL_WORKFLOW.md) and [BLENDER_PROCEDURAL_FLOW.md](./BLENDER_PROCEDURAL_FLOW.md).

## 12. No Blender Tricks (Persistence Ban)
*   **No Handlers**: Registration of `bpy.app.handlers` (e.g., `load_post`, `save_pre`, `frame_change_post`) is STRICTLY FORBIDDEN.
*   **No Background Timers**: Unauthorized use of `bpy.app.timers` to create persistent background processes is blocked.

## 13. Idempotence & Read-Before-Write
*   **Atomic Idempotence**: All mutation tools MUST be idempotent. Repeating a request should have no side effects beyond the first successful application.
*   **RBW Loop**: Every mutation must follow the sequence: `Inspect (Tool)` -> `Validate (Logic)` -> `Mutate (Tool)` -> `Verify (Tool)`.
*   **Mandatory Reconciliation**: Before any complex multi-step mutation (e.g., character rigging, scene lighting setup), the AI MUST call `reconcile_state` to sync its internal world-model with the bridge.

## 14. Asset Integrity & Scanning
*   **Mandatory Scan**: All external assets (`.blend`, `.fbx`, `.obj`, `.glb`, etc.) MUST be scanned via `scan_external_asset` before any import or link operation.
*   **No Auto-Run**: The bridge MUST NOT enable Blender's "Auto-run Python Scripts" preference.
*   **Script Block**: Any asset found containing embedded Python `import` or `exec` signatures must be rejected.

## 15. Tool Selection Priority (The Hierarchy)
*   **Level 1: High-Level MCP Tools**: Always prefer `transform_object`, `manage_modifier`, `setup_lighting`, etc. over raw script execution.
*   **Level 2: Atomic Sandbox**: If no high-level tool exists, use `sandbox_modify_object` to test changes on a clone before applying.
*   **Level 3: Low-Level Scripting**: `exec_script` is a last resort and REQUIRES a specific, detailed explanation of why high-level tools were insufficient.

## 16. Failure Recovery & Log Authority
*   **Logs > Inference**: If an operation fails, the AI MUST call `get_blender_errors()` and inspect `logs/vibe_audit.jsonl` BEFORE asking the user or retrying.
*   **Consultation Gate**: No state-changing operation may execute without explicit log consultation and acknowledgment as per [LIFECYCLE_DISCIPLINE.md](./LIFECYCLE_DISCIPLINE.md).
*   **Hardware Awareness**: Respect `ResourceMonitor` blocks. If blocked by `RAM CRITICAL` or `VRAM LOW`, the AI must wait, suggest purging orphans (`purge_orphans`), or downscaling resolutions before proceeding.
*   **Transaction Rollback**: If a transaction fails, `rollback_transaction` MUST be called to restore the last known good state.

## 17. Heartbeat & Progress Monitoring
*   **Heavy Ops**: For long-running operations (Baking, IO, Physics), the AI MUST periodically call `check_heartbeat()` to track the `progress` field.
*   **Activity Gating**: If a command response is delayed, the AI MUST assume the user is performing a manual stroke and wait patiently rather than spamming retries.

## 18. Headless CI/CD Support
*   **Background Detection**: When `get_scene_telemetry()` shows no active windows, the AI MUST avoid viewport-specific commands (e.g., `set_viewport_shading`) and focus on data-only mutations.

## 19. Blender AI Procedural Workflow
*   **Mandatory Adherence**: All AI operations must follow the steps defined in [BLENDER_PROCEDURAL_WORKFLOW.md](./BLENDER_PROCEDURAL_WORKFLOW.md) and the execution order in [BLENDER_PROCEDURAL_FLOW.md](./BLENDER_PROCEDURAL_FLOW.md).
*   **UUID Authoritative**: Names are cosmetic; UUIDs stored in datablock custom properties are the authoritative source of identity.

## 20. Vibe Lifecycle Discipline (Blender)
*   **Safety Protocols**: All operations must strictly follow the lifecycle, IO, and crash recovery rules defined in [LIFECYCLE_DISCIPLINE.md](./LIFECYCLE_DISCIPLINE.md).
*   **Performance Watchdog**: Enforce throttling, debouncing, and yield loops to prevent editor hangs and infinite loop spirals.
*   **Atomic Snapshots**: All mutations require a pre-operation snapshot and must be safe to auto-rollback on any failure.
*   **Unit Normalization**: All transform data must be normalized to SI Meters (1.0 = 1 Meter) before cross-boundary sync.
*   **Object Arbitration**: Agents must claim UUID-level locks; human interaction always breaks an AI lock.
*   **Dependency Pinning**: Scripts must declare dependencies; the bridge must block execution on environment mismatch.
*   **Resource Integrity**: Enforce topology budgets (polygons caps) and cumulative modifier guards to prevent VRAM overflows.
*   **Data Persistence**: Use the "Fake User" shield (`use_fake_user = True`) for all unlinked datablocks to prevent accidental deletion.
*   **Zero Trust IO**: All file IO and asset imports must be treated as untrusted and validated against race conditions.

## 22. TRIPLE-LOCK INVARIANCE MANDATE
*   **Layer 1 (Syntactic)**: All `bpy` API calls MUST be wrapped in `vibe_bridge.execute_blender_command()`.
*   **Layer 2 (Structural)**: `vibe_bridge.execute_blender_command()` MUST validate the command against a whitelist of approved operations.
*   **Layer 3 (Semantic)**: `commit_transaction` requires a technical rationale matching the current state hash (Proof of Work).

## 23. THE DISTRIBUTED PROOF AXIOMS (Second-Order Invariants)
...
*   **Silence is Error**: Lack of an expected signal/heartbeat is a terminal error, not a successful "quiet" state.

## 24. EPISTEMIC INTEGRITY (Third-Order Invariants)
*   **Belief Provenance**: The AI is FORBIDDEN to form stable beliefs without referencing specific WAL indices or state hashes.
*   **Confidence Half-Life**: Any automated "Known Good" classification expires after 12 operations unless re-validated.
*   **Narrative Isolation**: AI "Explanations" are strictly for human review. They MUST NOT be used as inputs for subsequent automated decision loops.
*   **Drift Budgeting**: Protocol deviations (edge cases) are a consumable resource. Exhaustion (2 deviations) requires manual human reset.
*   **Amnesia Mandate**: "Lessons Learned" regarding specific asset failures must carry an expiry (default 30 days) to prevent memory poisoning.

## The Meta-Rule
The AI is not allowed to "fix" invariance violations. Only the machine kernel may perform recovery. The AI's role is to explain, summarize, and escalate.
