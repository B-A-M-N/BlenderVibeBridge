# BLENDER VIBE LIFECYCLE DISCIPLINE

**Goal:** Prevent system collapse by enforcing strict lifecycle discipline, IO safety, and crash recovery across the Blender environment.

---

## 1. FILE SYSTEM & IO RACE CONDITIONS

1. **Atomic Writes**: Never read files currently being written.
2. **Write Markers**: Require a write-complete marker (`.done`, checksum, or rename).
3. **Safe Sequence**: Use `write → flush → fsync → rename`.
4. **Validation**: Reject partial files silently.

---

## 2. TIME-OF-CHECK vs TIME-OF-USE (TOCTOU)

1. **JIT Validation**: Re-validate UUID → object mapping **immediately before use**.
2. **Dynamic Rebind**: If mapping is invalid, perform an immediate re-scan and rebind.
3. **Fail Fast**: Abort the operation if the object cannot be re-resolved.

---

## 3. EVENT STORM CONTROL

1. **Re-entrancy Guards**: All event handlers must be guarded against recursive triggers.
2. **Rate Limiting**: Implement strict rate limits for event-driven mutations.
3. **Depth Monitoring**: Maintain an `event_depth_counter`; abort if depth exceeds the safety threshold.
4. **Deferred Execution**: Defer heavy processing to the next editor tick.

---

## 4. VERSIONED STATE MIGRATION

1. **Schema Versioning**: Every UUID registry must include a `schema_version`.
2. **Explicit Migration**: Detect version mismatches on load and migrate data explicitly with logging.
3. **Persistent Upgrade**: Never auto-upgrade data in-memory without a corresponding persistence step.

---

## 5. DUPLICATION SEMANTICS

1. **Detect Duplicate UUIDs**: Detect duplicated datablocks with matching UUIDs.
2. **Immediate Regeneration**: Regenerate the UUID for the duplicated datablock immediately.

---

## 6. DELETION DISCIPLINE

1. **Intercept Deletes**: Explicitly catch deletion events.
2. **Tombstoning**: Mark the UUID as `tombstoned` and notify external systems.
3. **Archive Mappings**: Never erase mappings immediately; move them to an archive.

---

## 7. MULTI-CONTEXT COHERENCE

1. **Namespacing**: Namespace UUIDs using `project_id + uuid`.
2. **Collision Detection**: Detect and block merges that result in UUID ambiguity.

---

## 8. EPHEMERAL HANDLE MANAGEMENT

1. **No Long-Lived References**: Treat all `bpy` object references as ephemeral and disposable.
2. **UUID-First Resolution**: Store `uuid → datablock name/type` and re-resolve the handle on every access.

---

## 9. CRASH LOOP BREAKER

1. **Boot Tracking**: Maintain a `last_boot_success` flag.
2. **Safe Mode Trigger**: If consecutive crashes are detected, start in Safe Mode with automation disabled.
3. **Manual Recovery**: Require manual user intervention to re-enable AI features after a crash loop.

---

## 10. USER INTENT PROTECTION

1. **Manipulation Detection**: Detect when the user is manually editing the scene.
2. **Automation Pause**: Instantly pause AI operations during direct human manipulation.
3. **Idle Resume**: Resume automation only after a verified idle period.

---

## 11. EXTERNAL SYSTEM TRUST MODEL

1. **Zero Trust**: Treat all external data as untrusted input.
2. **Sanity Checks**: Validate UUIDs, schema versions, and update completeness before application.

---

## 12. LOGGING FOR RECOVERY

1. **Structured Auditing**: Logs must be structured (JSONL preferred), timestamped, and persisted.
2. **Replayable Fixes**: Every automated repair must be logged such that it is replayable for forensic recovery.

---

## 13. AI FAILURE BOUNDARY



1. **Failure Thresholds**: Maintain a persistent failure counter.

2. **Circuit Breakers**: Stop all automation and notify the user when the threshold is reached.

3. **No Silent Retries**: Never attempt to "fix" a failure with the same AI logic that caused it.



---



## 14. LOG-DRIVEN GOVERNANCE (LOG-AS-STATE)



**Rule: No state-changing operation may execute without explicit log consultation and acknowledgment.**



### FLOW L1 — LOG INDEXING (BOOT TIME)

