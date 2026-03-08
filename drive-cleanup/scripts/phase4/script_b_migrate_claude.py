"""
PHASE 4 — SCRIPT B: Migrate _CLAUDE old numbered subfolders
Move contents of each numbered subfolder to correct new folder per migration map.
"""
import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, list_files_in_folder, move_file,
    get_folder_id_by_path, find_folder_by_name
)
from lib.audit_logger import log_action
from config.folder_structure import MIGRATION_MAP

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")

# Only _CLAUDE subfolders for Script B
CLAUDE_MIGRATIONS = {
    k: v for k, v in MIGRATION_MAP.items() if k.startswith("_CLAUDE/")
}


def run():
    print("=" * 60)
    print("PHASE 4 — SCRIPT B: MIGRATE _CLAUDE SUBFOLDERS")
    print("=" * 60)

    service = get_drive_service()

    # Find _CLAUDE folder
    claude_id = find_folder_by_name(service, "_CLAUDE", WORKSPACE_FOLDER_ID)
    if not claude_id:
        print("ERROR: _CLAUDE folder not found!")
        return

    claude_subfolders = list_files_in_folder(service, claude_id)
    moved_count = 0
    error_count = 0

    for old_path, destinations in CLAUDE_MIGRATIONS.items():
        subfolder_name = old_path.split("/", 1)[1]  # e.g., "01-BIZ BUSINESS"
        print(f"\n  Processing: {subfolder_name}")

        # Find the subfolder
        sub = next(
            (f for f in claude_subfolders if f["name"] == subfolder_name),
            None
        )
        if not sub:
            print(f"    NOT FOUND: {subfolder_name}")
            continue

        sub_id = sub["id"]
        files = list_files_in_folder(service, sub_id)
        files = [f for f in files if f["mimeType"] != "application/vnd.google-apps.folder" or f["name"] != "_ARCHIVE"]

        if not files:
            print(f"    Empty folder, skipping.")
            continue

        # Determine destination
        dest_path = destinations[0]  # Primary destination
        dest_id = get_folder_id_by_path(service, dest_path, WORKSPACE_FOLDER_ID)

        if not dest_id:
            print(f"    ERROR: Destination not found: {dest_path}")
            error_count += len(files)
            continue

        # Move files in batches of 50
        for i in range(0, len(files), 50):
            batch = files[i:i + 50]
            for f in batch:
                try:
                    move_file(service, f["id"], dest_id, sub_id)
                    print(f"    Moved: {f['name']} -> {dest_path}")
                    log_action("MIGRATION", [
                        f["name"], f["id"], old_path, dest_path, "OK"
                    ])
                    moved_count += 1
                except Exception as e:
                    print(f"    ERROR moving {f['name']}: {e}")
                    log_action("MIGRATION", [
                        f["name"], f["id"], old_path, dest_path, f"ERROR: {e}"
                    ])
                    error_count += 1

    # Verify: check all numbered folders are empty
    print("\n[Verifying _CLAUDE subfolders are empty...]")
    claude_subfolders = list_files_in_folder(service, claude_id)
    non_empty = []
    for sub in claude_subfolders:
        if sub["mimeType"] == "application/vnd.google-apps.folder" and sub["name"] != "_ARCHIVE":
            contents = list_files_in_folder(service, sub["id"])
            real_contents = [f for f in contents if f["name"] != "_ARCHIVE"]
            if real_contents:
                non_empty.append(sub["name"])

    if non_empty:
        print(f"  WARNING: These _CLAUDE subfolders still have files: {non_empty}")
    else:
        print("  All _CLAUDE numbered subfolders are empty.")

    print(f"\nScript B COMPLETE. Moved: {moved_count}, Errors: {error_count}")


if __name__ == "__main__":
    run()
