# 🛡️ MCP Blender Control Plane: The Operating System

**Core Philosophy:** Blender is a hostile, non-deterministic environment. The MCP must act as an **Operating System**, managing state, memory, and execution context to prevent silent corruption.

---

## 1. 🧬 The Kernel Tier (Deep Safety Primitives)
**Objective:** Prevent TOCTOU bugs, race conditions, and context poisoning.

### 🔒 Context & Selection Guard
*   **Mechanism:** `with ContextGuard():` wrapper for all operations.
*   **Function:** Snapshots active object/selection before op, forces restore after.
*   **Defense:** Prevents "bleed" where an operation leaves the wrong object selected, poisoning the next command.

### 🛑 TOCTOU Protection (Time-of-Check to Time-of-Use)
*   **Mechanism:** State Hash Locking.
*   **Function:** Calculate hash of target object (verts + transform) *during validation*. Verify hash matches *immediately before execution*.
*   **Defense:** Aborts if the scene changed between the "Plan" and "Act" phase.

### ⚡ NaN & Infinity Watchdog
*   **Mechanism:** Deep Scan.
*   **Function:** Scans transforms, bone rolls, and shape keys for `NaN` or `inf` values.
*   **Defense:** Prevents "exploding rig" syndrome where corrupt math propagates silently.

### ✅ Mode Transition Airlock
*   **Mechanism:** Explicit Mode Gates + Rubber-Banding.
*   **Function:** Never assume mode. Force `bpy.ops.object.mode_set(mode='OBJECT')` before mutation, then restore the original Sculpt/Edit mode if mesh integrity is preserved.
*   **Defense:** Prevents crashes and flow interruptions.

---

## 2. 🧱 The Filesystem Tier (Data Integrity)
**Objective:** Manage datablocks like inodes.

### 🧹 Orphan & Dependency Manager
*   **Tool:** `audit_external_dependencies()`
*   **Function:** Checks for missing textures/linked libraries before they become invisible.
*   **Tool:** `purge_orphans_deterministic()`
*   **Function:** Hard cleanup of unused blocks to prevent file bloat.

### 📄 Export Contract
*   **Mechanism:** Strict Schema Validation.
*   **Function:** Rejects export if: `Scale != 1.0`, `Rot != 0`, `N-Gons > 0`, `Bone Names != Standard`.
*   **Defense:** Fails fast in Blender, not slowly in Game Engine.

---

## 3. 🛡️ The Application Tier (Recovery)
**Objective:** Undo, Redo, and Crash Recovery.

### ⚛️ Atomic Execution Wrapper (Implemented)
*   **Function:** Wraps scripts in `Undo Push` -> `Try` -> `Undo (on Fail)`.
*   **Status:** **ACTIVE**.

### 🧹 The Janitor (Implemented)
*   **Tool:** `reset_material_standard`.
*   **Status:** **ACTIVE**.

### 🚑 Safety Checkpoints (Implemented)
*   **Tool:** `create_safety_checkpoint`, `save_as_new_copy`.
*   **Status:** **ACTIVE**.

---

## 4. 🔄 The Atomic Save-Game Loop (Execution Mandate)
**Objective:** Absolute forensic traceability and reversible orchestration.

Every AI Turn MUST follow this loop. Skipping steps is a protocol violation.

1.  **Handshake**: `check_heartbeat()` + `get_state_hash()`.
2.  **Open Transaction**: `begin_transaction()`.
3.  **Mutate**: Execute high-level tools or `exec_script`.
4.  **Close Transaction**: `commit_transaction()` with rationale and hash.
5.  **Ghost Audit**: `git --git-dir=.git_safety --work-tree=. add .` && `git --git-dir=.git_safety --work-tree=. commit -m "..."`.
6.  **Verify Integrity**: `python3 mcp-server/security_gate.py --integrity`.

---

## 🚀 Implementation Roadmap

1.  **Phase 1 (Complete):** Atomic Wrapper, Checkpoints, Janitor.
2.  **Phase 2 (Immediate):** **ContextGuard** (Selection Defense) & **NaN Scanner**.
3.  **Phase 3 (Next):** Export Contracts & Dependency Auditing.