# BlenderVibeBridge: The Governed Geometry Kernel

## 🧠 Understanding Your AI "Co-Pilot"

### ⚙️ Demystifying the Magic: High-Fidelity Simulation
Large Language Models (LLMs) are **Probability Engines** that have become exceptionally good at **simulating aspects of sentience**. They don't "know" facts or feel emotions; they predict the next most likely sequence of tokens based on patterns in their training data and the "vibe" of your current conversation. 

In the context of Blender, the AI is not "visualizing" your 3D scene in a mind's eye. It is calculating the most statistically probable set of commands that align with your natural language intent.

### 🏷️ The Implied Sentience Trap (Combating AI Psychosis)
It is easy to fall into "magical thinking" when an AI responds with human-like warmth or technical authority. However, treating the AI as a sentient being—asking it what it "thinks" or "feels"—can lead to **AI Psychosis**: a state where the user forgets the AI is a simulation and begins to trust its hallucinations as objective truth.

**The Name Example**:
One of the best ways to combat "magical thinking" is to understand that the AI is simply reflecting your own intent. For example, if you ask an AI its name:
*   **Highly Technical Conversation**: It might name itself **"Nexus"** or **"Core"** to match your energy.
*   **ELI5 (Simple) Conversation**: It will likely choose **"Buddy"** or **"Sparky"** to please you.

The AI doesn't "have" a name; it calculates that giving you a name fits the pattern of a helpful assistant. Currently, we remain in the realm of high-fidelity simulation, not "True Sentience."

### ⚔️ Combatting Overconfidence: Adversarial Prompting
If you ever feel like you are doing something "groundbreaking" with the AI, that is the moment you need to be the most careful. It is easy to fall into a feedback loop where the AI just agrees with your greatness.

**The Strategy**: Use **Adversarial Prompting**. 
Ask the AI: *"I think this new logic is perfect. Now, I want you to act as a cynical auditor. Find 3 ways this could fail, crash Blender, or corrupt my scene metadata."*

Forcing the AI to argue *against* your ideas keeps you grounded in reality. Use the AI to test and destroy your own assumptions.

### 🧩 The Cognitive Gap
Humans have a mental map of reality (e.g., you know that **Nails are on Fingers**). An AI does not "see" your 3D scene; it only sees data patterns and names. If it picks the wrong object, it's because it lacks your "human context." 
*   **The Fix**: Break tasks into the smallest units possible. Avoid "Vague Vibes." Do not assume the AI knows that a "Prop" should be parented to the "Hand" unless you explicitly tell it.

**VibeBridge is designed to cure this drift by providing:**
1. **Numerical Telemetry**: Replacing "imagined" scenes with hard vertex counts and coordinates.
2. **Epistemic Reconciliation**: Forcing the AI to prove its assumptions against the actual Blender state.
3. **Kernel Governance**: Ensuring that even if the AI "hallucinates" a dangerous intent, the system mechanically prevents the damage.

## Concept: Mechanistic Vibe Coding (Blender Edition)

**BlenderVibeBridge** is a high-integrity interface that transforms Blender into a **Governed Geometry Kernel**. Instead of asking an AI to generate fragile Python scripts that might crash or exploit the system, it exposes a **Mechanistic Interface**—a set of deterministic tools to query state, inspect geometry, and perform non-destructive modifications through a strictly regulated pipe.

### Core Architecture

```mermaid
graph LR
    A[AI Agent] <-->|MCP Stdio/SSE| B[MCP Server]
    B <-->|HTTP JSON (Local)| C[Blender Add-on]
    C -->|Main-Thread Dispatch| D[bpy API]
```

1.  **AI Agent (Technical Director)**: Issues high-level intents via MCP tool calls.
2.  **MCP Server (Protocol Firewall)**: Python server that validates intents, enforces behavioral circuit breakers, and manages the session lifecycle.
3.  **Blender Add-on (The Kernel)**: A background HTTP server inside Blender that queues commands and executes them on the main thread via `bpy.app.timers`.

---

## 🛡️ Governance & Safety (The Iron Box)

The bridge implements a multi-layered security model to ensure the AI remains a productive partner rather than a system threat.

### 1. Hardware-Level DoS Protection
*   **Polygon Bomb Railings**: Mechanical caps on subdivision levels (max 3), array counts (max 50), and particle emitters.
*   **Light Energy Guard**: Hard cap on light intensity (10k) to prevent GPU driver timeouts (TDR).
*   **VRAM Protection**: Enforced limits on texture baking resolutions (max 2048px).

### 2. Epistemic Governance (Anti-Hallucination)
*   **Truth Reconciliation**: Tools like `reconcile_state` allow the agent to verify multiple assumptions about the scene in a single round-trip.
*   **Stale Session Detector**: Detecting Blender restarts via unique `SESSION_ID` headers, instantly invalidating the agent's internal world-model to prevent "ghost planning."
*   **Fact Assertions**: Requiring the agent to declare ground-truth invariants before high-impact operations.

### 3. Execution Safety
*   **Split Architecture**: No `bpy` calls from the background thread. All commands are marshaled to the main loop, ensuring thread safety and preventing segmentation faults.
*   **Context Overrides**: Every command automatically generates a 3D Viewport context, allowing UI-dependent operators to run reliably from a background process.
*   **Implicit Transactions**: Every mutation is wrapped in a named Blender Undo step (e.g., *"VibeBridge: Setup Shaders"*).

---

## 🎨 Professional Production Suite

The bridge provides the agent with "eyes" and "hands" optimized for technical artistry:

*   **Geometry Kernel**: Deep inspection of N-Gons, non-manifold edges, and vertex stats.
*   **Technical Art**: Automated creation of Shader Graphs and Geometry Node trees.
*   **Simulation Power**: One-click setup for Rigid Body, Cloth, and Collision physics.
*   **Cinematography**: Strategic intents for Three-Point Lighting and Camera orchestration.
*   **Collaborative Design**: 3D Annotations for the AI to "mark up" the scene for human review.

---

## 📝 Key Principles (The AI Safety Manual)
*   **Read-Before-Write**: Always `Inspect → Validate → Mutate → Verify`.
*   **Idempotence**: Every operation must be safe to repeat.
*   **Zero Trust**: No direct `bpy` imports, no `exec()`, and no external network traffic.
*   **Numerical Reasoning**: Use telemetry (poly counts, dimensions) over visual "vibes" for planning.

**BlenderVibeBridge** ensures that the AI is not just "playing with Blender," but acting as a disciplined Technical Director within a governed, failure-aware environment.