1. On attach / boot:

   * Load last **N** log entries.

   * Build in-memory index: `UUID → last_known_state`, `UUID → last_error`, `operation → last_outcome`.

2. Validate log schema. Abort automation if logs are unreadable.



### FLOW L2 — LOG CONSULTATION GATE (PRE-ACTION)

3. **Pre-Action Query**: Before every mutation, query log index for prior failures on the same UUID, recent crash flags, or incomplete transactions.

4. **Behavioral Adjustment**: Adjust behavior (retry, degrade, block) based on findings. Log the consultation.



### FLOW L3 — LOG-DRIVEN DECISION OVERRIDE

5. **Override Authority**: Logs outrank inference. If logs indicate repeated failure or identity ambiguity, override the current plan and enter safe mode.



### FLOW L4 — TRANSACTION-BOUND LOGGING

6. **Transaction Lifecycle**: Every transaction MUST log `BEGIN`, `STEP(S)`, and `COMMIT | ROLLBACK`.

7. **Boot Recovery**: On boot, scan for `BEGIN` without `COMMIT` and auto-rollback or quarantine the state.



### FLOW L5 — LOG-AS-MEMORY PROMOTION

8. **Operational Memory**: Promote logs regarding known bad assets or unstable sequences into hard constraints in operational memory.



### FLOW L6 — FAILURE ESCALATION VIA LOGS

9. **Granular Escalation**: Use failure counters in logs to disable specific features rather than the entire system where possible.



### FLOW L7 — POST-ACTION LOG VALIDATION

10. **Write-Verification**: After an operation, re-read the log entry just written to confirm it exists and matches the expected state.



## 14. LOG-DRIVEN GOVERNANCE (LOG-AS-STATE)
...
### FLOW L8 — CROSS-PROCESS COHERENCE
11. **Sequence Sync**: Sync log sequence numbers between Blender and the Bridge Server to detect divergence. Block actions on divergence.

---

## 15. PERFORMANCE & WATCHDOG

1. **Event Debouncing**: Thottle event listeners to prevent infinite loops and editor hangs.
2. **Knowledge Base Lookup**: Consult [BLENDER_FREEZE_KNOWLEDGE_BASE.md](./BLENDER_FREEZE_KNOWLEDGE_BASE.md) to predict and mitigate specific freeze vectors before operation.
3. **Hard Limits**: Enforce `Max operations per tick` and `Max scan frequency`.
3. **Yield Loops**: Long-running scans must yield execution to keep the Blender UI responsive.
4. **Stale State Guard**: Introduce sequence numbers to detect if the AI is acting on state that changed during a multi-frame calculation.

---

## 16. ATOMICITY & ROLLBACK

1. **Full State Snapshot**: Capture a complete state snapshot (relevant to the operation) before any mutation.
2. **Auto-Rollback**: Any failure or unexpected crash during an operation MUST trigger an immediate rollback to the pre-operation snapshot.
3. **Commit/Rollback Discipline**: Every multi-step operation follows the pattern: `Snapshot → Mutate → Validate → Commit | Rollback`.

---

## 17. UNIT NORMALIZATION PROTOCOL (Anti-Drift)

1. **Unit-Agnostic Scaling**: Verify `Scene.unit_settings` (Metric vs. Imperial) before any transform mutation.
2. **Normalize to "Vibe-Meters"**: All positional and scale data must be normalized to SI Meters (1.0 = 1 Meter) at the sync boundary.
3. **Scale Invariant Enforcement**:
    * If `Scene.unit_settings.scale_length` != 1.0, apply the inverse factor to all outgoing coordinates.
    * If incoming data is unscaled, apply the current scene scale factor before applying to datablocks.
4. **Coordinate Basis Audit**: Confirm the coordinate system basis (e.g., Z-Up vs. Y-Up) matches the external engine's contract before any matrix multiplication.

---

## 18. TOMBSTONE LIFECYCLE & REGISTRY GC

1. **Archive Threshold**: Tombstoned UUIDs must be archived for a minimum of 30 days or 10 sessions before permanent deletion.
2. **Resurrection Flow**: If a datablock is re-created with identical topology/name to a tombstoned entry, trigger a UUID recovery prompt or auto-rebind if confidence > 95%.
3. **Registry Maintenance**: Perform a deterministic "Registry Purge" once per project lifecycle or on manual trigger to remove orphans that exceed the archive threshold.

---

