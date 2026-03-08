"""
PHASE 4 — SCRIPT D: Delete Empty Folder Shells
Find all folders that are now empty and move them to Google Trash.
Verify workspace root contains exactly 18 folders.
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, list_files_in_folder, trash_file
)
from config.folder_structure import TARGET_STRUCTURE

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")
TARGET_FOLDER_NAMES = set(TARGET_STRUCTURE.keys())


def is_folder_empty(service, folder_id):
    """Check if a folder is completely empty (no files, no subfolders)."""
    contents = list_files_in_folder(service, folder_id)
    return len(contents) == 0


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
            return False  # Has a real file
    return True


def run():
    print("=" * 60)
    print("PHASE 4 — SCRIPT D: DELETE EMPTY FOLDER SHELLS")
    print("=" * 60)

    service = get_drive_service()

    # List all items at workspace root
    root_items = list_files_in_folder(service, WORKSPACE_FOLDER_ID)
    folders = [f for f in root_items if f["mimeType"] == "application/vnd.google-apps.folder"]

    print(f"\n  Found {len(folders)} folders at workspace root.")
    print(f"  Target: {len(TARGET_FOLDER_NAMES)} folders.\n")

    # Identify folders that are NOT in the target structure
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
            trashed_count += 1
        else:
            print(f"    NOT EMPTY — keeping (needs manual review)")
            kept_count += 1

    # Also check for non-folder files at root level
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

    if len(final_folders) == len(TARGET_FOLDER_NAMES):
        print(f"\nScript D COMPLETE. Exactly {len(TARGET_FOLDER_NAMES)} folders remain.")
    else:
        print(f"\nScript D WARNING: {len(final_folders)} folders remain, expected {len(TARGET_FOLDER_NAMES)}.")
        if kept_count > 0:
            print(f"  {kept_count} non-target folder(s) still have content — review manually.")

    print(f"  Trashed: {trashed_count}")


if __name__ == "__main__":
    run()
