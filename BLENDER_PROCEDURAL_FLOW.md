# BLENDER AI PROCEDURAL FLOW (v1.0.0)

**Objective:** Preserve identity, prevent crashes, survive undo/reload, and maintain external sync integrity.

---

## FLOW 0 — ATTACH

1. Wait until Blender is **idle** (no modal operator, no render, no undo push).
2. Confirm a `.blend` file is loaded.
3. Abort if Blender is compiling shaders or saving.

---

## FLOW 1 — LOAD STATE

4. Load UUID registry from:
   * Datablock custom properties
   * Sidecar registry file (backup)
5. Validate registry schema.
6. If registry missing → initialize empty registry.

---

## FLOW 2 — INDEX DATA

7. Scan all datablocks:
   * Objects
   * Meshes
   * Materials
   * Armatures
   * Actions
   * Images
   * Collections
8. Build map:
   ```
   UUID → datablock reference
   ```

---

## FLOW 3 — ENFORCE IDENTITY

9. For each datablock:
   * If UUID exists → continue
   * If UUID missing → generate UUID
   * Write UUID to datablock custom property
10. Detect duplicate UUIDs.
11. On collision:
    * Freeze operations
    * Regenerate UUID for newest datablock
    * Persist immediately

---

## FLOW 4 — SNAPSHOT (MANDATORY)

12. Serialize snapshot:
    * UUID ↔ datablock name
    * UUID ↔ datablock type
    * UUID ↔ external references
13. Timestamp snapshot.
14. Abort if snapshot incomplete.

---

## FLOW 5 — EXECUTE OPERATION

15. Execute requested task.
16. Resolve all targets **by UUID only**.
17. Never store long-lived Python object references.
18. Wrap mutations in undo-safe blocks.

---

## FLOW 6 — STABILITY MONITOR

19. Monitor for:
    * Repeated exceptions
    * Undo stack corruption
    * UI freeze
20. If instability detected:
    * Abort operation
    * Disable automation
    * Preserve state

---

## FLOW 7 — RECOVERY TRIGGERS

**Triggered on:**
* Undo / redo
* File reload
* Auto-save restore
* External sync reconnect

21. Drop all cached datablock references.
22. Re-scan all datablocks.
23. Rebuild:
    ```
    UUID → datablock reference
    ```

---

## FLOW 8 — REATTACH EXTERNAL LINKS

24. Rebind Unity / server / tool references via UUID.
25. Ignore datablock names, suffixes, order.

---

## FLOW 9 — SELF-HEAL

26. Assign UUIDs to newly discovered datablocks.
27. Archive mappings for deleted datablocks.
28. Never auto-resolve ambiguous matches.

---

## FLOW 10 — VALIDATE

29. Validate:
    * UUID uniqueness
    * Registry parity
    * External mapping validity
30. Log results.
31. Persist registry and logs.

---

## FLOW 11 — IDLE / WATCH

32. Enter watch mode.
33. Listen for:
    * Datablock creation/deletion
    * Mode changes
    * File save/load
    * External requests
34. Throttle checks to avoid UI degradation.

---

# ABSOLUTE ENFORCEMENT RULES

* UUID stored in datablock custom properties is authoritative
* Python object references are disposable
* Undo invalidates assumptions
* File reload invalidates everything
* Never trust names
* Never trust order
* Never guess

---

## UNITY ↔ BLENDER FLOW PARITY

Unity: Domain Reload → Re-index → Rebind by UUID
Blender: Undo/File Reload → Re-index → Rebind by UUID

Same spine. Different failure modes.
