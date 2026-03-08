"""
PHASE 1 — n8n Cleanup
1. Connect to n8n API
2. List all workflows (name, status, last modified)
3. Show list to Fabian for approval
4. Pause active workflows
5. Delete confirmed workflows
6. Verify final state
"""
import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

N8N_BASE_URL = os.environ.get("N8N_BASE_URL", "").rstrip("/")
N8N_API_KEY = os.environ.get("N8N_API_KEY", "")


def get_headers():
    return {"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"}


def list_workflows():
    """List all workflows with name, status, last modified."""
    url = f"{N8N_BASE_URL}/api/v1/workflows"
    resp = requests.get(url, headers=get_headers())
    resp.raise_for_status()
    data = resp.json()
    workflows = data.get("data", [])
    result = []
    for wf in workflows:
        result.append({
            "id": wf["id"],
            "name": wf["name"],
            "active": wf.get("active", False),
            "updatedAt": wf.get("updatedAt", "unknown"),
        })
    return result


def deactivate_workflow(wf_id):
    """Deactivate (pause) a workflow."""
    url = f"{N8N_BASE_URL}/api/v1/workflows/{wf_id}/deactivate"
    resp = requests.post(url, headers=get_headers())
    resp.raise_for_status()
    return resp.json()


def delete_workflow(wf_id):
    """Delete a workflow."""
    url = f"{N8N_BASE_URL}/api/v1/workflows/{wf_id}"
    resp = requests.delete(url, headers=get_headers())
    resp.raise_for_status()
    return True


def run():
    """Main execution for Phase 1."""
    if not N8N_BASE_URL or not N8N_API_KEY:
        print("ERROR: N8N_BASE_URL and N8N_API_KEY must be set in .env")
        sys.exit(1)

    print("=" * 60)
    print("PHASE 1 — n8n CLEANUP")
    print("=" * 60)

    # Step 1: List all workflows
    print("\n[Step 1] Listing all workflows...\n")
    workflows = list_workflows()

    if not workflows:
        print("No workflows found. Phase 1 complete.")
        return

    print(f"Found {len(workflows)} workflow(s):\n")
    print(f"{'#':<4} {'ID':<8} {'Status':<10} {'Last Modified':<22} {'Name'}")
    print("-" * 80)
    for i, wf in enumerate(workflows, 1):
        status = "ACTIVE" if wf["active"] else "inactive"
        print(f"{i:<4} {wf['id']:<8} {status:<10} {wf['updatedAt']:<22} {wf['name']}")

    # Step 2: Save list for Fabian's review
    output_file = os.path.join(os.path.dirname(__file__), "..", "..", "n8n_workflows.json")
    with open(output_file, "w") as f:
        json.dump(workflows, f, indent=2)
    print(f"\nWorkflow list saved to: {output_file}")

    # Step 3: Wait for confirmation
    print("\n" + "=" * 60)
    print("ACTION REQUIRED: Review the workflow list above.")
    print("Enter the IDs of workflows to DELETE (comma-separated),")
    print("or 'skip' to keep all workflows:")
    print("=" * 60)
    user_input = input("> ").strip()

    if user_input.lower() == "skip":
        print("Skipping workflow deletion. Phase 1 complete.")
        return

    delete_ids = [x.strip() for x in user_input.split(",") if x.strip()]
    if not delete_ids:
        print("No IDs provided. Skipping deletion.")
        return

    # Step 4: Pause all active workflows first
    print("\n[Step 4] Pausing all active workflows...")
    for wf in workflows:
        if wf["active"]:
            print(f"  Deactivating: {wf['name']} (ID: {wf['id']})")
            deactivate_workflow(wf["id"])
            time.sleep(0.5)

    # Step 5: Delete confirmed workflows
    print("\n[Step 5] Deleting confirmed workflows...")
    for wf_id in delete_ids:
        wf_name = next((w["name"] for w in workflows if str(w["id"]) == wf_id), "unknown")
        print(f"  Deleting: {wf_name} (ID: {wf_id})")
        delete_workflow(wf_id)
        time.sleep(0.5)

    # Step 6: Verify
    print("\n[Step 6] Verifying final state...")
    remaining = list_workflows()
    print(f"\nRemaining workflows: {len(remaining)}")
    for wf in remaining:
        status = "ACTIVE" if wf["active"] else "inactive"
        print(f"  {wf['id']} | {status} | {wf['name']}")

    deleted_still_present = [wf for wf in remaining if str(wf["id"]) in delete_ids]
    if deleted_still_present:
        print("\nWARNING: Some workflows were not deleted:")
        for wf in deleted_still_present:
            print(f"  {wf['id']} | {wf['name']}")
    else:
        print("\nPhase 1 COMPLETE. All confirmed workflows deleted.")


if __name__ == "__main__":
    run()
