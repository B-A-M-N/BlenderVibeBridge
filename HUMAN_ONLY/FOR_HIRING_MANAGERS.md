# 👔 For Hiring Managers: Engineering Audit & Systems Design

If you are evaluating this repository for a technical role, this document provides a high-level audit of the architectural decisions, security invariants, and systems engineering principles implemented in **BlenderVibeBridge**.

---

## 🏛️ 1. Control-Plane vs. Execution-Plane Separation
The core innovation of this project is the strict decoupling of **AI Intent** from **Blender Execution**.
*   **The Problem**: LLMs are non-deterministic. Allowing them to execute raw Python scripts inside Blender is a critical security risk and leads to "hallucination drift" where the AI loses track of the scene state.
*   **The Solution**: We implemented a **Mechanistic ISA (Instruction Set Architecture)**. The AI issues high-level JSON "Intents" (e.g., `run_op`, `transform`). These are validated by a Python middleware and then dispatched to a Blender Kernel that executes them via `bpy.app.timers`.
*   **Engineering Impact**: This ensures that even if the AI "hallucinates," it can only express actions within the bounds of the provided toolset.

## 🛡️ 2. Adversarial Security & "Iron Box" Isolation
BlenderVibeBridge treats the AI as an **untrusted operator**.
*   **Recursive AST Auditing**: Before any payload is accepted, the middleware performs a recursive Abstract Syntax Tree (AST) scan. It blocks high-risk modules (`os`, `subprocess`, `socket`) and patterns (obfuscated code, `exec()`) that could be used to bypass the bridge.
*   **Token-Based Auth**: Communication is authenticated via a session-specific token (`X-Vibe-Token`).
*   **Airlock Plane**: Commands are passed through a file-based queue (`vibe_queue/inbox`) to isolate the main Blender process from the HTTP server thread, preventing memory corruption.

## ⚛️ 3. Transactional State Mutation (Atomic Undo)
Blender's state can be easily corrupted by malformed scripts.
*   **Mechanism**: Every AI request is wrapped in a single, atomic Blender Undo step (`bpy.ops.ed.undo_push`). 
*   **Failure Protocol**: On any exception, the Kernel catches the error, logs it to `vibe_audit.jsonl`, and can trigger an immediate rollback.
*   **Outcome**: One AI Intent = One Clean Undo Step. This prevents "ghost data" or scene rot.

## 🏃 4. Main-Thread Dispatching & UI Stability
Blender's API (`bpy`) is not thread-safe.
*   **The Consumer Loop**: The Kernel runs as a `bpy.app.timers` function on the main thread. It "consumes" the airlock queue every 0.1s, ensuring all mutations happen safely without crashing the Blender UI.
*   **Resource Monitoring**: The bridge monitors system RAM and VRAM, automatically blocking memory-heavy operations (like Subsurf or Baking) if resources are critical.

## 🧠 5. Epistemic Governance (Truth Reconciliation)
To solve the "Blind AI" problem:
*   **Forensic Hashing**: The kernel generates scene hashes pre- and post-mutation. This forces the AI to prove its assumptions against numerical reality.
*   **Telemetry Feedback**: The AI has access to the Blender System Console. If an operation fails, it pulls the raw traceback to self-correct its logic.

---

## 🛠️ Tech Stack Summary
- **Language**: Python (Full Stack: Middleware & Blender Kernel).
- **Security**: AST Parsing, Token-Auth, Airlock Pattern.
- **Architecture**: Split-Thread Consumer model.
- **Stability**: Main-thread Timer loops, Atomic Transactions.

**Conclusion**: This repository demonstrates **Governance Engineering**. It provides a blueprint for how to deploy powerful, non-deterministic models into high-stakes, stateful environments like 3D production pipelines safely and efficiently.
