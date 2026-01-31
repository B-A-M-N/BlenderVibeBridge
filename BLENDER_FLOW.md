# BLENDER VIBE BRIDGE: SERVER FLOW & LIFECYCLE

**Objective:** Maintain a deterministic, non-blocking IPC state machine between Blender and the external VibeBridge Server.

---

## 1. STARTUP SEQUENCE (Bootstrap)
1.  **Addon Registration**: `register()` is called. 
2.  **Identity Verification**: UUID registry is loaded from `.blend` and sidecar.
3.  **IPC Initialization**: Non-blocking socket/pipe is opened.
4.  **Timer Heartbeat**: `bpy.app.timers` starts the `vibe_bridge.poll` loop.
5.  **Handshake**: Bridge sends `SYNC_READY` with `session_id` to the server.

---

## 2. THE POLLING LOOP (Heartbeat)
*   **Frequency**: 10Hz - 20Hz (Capped by `ResourceMonitor`).
*   **Tasks**:
    1. Check for incoming IPC messages.
    2. Monitor `bpy.context` for user interaction (Pause if active).
    3. Update `vibe_health.json` with current telemetry.
    4. Detect `domain_reload` or `undo` events to trigger re-indexing.

---

## 3. COMMAND EXECUTION (The Transaction)
1.  **Ingress**: Server sends a command (e.g., `transform_object`).
2.  **Validation**: `security_gate.py` audits the Python intent.
3.  **Snapshot**: Pre-mutation scene hash and UUID state are recorded.
4.  **Dispatch**: Operation is executed via a modal operator or direct API.
5.  **Acknowledge**: Result and delta-hash are sent back to the server.

---

## 4. FAILURE RECOVERY
*   **Connection Lost**: The loop enters `RECONNECT` mode (Exponential backoff).
*   **Blender Freeze**: `KILL_VIBE` environment variable is checked to force-stop.
*   **Invalid State**: If UUID collision is detected, sync is frozen until `reconcile_state` is called.

---

## 5. SHUTDOWN (Cleanup)
1.  **Deregistration**: `unregister()` is called.
2.  **Handle Disposal**: All persistent timers and sockets are explicitly closed.
3.  **Tombstoning**: Final registry state is persisted to sidecar.
