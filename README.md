# 🌌 BlenderVibeBridge

> [!WARNING]
> **EXPERIMENTAL & IN-DEVELOPMENT**  
> This project is currently an active research prototype. APIs, security protocols, and core logic are subject to rapid, breaking changes. This software performs mutations on 3D scenes; **MANDATORY BACKUPS** are required before use.

### The "One-Click" Technical Director for 3D Creation & Mastery
*A production-grade AI control interface for deterministic, undo-safe Blender operations.*

**BlenderVibeBridge lets external tools and AI systems control Blender safely, without giving them unrestricted Python access.** 

It is a professional-grade intelligent interface that transforms Blender into a **Governed Geometry Kernel**. It allows AI agents to interact safely, deterministically, and artistically with Blender’s core engine—turning natural language intents into professional production operations.

| **Capability** | **Feature** |
| :--- | :--- |
| 🛡️ **Iron Box** | Zero-trust security via AST Auditing, Behavioral Circuit Breakers, and local binding. |
| ⚛️ **Kernel Integrity** | Real-time invariant enforcement (No negative scales, no non-manifold geometry). |
| 🏃 **Stable Motion** | Thread-safe main-loop dispatching via `bpy.app.timers` (No crashes). |
| 🧠 **Epistemic Control** | Truth-reconciliation tools that prevent AI hallucinations about scene state. |

### 🎯 Target Audience
*   **Technical Directors & Pipeline Engineers** seeking secure AI automation.
*   **AI Systems Researchers** exploring governed LLM-to-tool interfaces.
*   **3D Content Creators** who want to use AI without risking scene corruption.

## ⚡ Quick Start (Usage at a Glance)
1.  **Install Addon**: Zip `blender_addon/vibe_bridge` and install via Blender Preferences.
2.  **Enable**: Check the box for "System: BlenderVibeBridge".
3.  **Connect AI**: Point your MCP-compatible AI tool (Goose, Claude Desktop) to `mcp-server/server.py`.
4.  **Run Server**: Execute `./start_bridge.sh`.
5.  **Prompt**: Ask your AI to "Check my Blender scene" to verify the handshake.

---

