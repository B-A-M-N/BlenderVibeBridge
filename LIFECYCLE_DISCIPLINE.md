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
2. **Hard Limits**: Enforce `Max operations per tick` and `Max scan frequency`.
3. **Yield Loops**: Long-running scans must yield execution to keep the Blender UI responsive.
4. **Stale State Guard**: Introduce sequence numbers to detect if the AI is acting on state that changed during a multi-frame calculation.

---

## 16. ATOMICITY & ROLLBACK

1. **Full State Snapshot**: Capture a complete state snapshot (relevant to the operation) before any mutation.
2. **Auto-Rollback**: Any failure or unexpected crash during an operation MUST trigger an immediate rollback to the pre-operation snapshot.
3. **Commit/Rollback Discipline**: Every multi-step operation follows the pattern: `Snapshot → Mutate → Validate → Commit | Rollback`.

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
