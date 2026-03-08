"""
PHASE 4 — SCRIPT F: Archive Old Files
Find all files not modified since 08/03/2025 (12 months ago).
Move to _ARCHIVE subfolder within current folder.
"""
import os
import sys
from datetime import datetime, timezone
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
CUTOFF_DATE = datetime(2025, 3, 8, tzinfo=timezone.utc)


def archive_old_in_folder(service, folder_id, folder_path=""):
    """Recursively find and archive files older than cutoff date."""
    items = list_files_in_folder(service, folder_id)
    archived_count = 0

    files = []
    subfolders = []

    for item in items:
        if item["mimeType"] == "application/vnd.google-apps.folder":
            if item["name"] != "_ARCHIVE":
                subfolders.append(item)
        else:
            files.append(item)

    # Check each file's modified date
    old_files = []
    for f in files:
        modified = f.get("modifiedTime", "")
        if not modified:
            continue
        try:
            mod_dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
            if mod_dt < CUTOFF_DATE:
                old_files.append(f)
        except ValueError:
            continue

    if old_files:
        archive_id = find_or_create_folder(service, "_ARCHIVE", folder_id)

        for i in range(0, len(old_files), 50):
            batch = old_files[i:i + 50]
            for f in batch:
                archive_name = generate_archive_name(f["name"])
                try:
                    rename_file(service, f["id"], archive_name)
                    move_file(service, f["id"], archive_id, folder_id)
                    print(f"  Archived: {folder_path}/{f['name']} (last modified: {f.get('modifiedTime', '?')})")
                    log_action("ARCHIVED", [
                        f["name"], f["id"], folder_path, f"{folder_path}/_ARCHIVE",
                        f.get("modifiedTime", ""), "Older than 12 months"
                    ])
                    archived_count += 1
                except Exception as e:
                    print(f"  ERROR: {f['name']}: {e}")
                    log_action("ARCHIVED", [
                        f["name"], f["id"], folder_path, f"{folder_path}/_ARCHIVE",
                        f.get("modifiedTime", ""), f"ERROR: {e}"
                    ])

    # Recurse
    for sub in subfolders:
        sub_path = f"{folder_path}/{sub['name']}" if folder_path else sub["name"]
        archived_count += archive_old_in_folder(service, sub["id"], sub_path)

    return archived_count


def run():
    print("=" * 60)
    print("PHASE 4 — SCRIPT F: ARCHIVE OLD FILES")
    print(f"Cutoff date: {CUTOFF_DATE.strftime('%Y-%m-%d')}")
    print("=" * 60)

    service = get_drive_service()

    print("\n[Scanning for files older than 12 months...]")
    total = archive_old_in_folder(service, WORKSPACE_FOLDER_ID)

    print(f"\nScript F COMPLETE. Archived {total} old file(s).")


if __name__ == "__main__":
    run()
