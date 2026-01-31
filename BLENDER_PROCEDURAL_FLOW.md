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
6. **Environment Check**: Validate Python dependency manifest against `sys.modules`. Abort on mismatch.
7. Load UUID registry from datablock custom properties and sidecar registry file (backup).
8. Validate registry schema and version. If mismatch, run migration or abort.
9. If registry missing → initialize empty registry.

---

## FLOW 2 — INDEX DATA
...
## FLOW 5 — EXECUTE OPERATION (TRANSACTIONAL)

16. **Claim Lock**: Claim UUID-level lock for target datablocks. Abort on contention.
17. **Resource Audit**: Pre-calculate topology/VRAM impact. Abort if the budget is exceeded as per [LIFECYCLE_DISCIPLINE.md](./LIFECYCLE_DISCIPLINE.md).
18. **Freeze-Proofing Check**: If the operation is a large batch, disable `use_global_undo`.
19. Wrap operation in a transaction: `begin → mutate → validate → commit | rollback`.
20. **Persistence Shield**: Apply `use_fake_user = True` to all modified/unlinked datablocks.
21. Resolve all targets **by UUID only**.
22. **Main Thread Only**: Ensure all `bpy` mutations are executed on the main thread.
23. Serialize writes through a **single writer queue** (One write at a time).

---

## FLOW 6 — STABILITY & MONITOR
...
## FLOW 8 — INTERCEPT & SELF-HEAL

25. **Duplication**: Detect duplicated datablocks; regenerate UUID for the duplicate immediately.
26. **Deletion**: Detect deletion; tombstone UUID, notify external systems, and archive mapping.
27. **Resurrection**: On datablock re-creation, attempt UUID recovery from archived tombstone mappings.
28. **Discovery**: Assign UUIDs to newly discovered datablocks. Never auto-resolve ambiguous matches.

---

## FLOW 9 — VALIDATE & AUDIT

29. **Unit Normalization**: Verify and normalize all transform data to SI Meters (1.0 = 1 Meter).
30. Validate UUID uniqueness, registry parity, and external mapping validity.
31. Emit structured logs (Timestamp, UUID, Operation, Result).
32. Persist registry and logs. Ensure logs are replayable for recovery.

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