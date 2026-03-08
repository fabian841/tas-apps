"""
PHASE 4 — SCRIPT E: Find and Archive Duplicates
Find files with identical names in the same folder.
Keep newest, archive older versions.
Logs EVERY duplicate action to File_Register + Change_Log.
"""
import os
import sys
import time
from collections import defaultdict
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, list_files_in_folder, move_file,
    rename_file, find_or_create_folder
)
from lib.filing_engine import generate_archive_name
from lib.audit_logger import (
    log_file_register, log_change,
    log_run_start, log_run_end, generate_run_id,
    get_pending_reviews,
)

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")


def find_duplicates_in_folder(service, folder_id, folder_path="", run_id=""):
    """Recursively find duplicate files (same name) in each folder."""
    items = list_files_in_folder(service, folder_id)
    duplicates_found = 0
    errors = 0

    files_by_name = defaultdict(list)
    subfolders = []

    for item in items:
        if item["mimeType"] == "application/vnd.google-apps.folder":
            if item["name"] != "_ARCHIVE":
                subfolders.append(item)
        else:
            files_by_name[item["name"]].append(item)

    for name, file_list in files_by_name.items():
        if len(file_list) <= 1:
            continue

        file_list.sort(key=lambda f: f.get("modifiedTime", ""), reverse=True)
        newest = file_list[0]
        older = file_list[1:]

        print(f"\n  Duplicate: {name} in {folder_path or 'root'}")
        print(f"    Keeping: {newest['id']} (modified: {newest.get('modifiedTime', '?')})")

        archive_id = find_or_create_folder(service, "_ARCHIVE", folder_id)

        for old in older:
            archive_name = generate_archive_name(old["name"])
            print(f"    Archiving: {old['id']} -> _ARCHIVE as {archive_name}")

            try:
                rename_file(service, old["id"], archive_name)
                move_file(service, old["id"], archive_id, folder_id)

                log_file_register(
                    file_id=old["id"], file_name=archive_name,
                    file_type=old.get("mimeType", ""),
                    original_location=folder_path,
                    new_location=f"{folder_path}/_ARCHIVE",
                    folder_id=archive_id, action="ARCHIVED",
                    version_notes=f"Duplicate of {name}. Kept: {newest['id']}",
                    supersedes_file_id=newest["id"],
                    status="ARCHIVED",
                )
                log_change(
                    file_id=old["id"], file_name=name,
                    change_type="DUPLICATE_ARCHIVED",
                    before_state=folder_path,
                    after_state=f"{folder_path}/_ARCHIVE (renamed to {archive_name})",
                    script_phase="phase4e", run_id=run_id,
                    notes=f"Kept newest: {newest['id']} ({newest.get('modifiedTime', '?')})",
                )
                duplicates_found += 1
            except Exception as e:
                print(f"    ERROR: {e}")
                log_change(
                    file_id=old["id"], file_name=name,
                    change_type="DUPLICATE_ERROR",
                    before_state=folder_path,
                    after_state=f"ERROR: {e}",
                    script_phase="phase4e", run_id=run_id,
                )
                errors += 1

    for sub in subfolders:
        sub_path = f"{folder_path}/{sub['name']}" if folder_path else sub["name"]
        sub_dupes, sub_errors = find_duplicates_in_folder(service, sub["id"], sub_path, run_id)
        duplicates_found += sub_dupes
        errors += sub_errors

    return duplicates_found, errors


def run():
    print("=" * 60)
    print("PHASE 4 — SCRIPT E: FIND AND ARCHIVE DUPLICATES")
    print("=" * 60)

    start_time = time.time()
    run_id = generate_run_id("phase4e")
    log_run_start(run_id, "phase4e")

    # Check Review_Queue first
    print("\n[Checking Review_Queue...]")
    pending = get_pending_reviews()
    if pending:
        print(f"  {len(pending)} pending review(s) — process via Phase 3 first.")

    service = get_drive_service()

    print("\n[Scanning for duplicates...]")
    total, errors = find_duplicates_in_folder(service, WORKSPACE_FOLDER_ID, run_id=run_id)

    duration = time.time() - start_time
    log_run_end(
        run_id, "phase4e",
        files_processed=total + errors, files_archived=total,
        errors=errors, duration_seconds=duration,
        status="SUCCESS" if errors == 0 else "PARTIAL",
        summary=f"Archived {total} duplicates, {errors} errors.",
    )

    print(f"\nScript E COMPLETE. Archived {total} duplicate file(s).")


if __name__ == "__main__":
    run()
