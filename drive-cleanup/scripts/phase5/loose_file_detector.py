"""
PHASE 5 — Loose File Detector
Runs on daily schedule. Finds files sitting directly in top-level folders
(not in subfolders) and moves them to TO SORT.
Checks Review_Queue first. Logs EVERY move to File_Register + Change_Log.
"""
import os
import sys
import time
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, list_files_in_folder, move_file, get_folder_id_by_path
)
from lib.audit_logger import (
    log_file_register, log_change,
    log_run_start, log_run_end, generate_run_id,
    get_pending_reviews,
)
from config.folder_structure import TARGET_STRUCTURE

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")
EXEMPT_FOLDERS = {"TO SORT", "_CLAUDE"}


def detect_and_move_loose_files(service, run_id):
    """Find loose files in top-level folders and move to TO SORT."""
    to_sort_id = get_folder_id_by_path(service, "TO SORT", WORKSPACE_FOLDER_ID)
    if not to_sort_id:
        print("ERROR: TO SORT folder not found!")
        return 0, 0

    moved_count = 0
    error_count = 0
    root_items = list_files_in_folder(service, WORKSPACE_FOLDER_ID)

    # Files directly at workspace root
    root_files = [f for f in root_items if f["mimeType"] != "application/vnd.google-apps.folder"]
    for f in root_files:
        print(f"  Loose at root: {f['name']} -> TO SORT")
        try:
            move_file(service, f["id"], to_sort_id, WORKSPACE_FOLDER_ID)

            log_file_register(
                file_id=f["id"], file_name=f["name"],
                file_type=f.get("mimeType", ""),
                original_location="WORKSPACE ROOT",
                new_location="TO SORT", folder_id=to_sort_id,
                action="MOVED", status="ACTIVE",
            )
            log_change(
                file_id=f["id"], file_name=f["name"],
                change_type="LOOSE_FILE_MOVED",
                before_state="WORKSPACE ROOT",
                after_state="TO SORT",
                script_phase="phase5", run_id=run_id,
            )
            moved_count += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            error_count += 1

    # Check each top-level folder
    top_folders = [f for f in root_items if f["mimeType"] == "application/vnd.google-apps.folder"]

    for folder in top_folders:
        if folder["name"] in EXEMPT_FOLDERS:
            continue

        contents = list_files_in_folder(service, folder["id"])
        loose = [f for f in contents if f["mimeType"] != "application/vnd.google-apps.folder"]

        for f in loose:
            print(f"  Loose in {folder['name']}: {f['name']} -> TO SORT")
            try:
                move_file(service, f["id"], to_sort_id, folder["id"])

                log_file_register(
                    file_id=f["id"], file_name=f["name"],
                    file_type=f.get("mimeType", ""),
                    original_location=folder["name"],
                    new_location="TO SORT", folder_id=to_sort_id,
                    action="MOVED", status="ACTIVE",
                )
                log_change(
                    file_id=f["id"], file_name=f["name"],
                    change_type="LOOSE_FILE_MOVED",
                    before_state=folder["name"],
                    after_state="TO SORT",
                    script_phase="phase5", run_id=run_id,
                )
                moved_count += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                error_count += 1

    return moved_count, error_count


def run_once():
    """Single run of the detector."""
    print("=" * 60)
    print("PHASE 5 — LOOSE FILE DETECTOR (single run)")
    print("=" * 60)

    start_time = time.time()
    run_id = generate_run_id("phase5")
    log_run_start(run_id, "phase5")

    # Check Review_Queue first
    print("\n[Checking Review_Queue...]")
    pending = get_pending_reviews()
    if pending:
        print(f"  {len(pending)} pending review(s) — process via Phase 3 first.")

    service = get_drive_service()
    moved, errors = detect_and_move_loose_files(service, run_id)

    duration = time.time() - start_time
    log_run_end(
        run_id, "phase5",
        files_processed=moved + errors, files_moved=moved,
        errors=errors, duration_seconds=duration,
        status="SUCCESS" if errors == 0 else "PARTIAL",
        summary=f"Moved {moved} loose files to TO SORT. {errors} errors.",
    )

    print(f"\nMoved {moved} loose file(s) to TO SORT.")
    return moved


def run_scheduled(interval_hours=24):
    """Scheduled mode — runs every N hours."""
    print("=" * 60)
    print(f"PHASE 5 — LOOSE FILE DETECTOR (every {interval_hours}h)")
    print("=" * 60)

    while True:
        try:
            moved = run_once()
            print(f"\n  [{time.strftime('%Y-%m-%d %H:%M')}] Moved {moved} loose file(s).")
        except Exception as e:
            print(f"\n  ERROR: {e}")
        time.sleep(interval_hours * 3600)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once")
    parser.add_argument("--schedule", action="store_true", help="Run on schedule")
    parser.add_argument("--interval", type=int, default=24, help="Hours between runs")
    args = parser.parse_args()

    if args.once:
        run_once()
    elif args.schedule:
        run_scheduled(args.interval)
    else:
        print("Usage: python loose_file_detector.py --once | --schedule [--interval 24]")
