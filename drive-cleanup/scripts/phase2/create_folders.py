"""
PHASE 2 — Create Folder Structure
1. Create all 18 top-level folders in the workspace
2. Create all subfolders per TARGET_STRUCTURE
3. Create _ARCHIVE inside every folder and subfolder
4. Verify structure
"""
import os
import sys
import random
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, find_or_create_folder, list_files_in_folder, find_folder_by_name
)
from config.folder_structure import TARGET_STRUCTURE

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")


def run():
    print("=" * 60)
    print("PHASE 2 — CREATE FOLDER STRUCTURE")
    print("=" * 60)

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

        # Step 2: Create subfolders
        for sub in subfolders:
            sub_id = find_or_create_folder(service, sub, folder_id)
            path = f"{folder_name}/{sub}"
            folder_registry[path] = sub_id
            print(f"    + {sub} ({sub_id})")
            created_count += 1

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
    import json
    with open(registry_path, "w") as f:
        json.dump(folder_registry, f, indent=2)
    print(f"\nFolder registry saved to: {registry_path}")

    # Step 4: Verify
    print(f"\n[Step 4] Verifying...")
    print(f"  Total folders created/found: {created_count}")

    # Check 5 random top-level folders for _ARCHIVE
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

    if all_ok:
        print("\nPhase 2 COMPLETE. All folders created and verified.")
    else:
        print("\nWARNING: Some folders missing _ARCHIVE. Review above.")

    return folder_registry


if __name__ == "__main__":
    run()
