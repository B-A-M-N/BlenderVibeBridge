# Bridge Instruction Set Architecture (ISA) v1.0

This document defines the strictly mapped numbered opcodes for the BlenderVibeBridge. Using Opcodes ensures faster dispatch and reduces command spoofing risks.

| Opcode | Command Type | Capability | Description |
| :--- | :--- | :--- | :--- |
| **0x01** | `run_op` | `MUTATE_SCENE` | Execution of native bpy.ops. |
| **0x02** | `exec_script` | `MUTATE_DATA` | Execution of audited Python logic. |
| **0x03** | `transform` | `MUTATE_SCENE` | Precise Loc/Rot/Scale adjustments. |
| **0x04** | `modifier_op` | `MUTATE_SCENE` | Add/Remove/Set object modifiers. |
| **0x05** | `node_op` | `MUTATE_DATA` | Shader/Geometry node tree manipulation. |
| **0x06** | `lighting_op` | `MUTATE_SCENE` | Light source configuration. |
| **0x07** | `constraint_op` | `MUTATE_SCENE` | Object rigging and constraints. |
| **0x08** | `physics_op` | `MUTATE_SCENE` | Physics sim (Cloth/Rigid Body) application. |
| **0x09** | `material_op` | `MUTATE_DATA` | Material creation and assignment. |
| **0x0A** | `bake_op` | `MUTATE_DATA` | Texture baking orchestration. |
| **0x0B** | `io_op` | `STRUCTURAL` | Import/Export operations. |
| **0x0C** | `link_op` | `STRUCTURAL` | External .blend library linking. |
| **0x0D** | `unity_op` | `PIPELINE` | (Legacy) Specialized production pipelines. |
| **0x0E** | `viseme_op` | `PIPELINE` | Face/Lip-sync data generation. |
| **0x0F** | `system_op` | `KERNEL` | Undo, Rollback, Checkpoint, Reload. |
| **0x10** | `audit_op` | `READ` | Forensics and scene integrity scans. |
| **0x11** | `macro_op` | `PIPELINE` | Compiled high-level artistic recipes. |

## 🧠 Governance Extensions (v1.3)

All Bridge instructions now require **Intent Binding** and support **Speculative Execution**.

### 🏷️ Mandatory Intent Fields
Every command MUST include an `intent` string. Commands violating their intent envelope are rejected by the kernel.

| Intent | Primary Purpose | Allowed Opcodes |
| :--- | :--- | :--- |
| `OPTIMIZE` | Mesh/Scene optimization | 0x04, 0x0B, 0x10, 0x11 |
| `RIG` | Armature/Constraint work | 0x07, 0x0D, 0x10 |
| `LIGHT` | Shading and lighting | 0x05, 0x06, 0x09 |
| `SCENE_SETUP` | Project organization | 0x01, 0x0B, 0x0C |

### 🧪 Speculative Execution
Append `"dry_run": true` to any mutation to perform a validation pass without committing changes to the scene.

### 🚦 Temporal Governors
The kernel enforces a hard **5Hz** command ceiling. Bursting above this frequency will trigger a `RATE_LIMIT` rejection. Repeated validation failures will result in **Capability Revocation** (READ_ONLY or BLOCKED status).
