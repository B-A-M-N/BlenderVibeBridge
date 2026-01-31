# BlenderVibeBridge Security & Architecture

This document outlines the security measures, architectural invariants, and safety features implemented to ensure a secure environment for AI-assisted Blender development.

## 🛡️ The "Iron Box" Safety Model

Security is moved from **Instructions** (which an agent can ignore) to **Infrastructure** (which an agent cannot change).

### 1. The Security Gate (Static Analysis)
Every Python script proposed by the AI passes through a robust auditor (`security_gate.py`) that uses **AST (Abstract Syntax Tree)** parsing.

*   **Python AST Audit:**
    *   **Forbidden Modules:** Hard blocks `os`, `subprocess`, `socket`, `pty`, and `requests`.
    *   **Direct Bpy Block**: AI is discouraged from direct `import bpy` and encouraged to use high-level tools.
    *   **Network Firewall:** The bridge only binds to `localhost` (127.0.0.1) and rejects external traffic.

### 2. Main-Thread Dispatcher
Blender's API is not thread-safe.
*   **The Airlock**: Commands are received on a background thread and pushed to a `queue`.
*   **The Consumer**: A `bpy.app.timers` function consumes the queue every 0.1s, ensuring all mutations happen safely on Blender's main thread.

### 3. Hardware Railings (DoS Prevention)
To prevent the AI from crashing Blender via high-density mesh operations:
*   **Modifier Caps**: Hard limits on `SUBSURF` (3 levels) and `ARRAY` (50 count).
*   **Bake Resolution**: Textures are capped at 2048px.
*   **Energy Limits**: Light energy capped at 10,000 to prevent viewport blowout.

### 4. Transactional Integrity
*   **Atomic Blocks**: All multi-step operations are wrapped in `begin_transaction` / `commit_transaction`.
*   **Blender Undo**: The bridge uses Blender's native `bpy.ops.ed.undo_push()` to ensure a single AI action corresponds to exactly one undo step.

---

## 🛠️ Security Mandates
All AI agents must adhere to the rules in `AI_ENGINEERING_CONSTRAINTS.md`:
- **Zero-Trust**: No dynamic code execution (`eval`, `exec`) on the host.
- **Read-Before-Write**: Mandatory state verification before mutation.
- **Localhost Only**: Strictly local communication.

## Security Commandments
1.  **Never run the bridge as a root/admin user.**
2.  **Keep the `security_gate.py` outside of the AI's write-access.**
3.  **Always verify scene state via `reconcile_state` after heavy mutations.**

---
**Copyright (C) 2026 B-A-M-N**
