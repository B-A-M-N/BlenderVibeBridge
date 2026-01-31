# Technical Architecture: The Governed Kernel

This document details the internal engineering of the Blender VibeBridge.

## 1. The Split-Thread Dispatcher
Blender's Python API (`bpy`) is NOT thread-safe. To avoid crashes, the VibeBridge uses a **Split Architecture**:
1. **The Listener (Background)**: A Python `threading.Thread` runs a `socketserver.TCPServer`. It receives JSON payloads, validates the `X-Vibe-Token`, and pushes commands into a `queue.Queue`.
2. **The Consumer (Main Thread)**: A `bpy.app.timers` function runs every 0.1s. It pops items from the queue and executes them in the main Blender context.

## 2. Context Overrides
Executing operators from a timer often fails because the "Context" (active object, area, region) is null.
* **Solution**: Every `execute_command` call generates a `get_context_override()`. 
* It scans `bpy.context.window_manager` for a `VIEW_3D` area and injects it into the operator call: `bpy.ops.mesh.primitive_cube_add(override)`.

## 3. Epistemic Verification Loop
To prevent the agent from hallucinating, the bridge implements **State Reconciliation**:
* The agent sends its "Expected State" (e.g., "Cube is at 0,0,0").
* The bridge performs a `getattr` lookup and returns an `actual` vs `expected` diff.
* If `SESSION_ID` changes (detected via HTTP headers), the agent is notified that its entire internal world-model is now potentially false and must be refreshed.

## 4. Hardware Safety Railings
The `validate_command` gate acts as a hardware firewall.
* **Subdivision**: Blocks `levels > 3`.
* **Array**: Blocks `count > 50`.
* **Cycles**: Forces `shading_system = 'INTERNAL'` on every mutation to prevent OSL C-code injection.
* **Baking**: Intercepts `resolution` parameters and caps them at 2048px to prevent VRAM overflow.

## 5. Semantic Role Lock
Registry data in `metadata/vibe_registry.json` is used for **Active Enforcement**.
* If an object has a role like `PRIMARY_LIGHT`, the MCP server intercepts `object.delete` requests and returns a `403 Forbidden` before the command even reaches the queue.

## 6. AST Security Gate
The `SecurityGate` class uses Python's `ast` module to walk the tree of any proposed script.
* **Forbidden**: `import os`, `exec()`, `eval()`, `__import__`, and direct `import bpy`.
* **Allowed**: Basic logic, math, and calls to the bridge's own whitelisted helper functions.