🔰 **Not Technical? Start Here!**  
If you’re new to AI-assisted Blender workflows, don’t worry. We’ve created a **[Complete Beginner's Manual](HUMAN_ONLY/FOR_BEGINNERS.md)** that explains everything step by step, from setup to safe usage.

---

---

## 🖼️ Previews

| **Blender Bridge Interface & Operation** |
| :---: |
| ![Surgical Optimization Scan](Screenshot%20from%202026-01-28%2023-51-24.png) |

---

## ⚠️ Read This First (Why This Exists)

**BlenderVibeBridge** is not a toy, a prompt wrapper, or a "magic AI button." 

It is a **reference implementation of AI-assisted systems design** in a high-fidelity, stateful environment. It allows Large Language Models (LLMs) to safely operate inside Blender without risking scene corruption, data exfiltration, or runaway execution.

This project answers a critical engineering question: 
> *How do you let an AI act inside a complex, stateful application—without trusting it?*

**The answer is: You don’t. You constrain it.**

---

## 🧠 What This Project Demonstrates (For Engineers & Hiring Managers)

If you are evaluating this project as an engineer or hiring manager, this repository is a working demonstration of **AI Systems Engineering**:

*   **Control-Plane vs. Execution-Plane Separation**: LLMs generate *intent* (Mechanistic Intents), never raw code execution.
*   **Iron Box Security**: Hardened via local binding, static AST auditing, and header-based heartbeats.
*   **Transactional State Mutation**: Every operation is wrapped in undo-safe, atomic blocks. **One AI request = One Undo step.**
*   **Deterministic Asset Manipulation**: Control over material slots, colors, and hierarchies is handled mechanistically, eliminating the fragility of raw scripts.
*   **Truth Reconciliation Loop**: Tools like `reconcile_state` allow the agent to verify multiple assumptions about the scene in a single round-trip.

---

## 🛠️ Complete Tool Reference (Exhaustive)

### 1. 🧠 Epistemic & Cognitive Governance (Anti-Hallucination)
*   **`reconcile_state`**: Forces the agent to verify its assumptions against actual Blender state.
*   **`assert_scene_facts`**: Declares and verifies ground-truth facts before high-impact mutations.
*   **`request_human_confirmation`**: Pauses for human arbitration on value-judgments or destructive acts.
*   **Stale Session Guard**: Automatically invalidates beliefs if Blender restarts (SESSION_ID tracking).

### 2. 🛡️ Kernel & Integrity (The Guardrails)
*   **`validate_scene_integrity`**: Checks for scale sanity, missing cameras, and empty meshes.
*   **`get_mesh_metrics`**: Numerical analysis of N-Gons, non-manifold edges, and vertex counts.
*   **`manage_object_locks`**: Granular axis locking (Loc/Rot/Scale) and "Freeze" (hidden/unselectable) modes.
*   **`begin_transaction`**: Atomic Undo/Redo block labeling for complex sequences.

### 3. 🏗️ Scene Manipulation & Strategic Intent
*   **`execute_strategic_intent`**: Runs "Compiled Recipes" (e.g., `BLOCKOUT_HUMANOID`, `THREE_POINT_LIGHTING`).
*   **`add_primitive`**: Spawns Cubes, Spheres, or Monkeys.
*   **`transform_object`**: Precise location, rotation, and scale adjustments.
*   **`select_objects`**: Manages selection sets (`ALL`, `NONE`, or by name).
*   **`manage_collection`**: Organizes objects into collections.

### 4. 🎨 Technical Art, Nodes & Surfacing
*   **`manage_material`**: Create and assign materials.
*   **`manage_nodes`**: Build **Shader Graphs** and **Geometry Node** trees (Add & Link).
*   **`manage_modifier`**: Configure `SUBSURF`, `ARRAY`, `BOOLEAN`, etc., with hardware safety caps.
*   **`trigger_bake`**: Automated texture baking (Capped at 2048px).
*   **`process_mesh`**: shade smooth/flat, subdivide, and object joining.

### 5. 🏃 Animation, Physics & Mechanical Logic
*   **`set_animation_keyframe`**: Inserts keyframes for transforms across the timeline.
*   **`apply_physics`**: Sets up Rigid Body, Cloth, or Collision simulations.
*   **`manage_constraints`**: Rigging tools like `TRACK_TO`, `FOLLOW_PATH`, and `COPY_LOCATION`.
*   **`create_procedural_curve`**: Spawns 3D Bezier splines from coordinate lists.
*   **`manage_vertex_groups`**: Sets up groups for character rigging and weight painting.

### 6. 🎬 Production, Visuals & Audio
*   **`setup_lighting`**: Points, Suns, Spots, and Area lights with safety energy caps (10k).
*   **`manage_camera`**: Dynamic camera creation and active view control.
*   **`set_world_background`**: Sets the global environment color.
*   **`set_viewport_shading`**: Switches between Wireframe, Solid, Material, and Rendered.
*   **`take_viewport_screenshot`**: High-speed visual feedback for the agent.
*   **`setup_spatial_audio`**: Places 3D Speaker objects with secure audio path validation.

### 7. 🔗 Pipeline & Infrastructure
*   **`import_export_asset`**: Safe data flow for FBX, OBJ, STL, and GLB files.
*   **`link_external_library`**: Professional multi-file asset linking.
*   **`create_3d_annotation`**: 3D markup for AI-to-Human communication.
*   **`secure_write_file`**: AST-validated Python/C# file writing.

## 📚 Documentation & Governance

To maintain a secure and deterministic environment, this project follows strict operational doctrines. Please refer to the following documentation for setup, security, and philosophical guidance:

### 🐣 For Beginners
*   **[The Complete Beginner's Manual](HUMAN_ONLY/FOR_BEGINNERS.md)**: A step-by-step guide to setting up Blender, Python, and the AI bridge.
*   **[For Hiring Managers](HUMAN_ONLY/FOR_HIRING_MANAGERS.md)**: Engineering audit and systems design overview for technical recruiters.

### 🛠️ For Engineers & Power Users
*   **[Technical Installation Guide](HUMAN_ONLY/INSTALL.md)**: Deep dive into architecture, AST auditing, and main-thread dispatching.
*   **[Technical Architecture](HUMAN_ONLY/TECHNICAL_ARCHITECTURE.md)**: Details on the split-thread consumer model and context overrides.
*   **[Coordinate Systems & Normalization](HUMAN_ONLY/COORDINATE_SYSTEMS.md)**: Formulas for Vibe-Meters and Axis Translation.
*   **[Testing & Validation Guide](HUMAN_ONLY/TESTING_GUIDE.md)**: Procedures for Unit, Integration, and Security testing.
*   **[AI Engineering Constraints](AI_ENGINEERING_CONSTRAINTS.md)**: The "AI Constitution" — non-negotiable safety and structural rules.
*   **[Blender AI Procedural Workflow](BLENDER_PROCEDURAL_WORKFLOW.md)**: Mandatory procedural steps for identity and state management.
*   **[Blender AI Procedural Flow](BLENDER_PROCEDURAL_FLOW.md)**: Absolute execution order for AI operations in Blender.
*   **[Vibe Lifecycle Discipline](LIFECYCLE_DISCIPLINE.md)**: Final safety addendum for lifecycle and IO integrity.
*   **[ISA Specification](ISA_SPEC.md)**: The Instruction Set Architecture (Opcodes and Intent Binding).
*   **[Blender Kernel Tool Inventory](MCP_BLENDER_KERNEL.md)**: Exhaustive list of all low-level tools and capabilities.

### 🛡️ Security & Failure Protocols
*   **[Security Policy](HUMAN_ONLY/SECURITY.md)**: Vulnerability reporting and baseline security mandates.
*   **[Security & Architecture Deep Dive](HUMAN_ONLY/SECURITY_DOCS.md)**: The "Iron Box" safety model explained.
*   **[Triple-Lock Invariance Model](HUMAN_ONLY/TRIPLE_LOCK.md)**: The three-layer verification system for absolute determinism.
*   **[Agent Isolation Architecture](HUMAN_ONLY/AGENT_ISOLATION.md)**: Multi-agent sandboxing to prevent context poisoning.
*   **[Freeze-Proofing & Recovery Guide](HUMAN_ONLY/FREEZE_PROOFING.md)**: Prevention and recovery from Blender hangs and crashes.

### 📜 Doctrine & Legal
*   **[Governance & Override Policy](HUMAN_ONLY/GOVERNANCE_POLICY.md)**: Rules for the "Fourth Order" (Human-in-the-Loop).
*   **[Non-Goals & Doctrine](NON_GOALS.md)**: Intentional limitations to prevent "AI Psychosis."
*   **[AI Context & Philosophy](AI_CONTEXT.md)**: Philosophical guide to adversarial prompting and the "Overconfidence Trap."
*   **[Full Feature Manifest](HUMAN_ONLY/FEATURES.md)**: The authoritative list of all functional abilities.
*   **[Contributing Guide](HUMAN_ONLY/CONTRIBUTING.md)**: Standards for code quality and the "Zero Trust" philosophy.
*   **[Privacy Policy](HUMAN_ONLY/PRIVACY.md)**: Local-first, zero-telemetry commitment.

---

## 🛡️ Iron Box Security
The bridge is hardened via three distinct layers:
1.  **AST Auditing**: All incoming Python code is parsed and scanned for forbidden calls (e.g., `os.system`, `subprocess`).
2.  **Asset Scanning**: Binary assets are greedily scanned for embedded scripts before linking.
3.  **OS Sandboxing**: Optional kernel-level isolation.

### OS-Level Security Layers
You can enable additional protection by setting environment variables before running `start_bridge.sh`:

| Layer | Variable | Description |
| :--- | :--- | :--- |
| **Bubblewrap** | `USE_BWRAP=true` | Uses Linux namespaces to isolate the filesystem. |
| **Firejail** | `USE_FIREJAIL=true` | Applies restricted security profiles and network filtering. |
| **AppArmor** | `USE_APPARMOR=true` | Kernel-level Mandatory Access Control (MAC). |

**Usage Example:**
```bash
USE_BWRAP=true ./start_bridge.sh
```

*Note: AppArmor requires loading the profile once via `sudo apparmor_parser -r security/blender_vibe_bridge.apparmor`.*

---

## 🐣 Beginner's Guide (Getting Started)
1. **Download**: Use Blender 3.6 LTS or newer.
2. **Install**: 
   - Zip the `blender_addon/vibe_bridge` directory.
   - Install the `.zip` via Blender's **Edit > Preferences > Add-ons > Install**.
   - Enable **BlenderVibeBridge**.
3. **Start Server**:
   ```bash
   ./start_bridge.sh
   ```
4. **Build**: Use natural language to orchestrate your production pipeline.

---

## 🧠 AI Literacy & Philosophy

## 🧠 AI Literacy & The Human-AI Interface

### 🏷️ The Overconfidence Trap (Why we trust the "Vibe")
It is a natural human instinct to be impressed by an articulate, expert-sounding response. When an AI presents a solution with high confidence and professional terminology, it is very easy to fall into **Magical Thinking**—the belief that the AI has discovered a "groundbreaking" shortcut or a "unique" fix that defies standard technical limitations.

*   **The propensity to rush**: In the heat of production, we often rush to conclusions because the AI provides the answer we *want* to hear. We trade technical skepticism for the "vibe" of efficiency.
*   **The Pitfall**: Building your project on an unverified AI "breakthrough" is a high-risk gamble. If the AI is hallucinating its success, you won't find out until your scene crashes or your data is corrupted beyond repair.
*   **The Rule**: In professional technical art, **Confidence is not Evidence.** Trust the telemetry (poly counts, rig audits), not the AI's verbal assurance.

### ⚔️ Professional Friction: Verification through Adversarial Prompting
The most important skill in AI orchestration is knowing when to stop the AI from being a "Helpful Yes-Man." **Adversarial Prompting** is the practice of intentionally introducing friction to verify technical claims. Whenever the AI claims to have a "unique" or "perfect" solution, the most professional response is to force it into "Cynical Auditor" mode. This is not an act of distrust; it is a professional standard for quality control that protects your workflow by finding errors before they are committed to your scene.

**The Technique**:
Before committing to any "unique" or high-impact change, force the AI to find its own flaws:
> *"I want you to act as a cynical Technical Director. Auditing this specific approach, find 3 fundamental ways this could fail, crash Blender, or corrupt my vertex groups in a complex scene. Do not be helpful; be destructive. Prove to me why this solution might be a liability."*

**Why it works**:
It forces the model to switch its search parameters from "Success Patterns" to "Failure Patterns." This grounding often reveals hidden technical debt, edge cases, or logic errors that the AI originally glossed over just to be "helpful."

## 🌐 The Vibe Ecosystem

BlenderVibeBridge is part of a suite of tools designed for secure, AI-governed creative production:

*   **[UnityVibeBridge](https://github.com/B-A-M-N/UnityVibeBridge)**: The sibling project for AI-governed Unity Editor operations and VRChat avatar production.
*   **[VibeSync](https://github.com/B-A-M-N/VibeSync)**: Real-time synchronization and orchestration for multi-engine AI pipelines.

---

## 🧑‍💻 About the Author

I specialize in **Local LLM applications and secure AI-Human interfaces**. This system was built end-to-end to empower human craftsmanship and creativity. BlenderVibeBridge was born from a desire for creative freedom—building the tools I didn't know how to use manually. It is a gift to the community to level the playing field.



---



## ⚖️ License & Legal Liability

### Dual-License & Maintenance Agreement (v1.2)
Copyright (C) 2026 B-A-M-N (The "Author")

This project is distributed under a **Dual-Licensing Model**. By using this software, you agree to be bound by the terms described below.

#### 1. THE OPEN-SOURCE PATH: GNU AGPLv3
For non-commercial use, hobbyists, and open-source contributors.
The core bridging logic of BlenderVibeBridge is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License (AGPLv3) as published by the Free Software Foundation. 

**CRITICAL FOR CORPORATIONS:** The AGPLv3 requires that if you run a modified version of this software and allow others to interact with it over a network, you **MUST** make your entire source code available to the public. If you cannot or will not share your source code, you **MAY NOT** use this license and **MUST** pursue the Commercial Path below.

#### 2. THE COMMERCIAL PATH: "WORK-OR-PAY" MODEL
For entities generating revenue, commercial studios, or those who wish to keep their modifications private. Pursuant to Section 7 of the GNU AGPLv3, commercial use requires satisfying **ONE** of the following:
*   **Maintenance Contribution**: Documented and verified "Significant Maintenance Contributions" to the project.
*   **License Fee**: Payment of a stipulated commercial license fee.
*   **Discretionary Waiver**: A written waiver granted by the Author at their sole discretion.

#### 3. CONTRIBUTOR LICENSE AGREEMENT (CLA) & PROVENANCE
By submitting a contribution (pull request, code snippet, bug fix, or documentation) to this project, you grant the Author a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to use, reproduce, prepare derivative works of, publicly display, and **sublicense** your contributions in both the open-source and commercial versions of the software.

**TRACKING WAIVER**: This grant is made without the requirement for the Author to track, notify, or seek further approval from the Contributor for any future use. You represent that you are legally entitled to grant this license and that your contributions do not violate any third-party rights.

---

### ⚠️ LIABILITY LIMITATION, INDEMNITY & AI DISCLAIMER

1. **NO WARRANTY**: This software is provided "AS IS." The Author is not responsible for the non-deterministic nature of AI-interpreted operations.
2. **AI NON-DETERMINISM**: The Author is not liable for "hallucination drift," unintended asset deletion, project corruption, or "vibe loss" resulting from LLM-to-Blender translations.
3. **HUMAN-IN-THE-LOOP MANDATE**: All AI-suggested mutations are considered "Proposed" until a Human User executes a "Finalize" check. THE USER ACCEPTS FULL LEGAL AND TECHNICAL RESPONSIBILITY FOR ANY CODE OR MUTATION THEY ALLOW THE AI TO EXECUTE.
4. **INDEMNIFICATION**: You agree to indemnify, defend, and hold harmless the Author from and against any and all claims, liabilities, damages, and expenses (including attorney fees) arising from your use of the software, your breach of this license, or any assets produced using this software.
5. **THIRD-PARTY IP & EULA COMPLIANCE**: 
    *   **NON-AFFILIATION**: BlenderVibeBridge is an independent project and is **not affiliated with, endorsed by, or sponsored by** the Blender Foundation or any other engine provider.
    *   **USER RESPONSIBILITY**: Users are solely responsible for ensuring their use complies with the End User License Agreements (EULA) and Terms of Service of Blender and any assets used.
6. **LIMITATION OF LIABILITY**: TO THE MAXIMUM EXTENT PERMITTED BY LAW, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES (INCLUDING LOSS OF DATA, PROFITS, OR CREATIVE FLOW).



**Created by the Vibe Bridge Team.**

