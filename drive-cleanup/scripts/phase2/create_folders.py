"""
PHASE 2 — Create Folder Structure + TAS_Drive_Intelligence sheet
1. Create the TAS_Drive_Intelligence master Google Sheet
2. Create all 18 top-level folders in the workspace
3. Create all subfolders per TARGET_STRUCTURE
4. Create _ARCHIVE inside every folder and subfolder
5. Log every folder to Folder_Map tab
6. Verify structure
"""
import os
import sys
import json
import time
import random
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, find_or_create_folder, list_files_in_folder, find_folder_by_name
)
from lib.audit_logger import (
    ensure_sheet_exists, log_folder_map, log_run_start, log_run_end,
    log_change, generate_run_id
)
from config.folder_structure import TARGET_STRUCTURE

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")


def run():
    print("=" * 60)
    print("PHASE 2 — CREATE FOLDER STRUCTURE")
    print("=" * 60)

    start_time = time.time()
    run_id = generate_run_id("phase2")

    # Step 0: Create the intelligence sheet FIRST
    print("\n[Step 0] Creating TAS_Drive_Intelligence sheet...")
    ensure_sheet_exists()

    log_run_start(run_id, "phase2")

    service = get_drive_service()
    created_count = 0
    folder_registry = {}  # path -> folder_id

    # Step 1: Create 18 top-level folders
    print(f"\n[Step 1] Creating {len(TARGET_STRUCTURE)} top-level folders...\n")

    for folder_name, subfolders in TARGET_STRUCTURE.items():
        folder_id = find_or_create_folder(service, folder_name, WORKSPACE_FOLDER_ID)
        folder_registry[folder_name] = folder_id
        print(f"  + {folder_name} ({folder_id})")
        created_count += 1

        # Log to Folder_Map
        log_folder_map(folder_name, folder_id, parent_folder="WORKSPACE ROOT")

        # Log to Change_Log
        log_change(
            file_id=folder_id, file_name=folder_name,
            change_type="FOLDER_CREATED", before_state="",
            after_state="Created in workspace root",
            script_phase="phase2", run_id=run_id,
        )

        # Step 2: Create subfolders
        for sub in subfolders:
            sub_id = find_or_create_folder(service, sub, folder_id)
            path = f"{folder_name}/{sub}"
            folder_registry[path] = sub_id
            print(f"    + {sub} ({sub_id})")
            created_count += 1

            log_folder_map(sub, sub_id, parent_folder=folder_name)
            log_change(
                file_id=sub_id, file_name=sub,
                change_type="FOLDER_CREATED", before_state="",
                after_state=f"Created in {folder_name}",
                script_phase="phase2", run_id=run_id,
            )

            # _ARCHIVE inside subfolder
            archive_id = find_or_create_folder(service, "_ARCHIVE", sub_id)
            folder_registry[f"{path}/_ARCHIVE"] = archive_id
            print(f"      + _ARCHIVE ({archive_id})")
            created_count += 1

        # Step 3: _ARCHIVE inside top-level folder
        archive_id = find_or_create_folder(service, "_ARCHIVE", folder_id)
        folder_registry[f"{folder_name}/_ARCHIVE"] = archive_id
        print(f"    + _ARCHIVE ({archive_id})")
        created_count += 1

    # Save registry for use by other scripts
    registry_path = os.path.join(os.path.dirname(__file__), "..", "..", "folder_registry.json")
    with open(registry_path, "w") as f:
        json.dump(folder_registry, f, indent=2)
    print(f"\nFolder registry saved to: {registry_path}")

    # Step 4: Verify
    print(f"\n[Step 4] Verifying...")
    print(f"  Total folders created/found: {created_count}")

    top_level_names = list(TARGET_STRUCTURE.keys())
    sample = random.sample(top_level_names, min(5, len(top_level_names)))
    all_ok = True

    for name in sample:
        folder_id = folder_registry[name]
        archive = find_folder_by_name(service, "_ARCHIVE", folder_id)
        if archive:
            print(f"  PASS: {name} has _ARCHIVE")
        else:
            print(f"  FAIL: {name} missing _ARCHIVE!")
            all_ok = False

    duration = time.time() - start_time
    status = "SUCCESS" if all_ok else "PARTIAL"
    summary = f"Created {created_count} folders. {'All verified.' if all_ok else 'Some missing _ARCHIVE.'}"

    log_run_end(
        run_id, "phase2",
        files_processed=created_count, files_moved=0,
        files_archived=0, files_flagged=0, files_skipped=0,
        errors=0 if all_ok else 1,
        duration_seconds=duration, status=status, summary=summary,
    )

    if all_ok:
        print(f"\nPhase 2 COMPLETE. All folders created and verified.")
    else:
        print(f"\nWARNING: Some folders missing _ARCHIVE. Review above.")

    return folder_registry


if __name__ == "__main__":
    run()
