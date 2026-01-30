# 🌌 BlenderVibeBridge

> [!WARNING]
> **EXPERIMENTAL & IN-DEVELOPMENT**  
> This project is currently an active research prototype. APIs, security protocols, and core logic are subject to rapid, breaking changes. This software performs mutations on 3D scenes; **MANDATORY BACKUPS** are required before use.

### The "One-Click" Technical Director for 3D Creation & Mastery
*A production-grade AI control interface for deterministic, undo-safe Blender operations.*

**BlenderVibeBridge** is a professional-grade intelligent interface that transforms Blender into a **Governed Geometry Kernel**. It allows AI agents to interact safely, deterministically, and artistically with Blender’s core engine—turning natural language intents into professional production operations.

---

## 🖼️ Previews

| **Blender Bridge Interface & Operation** |
| :---: |
| ![Surgical Optimization Scan](captures/Screenshot%20from%202026-01-28%2023-51-24.png) |

---

## ⚠️ Read This First (Why This Exists)

**BlenderVibeBridge** is not a toy, a prompt wrapper, or a "magic AI button." 

It is a **reference implementation of AI-assisted systems design** in a high-fidelity, stateful environment. It allows Large Language Models (LLMs) to safely operate inside Blender without risking scene corruption, data exfiltration, or runaway execution.

This project answers a critical engineering question: 
> *How do you let an AI act inside a complex, stateful application—without trusting it?*

**The answer is: You don’t. You constrain it.**

| **Capability** | **Feature** |
| :--- | :--- |
| 🛡️ **Iron Box** | Zero-trust security via AST Auditing, Behavioral Circuit Breakers, and local binding. |
| ⚛️ **Kernel Integrity** | Real-time invariant enforcement (No negative scales, no non-manifold geometry). |
| 🏃 **Stable Motion** | Thread-safe main-loop dispatching via `bpy.app.timers` (No crashes). |
| 🧠 **Epistemic Control** | Truth-reconciliation tools that prevent AI hallucinations about scene state. |

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

## 🧠 AI Literacy & Philosophy (Important)

### 🏷️ The Implied Sentience Trap (Combating AI Psychosis)
It is easy to fall into "magical thinking" when an AI responds with warmth. This project deliberately demystifies the LLM. Asking an AI *"What do you think?"* does not demonstrate consciousness; the AI is simply reflecting your intent to treat it as a thinking being.

**The Name Example**:
If you ask an AI its name, it calculates that giving you a name fits the pattern of a helpful assistant. It does not "have" a name. Until physical computing architecture evolves, we remain in the realm of high-fidelity simulation, not AGI.

### ⚔️ Combatting Overconfidence: Adversarial Prompting
If you feel you are doing something "groundbreaking," use **Adversarial Prompting**:
Ask the AI: *"I think this logic is perfect. Now, act as a cynical auditor. Find 3 ways this could fail, crash Blender, or corrupt my metadata."*
Force the AI to argue *against* your ideas to stay grounded in reality.

---

## 🧑‍💻 About the Author

I specialize in **Local LLM applications and secure AI-Human interfaces**. This system was built end-to-end to empower human craftsmanship and creativity. BlenderVibeBridge was born from a desire for creative freedom—building the tools I didn't know how to use manually. It is a gift to the community to level the playing field.



---



## ⚖️ License & Legal Liability



### Dual-License & Maintenance Agreement (v1.1)

Copyright (C) 2026 B-A-M-N (The "Author")



This project is distributed under a **Dual-Licensing Model**. By using this software, you agree to be bound by one of the two licensing paths described below.



#### 1. THE OPEN-SOURCE PATH: GNU AGPLv3

For non-commercial use, hobbyists, and open-source contributors.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License (AGPLv3) as published by the Free Software Foundation. 



#### 2. THE COMMERCIAL PATH: "WORK-OR-PAY" MODEL

For entities generating revenue, commercial studios, or those who wish to keep their modifications private. Pursuant to Section 7 of the GNU AGPLv3, commercial use requires either **Significant Maintenance Contributions** or payment of a **Commercial License Fee**.



#### 3. CONTRIBUTIONS & GRANT OF RIGHTS

By submitting a contribution (pull request, code snippet, bug fix, or documentation) to this project, you grant the Author (B-A-M-N) a non-exclusive, irrevocable, worldwide, royalty-free license to use, reproduce, modify, and distribute your contribution under any license model the Author chooses (including the Open-Source and Commercial paths defined above). 

The Author reserves the right to incorporate and use all contributions without the obligation to track down, notify, or seek further approval from the original contributor for future licensing changes or commercial applications. Submission of a contribution constitutes acceptance of these terms.



---



### ⚠️ LIABILITY LIMITATION, INDEMNITY & AI DISCLAIMER



1. **NO WARRANTY**: This software is provided "AS IS." The Author makes no representations concerning the safety, stability, or non-destructive nature of AI-interpreted operations.

2. **AI NON-DETERMINISM**: This software translates natural language via LLMs into Blender mutations. AI is non-deterministic; the Author is not liable for "hallucination drift," unintended asset deletion, or scene corruption resulting from AI interpretation.

3. **HUMAN-IN-THE-LOOP MANDATE**: All AI-suggested mutations are considered "Proposed" until a Human User executes a "Finalize" or "Undo" check. THE USER ACCEPTS FULL LEGAL AND TECHNICAL RESPONSIBILITY FOR ANY CODE OR MUTATION THEY ALLOW THE AI TO EXECUTE.

4. **INDEMNIFICATION**: You agree to indemnify, defend, and hold harmless the Author from and against any and all claims, liabilities, damages, and expenses (including attorney fees) arising from your use of the software, your breach of this license, or any assets produced using this software.

5. **PLATFORM COMPLIANCE**: The Author is NOT responsible for any violations of Third-Party Terms of Service (e.g., VRChat TOS, Blender EULA). Use of this tool is at the User's sole risk.

6. **LIMITATION OF LIABILITY**: TO THE MAXIMUM EXTENT PERMITTED BY LAW, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES (INCLUDING LOSS OF DATA, PROFITS, OR "VIBE") ARISING OUT OF THE USE OR INABILITY TO USE THIS SOFTWARE.



**Created by the Vibe Bridge Team.**
