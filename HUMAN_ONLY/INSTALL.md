# 🛠️ BlenderVibeBridge: Technical Engineering & Installation Guide

This guide is intended for **Engineers, Technical Artists, and Power Users**. It provides a deep dive into the bridge architecture, security invariants, and advanced orchestration patterns.

---

## 🏗️ 1. System Architecture Overview

BlenderVibeBridge operates as a **Split-Thread Kernel**:

1.  **The Control Plane (Python/MCP)**: A high-performance middleware that handles AST auditing, token-based authentication, and protocol translation.
2.  **The Execution Plane (Python/Bpy)**: A main-thread consumer that executes mutations via `bpy.app.timers`.

### Architectural Invariants:
- **Main-Thread Dispatch**: All `bpy` calls are executed on the main thread to avoid C-level memory corruption.
- **Context Overrides**: The bridge dynamically generates context overrides to allow operations even when the AI doesn't have an "active" viewport.
- **Atomicity**: One AI request = One Undo step. Complex mutations are wrapped in `begin_transaction` / `commit_transaction`.

---

## 🚀 2. Advanced Installation & Hardening

### Prerequisites
- **Blender**: 3.6 LTS or newer (Recommended).
- **Python**: 3.10+ (Included with Blender, but required for the MCP server).
- **Environment**: Linux/macOS/Windows.

### Deployment Steps
1.  **Kernel Injection (Add-on)**:
    - Zip the `blender_addon/vibe_bridge` directory.
    - Install via Blender: **Edit > Preferences > Add-ons > Install**.
2.  **MCP Server Setup**:
    Initialize the virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r mcp-server/requirements.txt
    ```
3.  **Security Hardening**:
    Enable OS-level isolation via environment variables:
    ```bash
    USE_BWRAP=true ./start_bridge.sh
    ```

---

## 🧠 3. Advanced Epistemic Governance

To prevent "AI Psychosis" at an engineering level, the bridge implements **Truth Reconciliation Loops**.

### A. Forensic Hashing
The kernel generates a scene hash (topology + transforms) pre- and post-mutation.
- **Verification**: If the `post_hash` doesn't match the expected delta, the transaction is flagged for human review.

### B. System Console Streaming
The AI has access to the Blender System Console (stdout/stderr).
- **Tool**: `get_blender_errors`
- **Pattern**: If a `bpy` operator returns `CANCELLED`, the AI pulls the last 50 lines of the console to find the raw Python traceback.

---

## 🛠️ 4. Transactional Mutation Mastery

### Atomic Transactions
Multi-step operations (like character rigging) should be wrapped in transactions to prevent partial scene corruption.
```json
{
  "intent": "RIG",
  "commands": [
    {"tool": "add_armature", "args": {"name": "MainRig"}},
    {"tool": "manage_vertex_groups", "args": {"target": "Body", "action": "CREATE"}}
  ]
}
```
*If the vertex group creation fails, the `rollback_transaction` tool will automatically remove the newly created Armature.*

---

## 🛡️ 5. Security & AST Auditing

The `security_gate.py` uses **Recursive AST Parsing** to block malicious payloads. 

### Custom Whitelisting
If you need to allow a specific "Risky" call (e.g., `import requests`), you must manually sign the script:
1. Attempt the operation (it will be blocked).
2. Run: `python3 mcp-server/security_gate.py --trust avatar_scripts/your_script.py`
3. The SHA-256 fingerprint is added to `metadata/trusted_signatures.json`.

---

## 📊 6. Performance & Hardware Sentinel

### Resource Monitoring
The bridge monitors system RAM and VRAM.
- **Automatic Gating**: If VRAM exceeds 90%, the bridge will block `bake_op` or `subdiv_op` requests until memory is freed.
- **Orphan Purge**: Use `purge_orphans` to clear unreferenced Mesh and Material data-blocks.

---

## 💀 7. Debugging the Bridge

| Symptom | Diagnosis | Solution |
| :--- | :--- | :--- |
| **RuntimeError: Context is incorrect** | Background thread mutation | Ensure the `bpy.app.timers` loop is running. |
| **Security Block: Forbidden module** | AST Gate Rejection | AI attempted unauthorized `import os` or similar. |
| **Mutation Timeout** | Main thread hang | Check if a Blender popup (e.g., Save confirmation) is blocking execution. |

---
**Created by the Vibe Bridge Engineering Team.**
