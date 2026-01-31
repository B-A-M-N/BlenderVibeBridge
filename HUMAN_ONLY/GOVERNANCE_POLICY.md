# Governance & Human Override Policy (The Fourth Order)

**Objective:** Codify the relationship between the Governed Kernel and its Human Creator, ensuring that overrides are journaled as "Systemic Deviations" rather than random errors.

---

## 1. The Veto Protocol
Humans possess the ultimate authority to halt any AI operation. However, a Veto must follow the "Forensic Stop" procedure:
1.  **Trigger**: Use the `VETOED` state in the bridge UI or the `KILL_VIBE` environment variable.
2.  **Journaling**: Every Veto must be accompanied by a brief entry in `logs/human_intervention.log` explaining the rationale (e.g., "AI attempting incorrect topology simplification").
3.  **Kernel State**: A Vetoed session enters `READ_ONLY` mode until a manual `reconcile_state` is executed.

---

## 2. Snapshot Responsibility (Manual Reality)
While the AI performs automatic snapshots, the Human Operator is responsible for "Grand Reality Anchors":
1.  **Manual Save**: A manual `.blend` or `.unity` save MUST be performed before initiating any "Strategic Intent" (e.g., full character re-rigging).
2.  **Checkpoint Rotation**: Humans should periodically purge the `checkpoints/` folder, retaining only "Golden Milestone" files.

---

## 3. Audit Cycles (The Chain Review)
To prevent "Creeping Drift," the Human Auditor should perform the following reviews:
*   **Daily**: Quick scan of `vibe_audit.jsonl` for `INVARIANCE_VIOLATION` errors.
*   **Weekly**: Verify the cryptographic integrity of the WAL chain using the `Verify Chain` utility.
*   **Monthly**: "Epistemic Cleanup" — manually reviewing and expiring stale lessons in the Belief Ledger (`metadata/vibe_beliefs.jsonl`).

---

## 4. Credential & Token Management
To maintain the "Iron Box" security model:
1.  **Token Rotation**: The `VIBE_TOKEN` should be rotated every 30 days or after any suspected security breach.
2.  **Bootstrap Authority**: Only one "Master Instance" of the Bridge Server may run per project directory to prevent cross-process identity theft.

---

## ⚖️ THE LITMUS TEST
If a failure occurs, the Auditor must be able to prove whether it was:
*   **Machine Bug**: (1st Order)
*   **Causal Error**: (2nd Order)
*   **Poisoned Belief**: (3rd Order)
*   **Human Decision**: (4th Order)

**Any action not traceable to one of these four is a "Systemic Ghost" and requires an immediate bridge shutdown.**
