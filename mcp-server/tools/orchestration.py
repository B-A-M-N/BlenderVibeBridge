# BlenderVibeBridge: Strategic Orchestration Tools (v1.5.0)
import json
import time
import os
from ..ipc.blender_interface import blender_request
from .telemetry import get_scene_telemetry
from .management import check_heartbeat, get_blender_errors

def register_orchestration_tools(mcp):
    
    @mcp.tool()
    def propose_strategic_plan(steps: str) -> str:
        """THE ARCHITECT: Commits to a multi-step execution plan.
        steps: A JSON list of atomic intents.
        The plan is recorded in the audit log for forensic accountability."""
        try:
            plan = json.loads(steps)
            AuditLogger.log_mutation("PLAN", "orchestration/propose", {"plan": plan}, {"status": "ACKNOWLEDGED"})
            return f"Strategic Plan Acknowledged: {len(plan)} steps registered."
        except: return "Error: Invalid JSON plan."

    @mcp.tool()
    def verify_mutation_integrity(vibe_uuid: str, test_type: str = "TRANSFORM") -> str:
        """THE AUDITOR: Performs a post-mutation 'Stress Test' on an object.
        test_type: TRANSFORM (loc/rot/scale), MESH (vertex count), RIG (bone influence)."""
        res = blender_request("GET", f"/blender/integrity_test?uuid={vibe_uuid}&type={test_type}")
        return json.dumps(res, indent=2)

    @mcp.tool()
    def generate_sitrep() -> str:
        """THE OBSERVER: Generates a 360-degree Situation Report (SITREP).
        Includes 'Affordances', 'Reality Anchoring', and 'API Mandates'."""
        pulse = blender_request("GET", "/blender/heartbeat")
        telemetry = blender_request("GET", "/status")
        errors = get_blender_errors(5)
        
        # Get API Mandates for the current version
        from ..core.kernel import get_api_sentinel
        sentinel = get_api_sentinel()
        
        # --- AFFORDANCE MAPPING ---
        affordances = []
        for obj in telemetry.get("objects", []):
            if obj["type"] == "MESH":
                affordances.append(f"{obj['name']}: READY_FOR_UV_UNWRAP")
                if "Armature" in str(telemetry): affordances.append(f"{obj['name']}: READY_FOR_WEIGHT_PAINT")
        
        sitrep = {
            "status": "GREEN" if pulse.get("responsive") else "RED",
            "engine": pulse,
            "api_sentinel": sentinel,
            "scene_hash": telemetry.get("hash"),
            "affordances": affordances,
            "dirty_objects": telemetry.get("dirty_objects", []),
            "overlaps": telemetry.get("overlaps", []),
            "forensics": {"recent_errors": errors},
            "timestamp": time.time()
        }
        return json.dumps(sitrep, indent=2)

    @mcp.tool()
    def verify_transaction_parity(expected_hash: str) -> str:
        """THE AUDITOR: Verifies if the current scene hash matches your expected state.
        Chains a state scan and a forensic log check to prevent 'Ghost State' hallucinations."""
        current_hash = blender_request("GET", "/blender/scene_state").get("scene_hash")
        
        parity = {
            "match": current_hash == expected_hash,
            "current": current_hash,
            "expected": expected_hash,
            "drift_detected": current_hash != expected_hash
        }
        
        return json.dumps(parity, indent=2)

    @mcp.tool()
    def prepare_mutation_safe_zone(intent: str) -> str:
        """THE WARDEN: Prepares the engine for a safe mutation.
        Chains: begin_transaction -> run_preflight -> check_depsgraph.
        Returns a 'GO / NO-GO' status for the proposed mutation."""
        
        # 1. Pre-flight Check
        from .infrastructure import run_adversarial_preflight
        preflight = json.loads(run_adversarial_preflight())
        
        if not preflight.get("safe_to_proceed"):
            return json.dumps({"status": "NO-GO", "reason": "Pre-flight failed", "issues": preflight["issues"]})
        
        # 2. Open Transaction
        blender_request("POST", "/command", data={"type": "system_op", "action": "begin_transaction", "intent": intent}, is_mutation=True)
        
        return json.dumps({"status": "GO", "intent": intent, "ready_for_work_order": True})
