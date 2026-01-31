# 🌉 BlenderVibeBridge: Full Feature Manifest (v1.3-Stable)

This document serves as the authoritative list of all functional abilities and security protocols for the BlenderVibeBridge system.

---

## 🛡️ 1. Security & Orchestration (The "Iron Box")
The foundational layer ensuring AI agents interact safely with the Blender kernel.

*   **AST Security Gate**: Real-time Python parsing that blocks `os`, `subprocess`, and `eval` calls in AI scripts.
*   **Transactional Mutations**: All complex operations are wrapped in `begin_transaction` / `commit_transaction` blocks for atomic undos.
*   **Hardware Railings**: Hard caps on Subdivision levels (3), Array counts (50), and Light Energy (10k) to prevent system hangs.
*   **Intent Binding**: Commands are rejected if they drift outside their declared intent (e.g., `LIGHT` intent cannot delete objects).

---

## 🏗️ 2. Procedural & Strategic Modeling
Tools for rapid scene blockout and complex geometry generation.

*   **Strategic Recipes**: High-level commands like `BLOCKOUT_HUMANOID` or `THREE_POINT_LIGHTING`.
*   **Geometry Node Orchestration**: Programmatic addition and linking of Geometry Node trees.
*   **Boolean Workflow**: Non-destructive Boolean modifier management with automated solver selection.
*   **Procedural Curves**: Generation of 3D Bezier splines from mathematical coordinate lists.

---

## 🎨 3. Shading, Surfacing & Lighting
Professional-grade technical art tools for the Cycles and EEVEE engines.

*   **Shader Node Factory**: Dynamic creation and linking of `ShaderNodeTree` structures.
*   **Cycles Bake Orchestration**: Automated PBR texture baking (Diffuse, Roughness, Normal) capped at 2048px.
*   **Adaptive Lighting**: Intelligent placement of Point, Area, and Spot lights with automated "Look-At" constraints.
*   **Material Decoupling**: Automated material duplication to prevent accidental cross-object edits.

---

## 🚀 4. Optimization & Technical Audit
Ensuring scene performance and integrity for production.

*   **Mesh Metrics Audit**: Detailed reporting on N-Gons, non-manifold edges, and vertex density.
*   **Orphan Purge**: Automated cleanup of unused data-blocks (Meshes, Materials, Textures).
*   **Smart Decimation**: Goal-oriented poly-count reduction via the Decimate modifier.
*   **UV Integrity Check**: Detecting overlapping islands and missing UV maps.

---

## 🏃 5. Animation & Rigging
Lower-level utilities for high-precision mechanical logic.

*   **Constraint Factory**: Automated setup of `Track To`, `Follow Path`, and `Copy Transforms`.
*   **Vertex Group Management**: Programmatic creation and weight assignment for rigging.
*   **Keyframe Orchestration**: Timeline-aware transform recording for object animation.

---

## ⚖️ 6. Governance & Forensics
*   **Forensic Hash Plane**: Generates scene hashes pre- and post-mutation to track state drift.
*   **Speculative Execution**: Support for `"dry_run": true` to predict topology changes without committing.
*   **Semantic Role Lock**: Protects "Primary" objects (e.g., Main Camera) from accidental deletion.

---
**Copyright (C) 2026 B-A-M-N**