## 19. MULTI-AGENT ARBITRATION (OBJECT LOCKING)

1. **UUID-Level Locks**: An agent must claim an "Exclusive Lock" on a UUID before any mutation.
2. **Conflict Resolution**: If a UUID is already locked by another process (Human or Agent), the secondary agent must:
    * Enter `Wait` state.
    * Notify the bridge of a `CONTENTION_LOCK`.
    * Abort after a 5-second timeout.
3. **Implicit Human Priority**: User manipulation (detected via UI interaction) always overrides and breaks an AI lock.

---

## 20. ENVIRONMENT & DEPENDENCY PINNING

1. **Requirement Manifest**: All AI scripts must declare their required Python modules and Blender version range.
2. **Pre-Flight Validation**: The bridge must compare the manifest against `sys.modules` and `bpy.app.version` before execution.
3. **Module Isolation**: Block execution if any unauthorized/missing module is detected to prevent "Import Crashes."

---

## 21. RESOURCE & TOPOLOGY INTEGRITY

1. **Topology Budgeting**: AI agents MUST perform a complexity scan before any mesh mutation.
    * **Hard Cap**: Reject operations that would result in >1M polygons per object or >5M per scene without explicit human override.
    * **Integrity Check**: Mandate a `non-manifold` edge check for all geometry operations.
2. **The "Fake User" Shield**: To prevent Blender's garbage collector from deleting unlinked data:
    * Set `use_fake_user = True` on all newly created or modified Actions, Materials, and Meshes before unlinking or re-assigning.
    * Only unset `use_fake_user` during an explicit `Purge` operation.
3. **Cumulative Modifier Guard**: Before applying or adding modifiers (especially Subsurf, Array, or Boolean):
    * Calculate the estimated vertex delta.
    * Block the operation if the cumulative VRAM impact exceeds 80% of the hardware sentinel's available memory.

---

## 22. FREEZE PREVENTION & THREAD SAFETY

1. **Non-Blocking Execution**: AI-generated scripts must utilize `bpy.app.timers` or `Modal Operators` for any operation that takes >100ms.
2. **Marshaled Mutations**:
    * Background threads are for **Compute/IO only**.
    * Use a thread-safe queue to pass results to a main-thread consumer.
    * Never access `bpy.context` or `bpy.data` from outside the main thread.
3. **Undo-Safe Batching**: For mass renaming, vertex group updates, or material swaps:
    * Disable `use_global_undo`.
    * Perform batch.
    * Push a single undo step manually (`bpy.ops.ed.undo_push`).
    * Re-enable `use_global_undo`.
4. **I/O Timeouts**: Every external call (Socket, HTTP, Subprocess) must have a hard timeout (default 5s) to prevent the "Spinning Wheel" hang.

---

## 23. BLENDER FREEZE KNOWLEDGE BASE (AI REFERENCE)

| Category | Source | Cause | Symptoms | Fix / Prevention |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | Infinite loops | Tight loops with no yield | UI Hang | Use modal timers/operators; yield control. |
| **Python** | Heavy CPU Work | Large `bpy` calcs | Unresponsive | Offload to background threads. |
| **Python** | Blocking I/O | Sync file/net calls | Freeze | Non-blocking I/O; 5s Timeouts. |
| **Python** | Thread Safety | `bpy.data` from side threads | Crash/Hang | Marshal to main thread via queue. |
| **Scene** | High-poly Meshes | >1M vertex density | Viewport Stall | Decimate; Simplify; Bounding Box. |
| **Scene** | Modifier Stacks | Deep/Recursive eval | Update Hang | Collapse stacks; Apply non-essential. |
| **GPU** | Cycles/Eevee | Complex shaders/16k images | TDR Crash | Reduce Tile Size; Mipmaps. |
| **Undo** | History Spikes | Mass batch edits | History Hang | Disable `use_global_undo` for batches. |
| **Memory** | Data Spikes | Large temp buffers | Hard Crash | Delete temp blocks; Use generators. |

---

## REQUIRED LOG STRUCTURE (MINIMUM)



```

timestamp

process_id

session_id

operation_id

uuid(s)

phase (BEGIN | STEP | COMMIT | ROLLBACK)

outcome

error_code

schema_version

```



---



# ABSOLUTE META-RULE



> **Identity is not enough — lifecycle discipline is what keeps systems alive.**
