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

---
**Protocol Note**: The ModelingKernel accepts both string keys and their hex/int opcode equivalents for backward compatibility during the v1.x transition.
