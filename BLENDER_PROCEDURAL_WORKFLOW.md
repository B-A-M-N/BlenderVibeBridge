# BLENDER AI PROCEDURAL WORKFLOW (v1.0.0)

**Goal:** Prevent data loss, identity drift, dependency breakage, undo corruption, and crash loops across file reloads, undo stacks, and external sync.

---

## PHASE 0 — ATTACH / BOOTSTRAP

1. **Detect Blender Execution Context**
   * Confirm:
     * Interactive session vs background
     * File loaded vs empty
     * Auto-save state
   * Abort if Blender is in modal operator state.

2. **Load Persistent Identity Registry**
   * Load UUID registry from:
     * `.blend` custom properties **(primary)**
     * Sidecar JSON **(secondary backup)**
   * Validate schema and checksum.
   * If missing → initialize registry.

3. **Index Blender Data-Blocks**
   * Scan:
     * Objects
     * Meshes
     * Materials
     * Armatures
     * Actions
     * Images
     * Collections
   * Build map:
     ```
     UUID ↔ Blender datablock
     ```

---

## PHASE 1 — UUID ENFORCEMENT (BLENDER-SPECIFIC)

4. **Validate UUID Presence**
   * For each datablock:
     * If UUID exists → continue
     * If missing → generate UUID
     * Store in `datablock["uuid"]`

5. **Detect UUID Collisions**
   * If duplicate UUID detected:
     * Freeze sync
     * Log collision
     * Regenerate UUID for newest datablock only
     * Persist immediately

6. **Persist Registry**
   * Write registry to:
     * `.blend` file
     * Sidecar file
   * Force save if safe.

---

## PHASE 2 — PRE-OPERATION SNAPSHOT

**Before any operation that may mutate or invalidate Blender state**

7. **Snapshot State**
   * Serialize:
     * UUID ↔ datablock name
     * UUID ↔ datablock type
     * UUID ↔ external references (Unity, server, AI)
   * Timestamp snapshot.

8. **Validate Snapshot**
   * If snapshot incomplete → abort operation.

---

## PHASE 3 — OPERATION EXECUTION

9. **Execute Operation via UUID Only**
   * Applies to:
     * Import / export
     * Geometry edits
     * Renaming
     * Linking / appending
     * Modifier application
   * Never rely on:
     * Datablock name
     * List index
     * UI order

10. **Respect Blender’s Undo System**
    * Wrap operations in undo-safe blocks
    * Never:
      * Spam undo pushes
      * Mutate data in modal loops
    * If undo corruption risk detected → stop.

---

## PHASE 4 — FILE RELOAD / UNDO / REDO RECOVERY

**Triggered after:**
* File reload
* Undo / redo
* Linked file refresh
* Auto-save restore

11. **Rebuild Datablock Index**
    * Re-scan all datablocks
    * Rebuild:
      ```
      UUID → current datablock reference
      ```

12. **Reattach External Links**
    * Rebind Unity/server references by UUID
    * Ignore datablock renames or duplication suffixes

13. **Validate Rehydration**
    * Detect:
      * Missing UUIDs
      * Duplicate UUIDs
      * Orphaned external mappings

---

## PHASE 5 — SELF-HEALING

14. **Repair Missing UUIDs**
    * Generate UUID
    * Assign to datablock
    * Persist immediately

15. **Resolve Orphans**
    * If datablock deleted:
      * Archive mapping
      * Notify external systems
    * Never guess replacements

16. **Quarantine Corruption**
    * If Blender enters error loop:
      * Disable AI automation
      * Preserve state
      * Notify user

---

## PHASE 6 — VALIDATION PASS

17. **Consistency Check**
    * UUID uniqueness
    * Registry ↔ datablock parity
    * External references valid

18. **Persist Logs**
    * Save:
      * Actions taken
      * Repairs performed
      * Warnings

---

## PHASE 7 — SAFE IDLE / WATCH MODE

19. **Watch for Triggers**
    * Datablock creation/deletion
    * Mode changes
    * File save/load
    * External sync requests

20. **Throttle Operations**
    * Avoid:
      * Per-frame polling
      * Heavy scans in UI thread

---

# BLENDER-SPECIFIC HARD RULES

* **UUID stored in datablock custom properties is authoritative**
* **Names are cosmetic**
* **Undo can destroy references — expect it**
* **File reload invalidates all Python object handles**
* **Never store Blender object references long-term**
* **Assume users duplicate aggressively**

---

## UNITY ↔ BLENDER SYMMETRY (IMPORTANT)

| Concept          | Unity                  | Blender                       |
| ---------------- | ---------------------- | ----------------------------- |
| Identity         | UUID field             | datablock["uuid"]             |
| Reload hazard    | Domain reload          | Undo / file reload            |
| Instance drift   | Scene instance reorder | Object duplication / suffixes |
| Unsafe reference | InstanceID             | Python object pointer         |
| Safe rebind key  | UUID                   | UUID                          |

---

## WHY UUID > SEMANTIC IN BLENDER TOO

Blender:
* Renames silently
* Duplicates with suffixes
* Breaks Python references on reload
* Reorders collections

Semantic identifiers **cannot survive this**. UUIDs do.
