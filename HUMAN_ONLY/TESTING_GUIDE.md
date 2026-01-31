# VibeBridge Testing & Validation Guide

**Objective:** Ensure all mutations are deterministic, undo-safe, and security-hardened.

---

## 1. Unit Testing (Blender Python)

All new `avatar_scripts` or Kernel modifications must have a corresponding test case in `security_tests/`.

### Running Tests (Headless)
```bash
blender -b -P security_tests/run_suite.py
```

### Key Assertions
*   **Idempotence**: Running the same tool twice results in zero net change after the first application.
*   **Undo-Cleanliness**: `bpy.ops.ed.undo()` restores the scene hash to exactly the pre-mutation state.
*   **Identity Survival**: UUIDs persist after file reloads (`wm.open_mainfile`).

---

## 2. Integration Testing (MCP + Bridge)

### The Handshake Test
1.  Run `./start_bridge.sh`.
2.  Send the `get_scene_telemetry` command via an MCP client.
3.  Verify the `session_id` matches the current Blender session.

### Stress Testing (Event Storms)
Rapidly send 50+ `transform_object` commands. Verify that the **Performance Watchdog** in `LIFECYCLE_DISCIPLINE.md` correctly throttles the execution and prevents a Blender hang.

---

## 3. Security Regression (The Iron Box)

### Forbidden Call Audit
The `security_gate.py` must be tested against malicious scripts:
```python
# Test Case: Should be BLOCKED
import os
os.system("rm -rf /")
```

### Resource Boundary Test
Attempt to add a `Subsurf` modifier with 10 iterations. Verify that the **Hardware Sentinel** rejects the operation before VRAM overflow occurs.

---

## 4. Golden Set Regression (GSR)

When tuning complex rigging or optimization logic:
1.  Run the tool on a known reference model (the "Golden Asset").
2.  Compare the resulting `poly_count.txt` and `vgroup_names.txt` against the baseline.
3.  Any deviation > 0.01% requires a technical audit.

---

# THE FINAL GATE
No PR shall be merged without a green `vibe_audit.jsonl` log from the integration test suite.
