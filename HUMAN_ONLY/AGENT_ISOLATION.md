# The Architecture of Isolation: Multi-Agent Governance

**Objective:** Prevent "Context Poisoning" and engine drift by physically separating AI reasoning into strictly scoped sandboxes.

---

## 1. The Three-Agent Sandbox Model

To operate at scale, the VibeBridge system utilizes three distinct AI instances, each with a strictly scoped mental model:

### 🛡️ Agent Alpha (The Kernel Coordinator)
*   **Scope:** Only sees the Orchestrator/IPC layer.
*   **Rules:** Follows `BRIDGE_PROTOCOL.md` and `LIFECYCLE_DISCIPLINE.md`.
*   **Role:** Manages the Write-Ahead Log (WAL) and decides *what* needs to happen (e.g., "Move Object_01 to B"). It deals exclusively in UUIDs and Intents. It never sees a line of engine-specific code.

### 🎨 Agent Beta (The Blender Specialist)
*   **Scope:** Only sees the `BlenderVibeBridge` MCP.
*   **Rules:** Follows `BLENDER_PROCEDURAL_FLOW.md` and `BLENDER_FLOW.md`.
*   **Role:** Receives high-level intents from Alpha and translates them into precise `bpy` operations. It is oblivious to Unity’s existence.

### ⚛️ Agent Gamma (The Unity Specialist)
*   **Scope:** Only sees the `UnityVibeBridge` MCP.
*   **Rules:** Follows Unity-specific Engineering Constraints and Y-Up/Left-Handed coordinate systems.
*   **Role:** Ensures materials and physics in Unity match the incoming hashes. It is oblivious to Blender’s Z-Up world.

---

## 2. Preventing Context Poisoning

"Context Poisoning" occurs when engine-specific terminology (e.g., "GameObject" vs "DataBlock") leaks into the wrong reasoning chain. We prevent this via three firewalls:

1.  **Protocol-Only IPC**: Messages between agents are filtered. Any mention of Unity-specific terms is stripped before the message reaches the Blender specialist.
2.  **Stateless Specialist Prompts**: Specialists are treated as "Ephemeral Adapters." They receive the **Current State Hash** and the **Target Intent**, fulfilling the contract without needing the full project history.
3.  **The UUID Firewall**: Since all agents use a shared `global_id_map` provided by the Orchestrator, they can reference "Crate_01" without ever sharing the underlying technical handles that cause drift.

---

## 3. Ideal Model Configuration

*   **Kernel (Agent Alpha):** High-context, deep-reasoning model (e.g., Gemini 1.5 Pro / Claude 3.5 Sonnet) to maintain the distributed state model.
*   **Adapters (Beta/Gamma):** Fast, highly-skilled "literalists" (e.g., Gemini 1.5 Flash / Claude 3 Haiku) to execute the freeze-proof patterns.

---

## 4. Implementation Invariants

*   **No Shared History**: Never allow the specialists to see the chat history of the other engine.
*   **Intent-Based Delegation**: The Kernel never sends code; it only sends **Intent Tokens** (e.g., `TRANSFORM`, `RE-RIG`).
*   **Hash Verification**: Success is determined by matching state hashes, never by the AI's verbal assurance.
