"""
PHASE 4 — SCRIPT C: Consolidate All Old Folders
Move contents of all 32+ old folders to correct new folders per migration map.
Logs EVERY file move to File_Register + Change_Log.
"""
import os
import sys
import time
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, list_files_in_folder, move_file,
    get_folder_id_by_path, find_folder_by_name
)
from lib.audit_logger import (
    log_file_register, log_change,
    log_run_start, log_run_end, generate_run_id,
    get_pending_reviews,
)
from config.folder_structure import MIGRATION_MAP, TARGET_STRUCTURE

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")

NON_CLAUDE_MIGRATIONS = {
    k: v for k, v in MIGRATION_MAP.items()
    if not k.startswith("_CLAUDE/")
}

MERGE_FOLDERS = {"CLIENTS", "PEOPLE", "FINANCE", "HR", "INSURANCE", "MEETINGS",
                 "PERSONAL", "TAS", "TO SORT", "TRAINING", "TRANSCRIPTS", "TRAVEL"}


def resolve_old_folder(service, path):
    """Find an old folder by path (may be nested like DOCUMENTS/NSP)."""
    parts = path.split("/")
    current_id = WORKSPACE_FOLDER_ID
    for part in parts:
        folder_id = find_folder_by_name(service, part, current_id)
        if not folder_id:
            return None
        current_id = folder_id
    return current_id


def run():
    print("=" * 60)
    print("PHASE 4 — SCRIPT C: CONSOLIDATE ALL OLD FOLDERS")
    print("=" * 60)

    start_time = time.time()
    run_id = generate_run_id("phase4c")
    log_run_start(run_id, "phase4c")

    # Check Review_Queue first
    print("\n[Checking Review_Queue...]")
    pending = get_pending_reviews()
    if pending:
        print(f"  {len(pending)} pending review(s) — process via Phase 3 first.")

    service = get_drive_service()
    moved_count = 0
    error_count = 0
    total_processed = 0
    skipped = []

    for old_path, destinations in NON_CLAUDE_MIGRATIONS.items():
        dest_path = destinations[0]

        if old_path == dest_path:
            print(f"\n  SKIP: {old_path} -> {dest_path} (same location)")
            continue

        print(f"\n  Processing: {old_path} -> {dest_path}")

        old_id = resolve_old_folder(service, old_path)
        if not old_id:
            print(f"    NOT FOUND: {old_path}")
            skipped.append(old_path)
            continue

        dest_id = get_folder_id_by_path(service, dest_path, WORKSPACE_FOLDER_ID)
        if not dest_id:
            print(f"    ERROR: Destination not found: {dest_path}")
            error_count += 1
            continue

        contents = list_files_in_folder(service, old_id)
        contents = [f for f in contents if f["name"] != "_ARCHIVE"]

        if not contents:
            print(f"    Empty folder.")
            continue

        for i in range(0, len(contents), 50):
            batch = contents[i:i + 50]
            for f in batch:
                total_processed += 1
                try:
                    move_file(service, f["id"], dest_id, old_id)
                    print(f"    Moved: {f['name']}")

                    log_file_register(
                        file_id=f["id"], file_name=f["name"],
                        file_type=f.get("mimeType", ""),
                        original_location=old_path,
                        new_location=dest_path, folder_id=dest_id,
                        action="MOVED", status="ACTIVE",
                    )
                    log_change(
                        file_id=f["id"], file_name=f["name"],
                        change_type="CONSOLIDATION",
                        before_state=old_path, after_state=dest_path,
                        script_phase="phase4c", run_id=run_id,
                    )
                    moved_count += 1
                except Exception as e:
                    print(f"    ERROR: {f['name']}: {e}")
                    log_change(
                        file_id=f["id"], file_name=f["name"],
                        change_type="CONSOLIDATION_ERROR",
                        before_state=old_path, after_state=f"ERROR: {e}",
                        script_phase="phase4c", run_id=run_id,
                    )
                    error_count += 1

    # Verify
    print("\n[Verifying old folders are empty...]")
    non_empty = []
    for old_path in NON_CLAUDE_MIGRATIONS:
        if old_path in MERGE_FOLDERS or old_path == NON_CLAUDE_MIGRATIONS[old_path][0]:
            continue
        old_id = resolve_old_folder(service, old_path)
        if old_id:
            contents = list_files_in_folder(service, old_id)
            real = [f for f in contents if f["name"] != "_ARCHIVE"]
            if real:
                non_empty.append(old_path)

    if non_empty:
        print(f"  WARNING: These folders still have files: {non_empty}")
    else:
        print("  All old folders are empty.")

    duration = time.time() - start_time
    status = "SUCCESS" if error_count == 0 else "PARTIAL"
    log_run_end(
        run_id, "phase4c",
        files_processed=total_processed, files_moved=moved_count,
        files_skipped=len(skipped), errors=error_count,
        duration_seconds=duration, status=status,
        summary=f"Moved {moved_count}, Errors {error_count}, Skipped {len(skipped)}",
    )

    print(f"\nScript C COMPLETE. Moved: {moved_count}, Errors: {error_count}, Skipped: {len(skipped)}")


if __name__ == "__main__":
    run()
