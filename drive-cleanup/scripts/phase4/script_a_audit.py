"""
PHASE 4 — SCRIPT A: Full Workspace Audit
Scan entire workspace. List every file with metadata.
Flag files not modified in 12+ months and zero-size/stub files.
Logs EVERY file to File_Register + Change_Log.
"""
import os
import sys
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import get_drive_service, list_files_in_folder
from lib.audit_logger import (
    log_file_register, log_change, log_review_item,
    log_run_start, log_run_end, generate_run_id,
    get_pending_reviews, mark_review_resolved,
)

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")
TWELVE_MONTHS_AGO = datetime(2025, 3, 8, tzinfo=timezone.utc)

STUB_MIME_TYPES = {
    "application/vnd.google-apps.shortcut",
}


def scan_folder_recursive(service, folder_id, path="", run_id=""):
    """Recursively scan a folder and return all files with metadata."""
    items = list_files_in_folder(service, folder_id)
    results = []
    stubs = []
    old_files = []

    for item in items:
        item_path = f"{path}/{item['name']}" if path else item["name"]

        if item["mimeType"] == "application/vnd.google-apps.folder":
            sub_results, sub_stubs, sub_old = scan_folder_recursive(
                service, item["id"], item_path, run_id
            )
            results.extend(sub_results)
            stubs.extend(sub_stubs)
            old_files.extend(sub_old)
        else:
            size = item.get("size", "0")
            modified = item.get("modifiedTime", "")
            mime = item.get("mimeType", "")

            flags = []
            is_stub = (
                mime in STUB_MIME_TYPES
                or item.get("shortcutDetails") is not None
                or size == "0"
            )
            if is_stub:
                flags.append("STUB")
                stubs.append({
                    "name": item["name"], "id": item["id"],
                    "location": item_path, "size": size, "type": mime,
                })

            is_old = False
            if modified:
                try:
                    mod_dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                    if mod_dt < TWELVE_MONTHS_AGO:
                        flags.append("OLD_12M+")
                        is_old = True
                        old_files.append({
                            "name": item["name"], "id": item["id"],
                            "location": item_path, "modified": modified,
                        })
                except ValueError:
                    pass

            results.append({
                "name": item["name"], "id": item["id"],
                "location": item_path, "type": mime,
                "modified": modified, "size": size,
                "flags": ", ".join(flags) if flags else "",
            })

            # Log EVERY file to File_Register
            action = "FLAGGED" if (is_stub or is_old) else "SKIPPED"
            flag_str = ", ".join(flags) if flags else ""
            log_file_register(
                file_id=item["id"], file_name=item["name"],
                file_type=mime, original_location=item_path,
                new_location=item_path, action=action,
                version_notes=f"Size: {size}, Modified: {modified}",
                status="ACTIVE" if not is_stub else "FLAGGED",
            )

            # Log flagged items to Change_Log
            if flags:
                log_change(
                    file_id=item["id"], file_name=item["name"],
                    change_type="AUDIT_FLAG", before_state=item_path,
                    after_state=f"Flagged: {flag_str}",
                    script_phase="phase4a", run_id=run_id,
                    notes=f"Size: {size}, Modified: {modified}",
                )

    return results, stubs, old_files


def run():
    print("=" * 60)
    print("PHASE 4 — SCRIPT A: FULL WORKSPACE AUDIT")
    print("=" * 60)

    start_time = time.time()
    run_id = generate_run_id("phase4a")
    log_run_start(run_id, "phase4a")

    # Check Review_Queue first
    print("\n[Checking Review_Queue...]")
    pending = get_pending_reviews()
    if pending:
        print(f"  {len(pending)} pending review(s) — these will be processed by Phase 3.")

    service = get_drive_service()

    print("\n[Scanning workspace recursively...]")
    all_files, stubs, old_files = scan_folder_recursive(
        service, WORKSPACE_FOLDER_ID, run_id=run_id
    )

    print(f"\n  Total files found: {len(all_files)}")
    print(f"  Stub/zero-size files: {len(stubs)}")
    print(f"  Files older than 12 months: {len(old_files)}")

    duration = time.time() - start_time
    log_run_end(
        run_id, "phase4a",
        files_processed=len(all_files), files_moved=0,
        files_archived=0, files_flagged=len(stubs) + len(old_files),
        files_skipped=len(all_files) - len(stubs) - len(old_files),
        errors=0, duration_seconds=duration,
        status="SUCCESS",
        summary=f"Audited {len(all_files)} files. {len(stubs)} stubs, {len(old_files)} old.",
    )

    print(f"\nScript A COMPLETE. {len(all_files)} files audited.")
    return all_files, stubs, old_files


if __name__ == "__main__":
    run()
