# BlenderVibeBridge: Non-Goals & Doctrine

This document defines the intentional limitations of the BlenderVibeBridge system. Adhering to these non-goals prevents "AI Psychosis" and ensures deterministic project outcomes.

---

## 🚫 1. No Creative Autonomy
BlenderVibeBridge will **never** attempt to "improve" or "optimize" your scene creatively without a specific, bounded command.
- It will not "fix" your material assignments unless explicitly instructed.
- It will not auto-rename data-blocks or objects to "clean up" the Outliner.
- It will not suggest "better" lighting or camera settings.

## 🚫 2. No Silent Self-Healing
If a mutation fails or reality diverges from AI intent, the system will **never** silently try to "make it work."
- Failure is a first-class, desirable outcome.
- We would rather provide a `403 Forbidden` or `500 Error` and halt than perform a 90% accurate mutation.

## 🚫 3. No Guessing Intent
The bridge will **never** infer intent from ambiguous natural language.
- If you say "Make the cube red," and there are multiple cubes, the system MUST fail and ask for clarification.
- Ambiguity is a system risk.

## 🚫 4. No Trust in API Success
The system will **never** assume a "Success" message from the Blender API (`bpy`) means the operation is finished.
- Only independent verification via `reconcile_state` or `get_scene_telemetry` constitutes proof.
- If the AI cannot *prove* the change happened through numeric data, it must assume it failed.

## 🚫 5. No Persistent Bridge State
The bridge is a **Stateless Translator**. 
- It does not "remember" the scene between sessions beyond what is persisted in `vibe_registry.json`.
- It does not maintain a private "shadow scene" map.

---
**Copyright (C) 2026 B-A-M-N**
