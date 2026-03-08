"""
PHASE 4 — SCRIPT D: Delete Empty Folder Shells
Find all folders that are now empty and move them to Google Trash.
Verify workspace root contains exactly 18 folders.
Logs EVERY deletion to File_Register + Change_Log.
"""
import os
import sys
import time
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, list_files_in_folder, trash_file
)
from lib.audit_logger import (
    log_file_register, log_change,
    log_run_start, log_run_end, generate_run_id,
)
from config.folder_structure import TARGET_STRUCTURE

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")
TARGET_FOLDER_NAMES = set(TARGET_STRUCTURE.keys())


def is_folder_effectively_empty(service, folder_id):
    """Check if a folder only contains empty subfolders (recursive)."""
    contents = list_files_in_folder(service, folder_id)
    if not contents:
        return True
    for item in contents:
        if item["mimeType"] == "application/vnd.google-apps.folder":
            if not is_folder_effectively_empty(service, item["id"]):
                return False
        else:
            return False
    return True


def run():
    print("=" * 60)
    print("PHASE 4 — SCRIPT D: DELETE EMPTY FOLDER SHELLS")
    print("=" * 60)

    start_time = time.time()
    run_id = generate_run_id("phase4d")
    log_run_start(run_id, "phase4d")

    service = get_drive_service()

    root_items = list_files_in_folder(service, WORKSPACE_FOLDER_ID)
    folders = [f for f in root_items if f["mimeType"] == "application/vnd.google-apps.folder"]

    print(f"\n  Found {len(folders)} folders at workspace root.")
    print(f"  Target: {len(TARGET_FOLDER_NAMES)} folders.\n")

    non_target = [f for f in folders if f["name"] not in TARGET_FOLDER_NAMES]
    target = [f for f in folders if f["name"] in TARGET_FOLDER_NAMES]

    print(f"  Target folders present: {len(target)}")
    print(f"  Non-target folders: {len(non_target)}")

    trashed_count = 0
    kept_count = 0

    for folder in non_target:
        print(f"\n  Checking: {folder['name']}")
        if is_folder_effectively_empty(service, folder["id"]):
            print(f"    EMPTY — moving to Trash")
            trash_file(service, folder["id"])

            log_file_register(
                file_id=folder["id"], file_name=folder["name"],
                file_type="folder", original_location="WORKSPACE ROOT",
                new_location="TRASH", action="ARCHIVED",
                version_notes="Empty folder shell trashed",
                status="DELETED",
            )
            log_change(
                file_id=folder["id"], file_name=folder["name"],
                change_type="FOLDER_TRASHED",
                before_state="WORKSPACE ROOT",
                after_state="TRASH (empty folder shell)",
                script_phase="phase4d", run_id=run_id,
            )
            trashed_count += 1
        else:
            print(f"    NOT EMPTY — keeping (needs manual review)")
            log_change(
                file_id=folder["id"], file_name=folder["name"],
                change_type="FOLDER_KEPT",
                before_state="WORKSPACE ROOT",
                after_state="KEPT (non-empty, needs review)",
                script_phase="phase4d", run_id=run_id,
            )
            kept_count += 1

    # Check for loose files at root
    root_files = [f for f in root_items if f["mimeType"] != "application/vnd.google-apps.folder"]
    if root_files:
        print(f"\n  WARNING: {len(root_files)} loose file(s) at workspace root:")
        for f in root_files:
            print(f"    - {f['name']}")

    # Verify final state
    print("\n[Verifying final state...]")
    final_items = list_files_in_folder(service, WORKSPACE_FOLDER_ID)
    final_folders = [f for f in final_items if f["mimeType"] == "application/vnd.google-apps.folder"]

    print(f"  Folders at root: {len(final_folders)} (target: {len(TARGET_FOLDER_NAMES)})")
    for f in sorted(final_folders, key=lambda x: x["name"]):
        in_target = "OK" if f["name"] in TARGET_FOLDER_NAMES else "UNEXPECTED"
        print(f"    [{in_target}] {f['name']}")

    duration = time.time() - start_time
    ok = len(final_folders) == len(TARGET_FOLDER_NAMES)
    log_run_end(
        run_id, "phase4d",
        files_processed=len(non_target),
        files_archived=trashed_count, files_skipped=kept_count,
        errors=0, duration_seconds=duration,
        status="SUCCESS" if ok else "PARTIAL",
        summary=f"Trashed {trashed_count} empty shells, kept {kept_count}. {len(final_folders)} folders at root.",
    )

    if ok:
        print(f"\nScript D COMPLETE. Exactly {len(TARGET_FOLDER_NAMES)} folders remain.")
    else:
        print(f"\nScript D WARNING: {len(final_folders)} folders remain, expected {len(TARGET_FOLDER_NAMES)}.")
    print(f"  Trashed: {trashed_count}")


if __name__ == "__main__":
    run()
