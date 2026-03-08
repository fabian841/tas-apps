"""
PHASE 4 — SCRIPT F: Archive Old Files
Find all files not modified since 08/03/2025 (12 months ago).
Move to _ARCHIVE subfolder within current folder.
Logs EVERY archive action to File_Register + Change_Log.
"""
import os
import sys
import time
from datetime import datetime, timezone
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
CUTOFF_DATE = datetime(2025, 3, 8, tzinfo=timezone.utc)


def archive_old_in_folder(service, folder_id, folder_path="", run_id=""):
    """Recursively find and archive files older than cutoff date."""
    items = list_files_in_folder(service, folder_id)
    archived_count = 0
    errors = 0

    files = []
    subfolders = []

    for item in items:
        if item["mimeType"] == "application/vnd.google-apps.folder":
            if item["name"] != "_ARCHIVE":
                subfolders.append(item)
        else:
            files.append(item)

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

                    log_file_register(
                        file_id=f["id"], file_name=archive_name,
                        file_type=f.get("mimeType", ""),
                        original_location=folder_path,
                        new_location=f"{folder_path}/_ARCHIVE",
                        folder_id=archive_id, action="ARCHIVED",
                        version_notes=f"Last modified: {f.get('modifiedTime', '?')}. Older than 12 months.",
                        status="ARCHIVED",
                    )
                    log_change(
                        file_id=f["id"], file_name=f["name"],
                        change_type="OLD_FILE_ARCHIVED",
                        before_state=folder_path,
                        after_state=f"{folder_path}/_ARCHIVE (renamed to {archive_name})",
                        script_phase="phase4f", run_id=run_id,
                        notes=f"Last modified: {f.get('modifiedTime', '')}",
                    )
                    archived_count += 1
                except Exception as e:
                    print(f"  ERROR: {f['name']}: {e}")
                    log_change(
                        file_id=f["id"], file_name=f["name"],
                        change_type="ARCHIVE_ERROR",
                        before_state=folder_path,
                        after_state=f"ERROR: {e}",
                        script_phase="phase4f", run_id=run_id,
                    )
                    errors += 1

    for sub in subfolders:
        sub_path = f"{folder_path}/{sub['name']}" if folder_path else sub["name"]
        sub_archived, sub_errors = archive_old_in_folder(service, sub["id"], sub_path, run_id)
        archived_count += sub_archived
        errors += sub_errors

    return archived_count, errors


def run():
    print("=" * 60)
    print("PHASE 4 — SCRIPT F: ARCHIVE OLD FILES")
    print(f"Cutoff date: {CUTOFF_DATE.strftime('%Y-%m-%d')}")
    print("=" * 60)

    start_time = time.time()
    run_id = generate_run_id("phase4f")
    log_run_start(run_id, "phase4f")

    # Check Review_Queue first
    print("\n[Checking Review_Queue...]")
    pending = get_pending_reviews()
    if pending:
        print(f"  {len(pending)} pending review(s) — process via Phase 3 first.")

    service = get_drive_service()

    print("\n[Scanning for files older than 12 months...]")
    total, errors = archive_old_in_folder(service, WORKSPACE_FOLDER_ID, run_id=run_id)

    duration = time.time() - start_time
    log_run_end(
        run_id, "phase4f",
        files_processed=total + errors, files_archived=total,
        errors=errors, duration_seconds=duration,
        status="SUCCESS" if errors == 0 else "PARTIAL",
        summary=f"Archived {total} old files, {errors} errors.",
    )

    print(f"\nScript F COMPLETE. Archived {total} old file(s).")


if __name__ == "__main__":
    run()
