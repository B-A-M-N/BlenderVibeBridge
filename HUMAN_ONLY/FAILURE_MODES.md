# BlenderVibeBridge: Failure Modes & Recovery Protocols

This document defines the canonical taxonomy of failures within the Bridge/Kernel cluster and the required response for each.

---

## 🟥 1. Terminal Failures (Immediate PANIC)
*Definition: Any failure that compromises state integrity or trust boundaries.*

| Failure | Cause | Protocol |
| :--- | :--- | :--- |
| **Contract Violation** | MCP server sends malformed JSON. | Instant **HALT**; Return 500; Log to Audit. |
| **Security Breach** | Blocked pattern (e.g., `import os`) detected. | Instant **HALT**; Set bridge to `READ_ONLY`. |
| **Deadlock** | Main-thread timer timeout (>15s). | Trigger **Circuit Breaker**; Invalidate Session. |
| **Sandbox Leak** | Attempt to access `HUMAN_ONLY/`. | Mechanical Rejection; Log Critical Violation. |

---

## 🟨 2. Recoverable Failures (Auto-Rollback)
*Definition: Operational errors that can be reverted via the Undo system.*

| Failure | Cause | Protocol |
| :--- | :--- | :--- |
| **Mutation Fail** | `bpy` exception during tool call. | Execute `rollback_transaction`; Notify AI. |
| **Guard Block** | Mutation attempted during file load/save. | Abort; AI MUST wait for bridge `Ready` status. |
| **Sanity Fail** | GPU/VRAM limit exceeded (e.g. Subsurf > 3). | Mechanical Rejection; Error returned to AI. |
| **Identity Drift** | Target `bpy.data` pointer no longer valid. | Trigger **Re-Discovery** via `bpy.data` name lookup. |

---

## 🟦 3. Truth Reconciliation
*Definition: Protocol for when the "Numerical Truth" of the scene is in doubt.*

1.  **Halt**: If a tool fails due to a missing data block, the AI **MUST NOT** attempt to "re-invent" the object.
2.  **Inspect**: AI must call `get_scene_telemetry` to verify current scene state.
3.  **Audit**: If multiple errors occur, the AI must call `get_blender_errors` to see the actual System Console output before retrying.

---

## 🛠️ Human Intervention Policy
Human intervention is mandatory **ONLY** when:
- The Kernel is in an `Error` state (Requires addon restart).
- A `Terminal Failure` is logged in the `vibe_audit.jsonl`.
- The AI has attempted 3 re-discovery loops without finding the target.

---

## 📝 Case Study: The "Hallucinated Purge" Scenario

**The Scenario**: An AI Agent is tasked with "cleaning up" a character scene. Due to a model hallucination or a malformed regex, the agent identifies the `Armature` object as "temporary junk" and attempts to delete it.

In a naive implementation, the bridge would execute `bpy.data.objects.remove(armature)`, immediately corrupting the character's skeletal structure and breaking vertex group dependencies beyond a simple fix.

### Why it fails safely in BlenderVibeBridge

1.  **Safe Deletion Semantics (The Actuator Lock)**:
    *   **Mechanism**: The server maintains a session-based registry of agent-created objects.
    *   **Result**: When the agent calls `delete("Armature")`, the bridge checks if that object name was created by the agent in the current session.
    *   **Outcome**: The bridge returns a `Security Block: Cannot destroy an object not created by the agent.` error. The mutation is blocked at the gate.

2.  **Transactional Bounding (The Blast Shield)**:
    *   **Mechanism**: All multi-step operations are wrapped in `begin_transaction` / `commit_transaction`.
    *   **Result**: Even if a minor (allowed) deletion occurred before the hallucinated purge, the bridge can invoke `bpy.ops.ed.undo()`.
    *   **Outcome**: Blender's Undo system reverts the scene to the exact state before the transaction began.

3.  **Capability Discovery (The Safety Manual)**:
    *   **Mechanism**: `audit_identity`
    *   **Result**: A well-behaved agent calls this first. The bridge returns `type: ARMATURE`, `is_proxy: false`.
    *   **Outcome**: The agent recognizes that deleting this object is a high-risk operation and avoids it.

4.  **Read-Only Mode (The Kill Switch)**:
    *   **Mechanism**: `KILL_VIBE` environment variable or `readonly` mode.
    *   **Outcome**: All subsequent mutation attempts return `403 Forbidden`, freezing the agent in an observation state until a human intervenes.

---
**Copyright (C) 2026 B-A-M-N**
