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
*   **UUID Authoritative**: Names are cosmetic and volatile in Blender. The AI MUST use the `vibe_uuid` custom property as the primary key for all datablock references (Objects, Meshes, Materials, Armatures).
*   **References**: Never rely on `bpy.data.objects['Name']` without first verifying the `vibe_uuid` matches the expected target. Use `audit_identity` to verify state parity.

## 19. Blender AI Procedural Workflow
*   **Mandatory Adherence**: All AI operations must follow the steps defined in [BLENDER_PROCEDURAL_WORKFLOW.md](./BLENDER_PROCEDURAL_WORKFLOW.md).
*   **Identity Resolution**: Before any mutation, the AI MUST resolve its target by searching for its `vibe_uuid`. If a name collision occurs but UUIDs differ, the UUID is the source of truth.

## 20. Vibe Lifecycle Discipline (Blender)
*   **Safety Protocols**: All operations must strictly follow the lifecycle, IO, and crash recovery rules defined in [LIFECYCLE_DISCIPLINE.md](./LIFECYCLE_DISCIPLINE.md).
*   **Performance Watchdog**: Enforce throttling, debouncing, and yield loops to prevent editor hangs and infinite loop spirals.
*   **Atomic Snapshots**: All mutations require a pre-operation snapshot and must be safe to auto-rollback on any failure.
*   **Unit Normalization**: All transform data must be normalized to SI Meters (1.0 = 1 Meter) before cross-boundary sync.
*   **Object Arbitration**: Agents must claim UUID-level locks; human interaction always breaks an AI lock.
*   **Dependency Pinning**: Scripts must declare dependencies; the bridge must block execution on environment mismatch.
*   **Resource Integrity**: Enforce topology budgets (polygons caps) and cumulative modifier guards to prevent VRAM overflows.
*   **Data Persistence**: Use the "Fake User" shield (`use_fake_user = True`) for all unlinked datablocks to prevent accidental deletion.
*   **Binary Integrity (LFS)**: Large binary assets (.blend, .fbx, .png, etc.) MUST be tracked via Git LFS. Committing raw binaries >1MB is a protocol violation.
*   **Zero Trust IO**: All file IO and asset imports must be treated as untrusted and validated against race conditions.

## 22. TRIPLE-LOCK INVARIANCE MANDATE
*   **Layer 1 (Syntactic)**: All `bpy` API calls MUST be wrapped in `vibe_bridge.execute_blender_command()`.
*   **Layer 2 (Structural)**: `vibe_bridge.execute_blender_command()` MUST validate the command against a whitelist of approved operations.
*   **Layer 3 (Semantic)**: `commit_transaction` requires a technical rationale matching the current state hash (Proof of Work).

## 23. THE DISTRIBUTED PROOF AXIOMS (Second-Order Invariants)
...
*   **Silence is Error**: Lack of an expected signal/heartbeat is a terminal error, not a successful "quiet" state.

## 24. EPISTEMIC INTEGRITY (Third-Order Invariants)
...
*   **Amnesia Mandate**: "Lessons Learned" regarding specific asset failures must carry an expiry (default 30 days) to prevent memory poisoning.

## 25. INVARIANCE AMPLIFIERS (AI Execution Mandate)
*   **Hash-Chained WAL**: All operations are cryptographically chained. Breaking the chain invalidates the session.
*   **Force-Fed Hashes**: AI must acknowledge the force-fed `scene_hash` in every turn.
*   **Action Proof-of-Work**: `commit_transaction` requires a `technical_rationale_check` matching the current engine generation.
*   **Dual-Witness Consensus**: Facts without dual-source verification (Blender + Bridge) are treated as hallucinations.

## 26. ADVERSARIAL PRE-FLIGHT MANDATE
*   **Bootstrap Verification**: The AI MUST call `run_adversarial_preflight` at the start of every session to detect zombie processes and port conflicts.
*   **Self-Healing**: If the pre-flight report shows `safe_to_proceed: false`, the AI MUST prioritize system stabilization (cleaning ports/killing zombies) before any scene mutations.

## The Meta-Rule
The AI is not allowed to "fix" invariance violations. Only the machine kernel may perform recovery. The AI's role is to explain, summarize, and escalate.
