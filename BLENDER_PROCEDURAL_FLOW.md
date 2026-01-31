# BLENDER AI PROCEDURAL FLOW (v1.1.0)

**Objective:** Preserve identity, prevent crashes, survive undo/reload, and maintain external sync integrity.

---

## FLOW 0 — ATTACH & BOOTSTRAP

1. Wait until Blender is **idle** (no modal operator, no render, no undo push).
2. Confirm a `.blend` file is loaded.
3. Abort if Blender is compiling shaders or saving.
4. Detect last shutdown state. If abnormal:
   * Enter **Safe Mode**.
   * Disable automation layers.
   * Require explicit user opt-in to re-enable.

---

## FLOW 1 — CAPABILITY & STATE LOAD

5. Query editor capabilities (undo depth, auto-save interval). Adjust behavior accordingly.
6. Load UUID registry from datablock custom properties and sidecar registry file (backup).
7. Validate registry schema and version. If mismatch, run migration or abort.
8. If registry missing → initialize empty registry.

---

## FLOW 2 — INDEX DATA

9. Scan all datablocks (Objects, Meshes, Materials, Armatures, Actions, Images, Collections).
10. Build map: `UUID → datablock reference`.

---

## FLOW 3 — ENFORCE IDENTITY

11. For each datablock:
    * If UUID exists → continue.
    * If UUID missing → generate UUID and write to datablock custom property.
12. Detect duplicate UUIDs. On collision:
    * Freeze operations.
    * Regenerate UUID for newest datablock and persist immediately.

---

## FLOW 4 — SNAPSHOT & LOG CONSULTATION (MANDATORY)

13. Serialize snapshot (UUID ↔ name, type, and external references).
14. **Consult Audit Logs**: Query the log index for prior failures, incomplete transactions, or crash flags associated with target UUIDs.
15. Timestamp snapshot.
16. Abort if snapshot incomplete or log consultation indicates terminal instability.

---

## FLOW 5 — EXECUTE OPERATION (TRANSACTIONAL)

17. Wrap operation in a transaction: `begin → mutate → validate → commit | rollback`.
18. Resolve all targets **by UUID only**.
19. Never store long-lived Python object references.
20. Serialize writes through a **single writer queue** (One write at a time).

---

## FLOW 6 — STABILITY & MONITOR

20. Monitor for repeated exceptions, undo stack corruption, or UI freeze.
21. If instability detected:
    * Abort operation and roll back to snapshot.
    * Disable automation and preserve state.

---

## FLOW 7 — RECOVERY & RELOAD

**Triggered on: Undo/Redo, File Reload, Auto-save restore, Script Reload.**

22. Drop all cached datablock references (handles are volatile).
23. Re-scan all datablocks and rebuild: `UUID → datablock reference`.
24. Rebind external links (Unity/server) via UUID.

---

## FLOW 8 — INTERCEPT & SELF-HEAL

25. **Duplication**: Detect duplicated datablocks; regenerate UUID for the duplicate immediately.
26. **Deletion**: Detect deletion; tombstone UUID, notify external systems, and archive mapping.
27. **Discovery**: Assign UUIDs to newly discovered datablocks. Never auto-resolve ambiguous matches.

---

## FLOW 9 — VALIDATE & AUDIT

28. Validate UUID uniqueness, registry parity, and external mapping validity.
29. Emit structured logs (Timestamp, UUID, Operation, Result).
30. Persist registry and logs. Ensure logs are replayable for recovery.

---

## FLOW 10 — MODAL & USER ISOLATION

31. Treat modal operations (sculpt, paint, etc.) as non-persistent/blocking.
32. Detect manual edits and pause automation immediately.
33. Resume automation only when the editor is verified idle.

---

## FLOW 11 — IDLE / WATCH

34. Enter watch mode with performance governors (Max scan frequency/repair ops per tick).
35. **Debounce Events**: Throttled listener execution to avoid loop spirals.
36. Listen for datablock changes, mode transitions, and external requests.
37. Yield execution if performance limits are exceeded to maintain UI responsiveness.

---

# ABSOLUTE ENFORCEMENT RULES

* UUID stored in datablock custom properties is authoritative.
* Python object references are disposable.
* Undo/Reload invalidates all cached handles.
* Automation never fights the editor or the user.
* Transactions are never partial; roll back on any failure via pre-operation snapshots.
* Automation knows when to stop (Error escalation ladder).

---

## UNITY ↔ BLENDER FLOW PARITY

Unity: Domain Reload → Re-index → Rebind by UUID
Blender: Undo/File Reload → Re-index → Rebind by UUID