"""
PHASE 4 — SCRIPT E: Find and Archive Duplicates
Find files with identical names in the same folder.
Keep newest, archive older versions.
"""
import os
import sys
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, list_files_in_folder, move_file,
    rename_file, find_or_create_folder
)
from lib.filing_engine import generate_archive_name
from lib.audit_logger import log_action

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")


def find_duplicates_in_folder(service, folder_id, folder_path=""):
    """Recursively find duplicate files (same name) in each folder."""
    items = list_files_in_folder(service, folder_id)
    duplicates_found = 0

    # Group files by name (excluding folders)
    files_by_name = defaultdict(list)
    subfolders = []

    for item in items:
        if item["mimeType"] == "application/vnd.google-apps.folder":
            if item["name"] != "_ARCHIVE":
                subfolders.append(item)
        else:
            files_by_name[item["name"]].append(item)

    # Process duplicates in this folder
    for name, file_list in files_by_name.items():
        if len(file_list) <= 1:
            continue

        # Sort by modifiedTime descending (newest first)
        file_list.sort(
            key=lambda f: f.get("modifiedTime", ""),
            reverse=True,
        )
        newest = file_list[0]
        older = file_list[1:]

        print(f"\n  Duplicate: {name} in {folder_path or 'root'}")
        print(f"    Keeping: {newest['id']} (modified: {newest.get('modifiedTime', '?')})")

        # Find or create _ARCHIVE in this folder
        archive_id = find_or_create_folder(service, "_ARCHIVE", folder_id)

        for old in older:
            archive_name = generate_archive_name(old["name"])
            print(f"    Archiving: {old['id']} -> _ARCHIVE as {archive_name}")

            try:
                rename_file(service, old["id"], archive_name)
                move_file(service, old["id"], archive_id, folder_id)
                log_action("DUPLICATES", [
                    name, old["id"], folder_path, newest["id"], old["id"], "ARCHIVED"
                ])
                duplicates_found += 1
            except Exception as e:
                print(f"    ERROR: {e}")
                log_action("DUPLICATES", [
                    name, old["id"], folder_path, newest["id"], old["id"], f"ERROR: {e}"
                ])

    # Recurse into subfolders
    for sub in subfolders:
        sub_path = f"{folder_path}/{sub['name']}" if folder_path else sub["name"]
        duplicates_found += find_duplicates_in_folder(service, sub["id"], sub_path)

    return duplicates_found


def run():
    print("=" * 60)
    print("PHASE 4 — SCRIPT E: FIND AND ARCHIVE DUPLICATES")
    print("=" * 60)

    service = get_drive_service()

    print("\n[Scanning for duplicates...]")
    total = find_duplicates_in_folder(service, WORKSPACE_FOLDER_ID)

    print(f"\nScript E COMPLETE. Archived {total} duplicate file(s).")


if __name__ == "__main__":
    run()
