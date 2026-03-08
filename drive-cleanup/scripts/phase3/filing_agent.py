"""
PHASE 3 — Filing Agent (TO SORT watcher)
1. Check Review_Queue for PENDING items with Fabian's instructions — process FIRST
2. Watch the TO SORT folder for new files
3. Classify each file using filing rules
4. Move to correct folder if confidence >= 70%
5. Leave and flag if confidence < 70% — add to Review_Queue
6. Log EVERY file action to File_Register + Change_Log
"""
import os
import sys
import time
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, list_files_in_folder, move_file, rename_file,
    get_file_content, get_folder_id_by_path, find_or_create_folder
)
from lib.filing_engine import classify_file, generate_filename
from lib.audit_logger import (
    log_file_register, log_change, log_review_item,
    log_run_start, log_run_end, generate_run_id,
    get_pending_reviews, mark_review_resolved,
)

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")
CONFIDENCE_THRESHOLD = 70


def get_to_sort_folder_id(service):
    """Get the TO SORT folder ID."""
    return get_folder_id_by_path(service, "TO SORT", WORKSPACE_FOLDER_ID)


def process_pending_reviews(service, run_id):
    """Check Review_Queue for PENDING items with Fabian's instructions.
    Process these FIRST before any new files."""
    pending = get_pending_reviews()
    if not pending:
        print("  No pending review items.")
        return 0

    print(f"  Found {len(pending)} pending review item(s) from Fabian:")
    processed = 0

    for item in pending:
        file_id = item.get("File_ID", "")
        file_name = item.get("File_Name", "")
        instruction = item.get("Fabian_Instruction", "")
        row_num = item["_row_number"]

        print(f"\n    Review: {file_name}")
        print(f"    Instruction: {instruction}")

        # Parse instruction — look for "move to FOLDER/PATH" pattern
        instruction_lower = instruction.lower().strip()
        dest_path = None

        for prefix in ["move to ", "file to ", "put in ", "goes in ", "belongs in "]:
            if instruction_lower.startswith(prefix):
                dest_path = instruction[len(prefix):].strip().strip("'\"")
                break

        if not dest_path:
            # Treat the whole instruction as a folder path
            dest_path = instruction.strip().strip("'\"")

        dest_folder_id = get_folder_id_by_path(service, dest_path, WORKSPACE_FOLDER_ID)
        if not dest_folder_id:
            print(f"    ERROR: Destination not found: {dest_path}")
            continue

        try:
            move_file(service, file_id, dest_folder_id)
            print(f"    MOVED: {file_name} -> {dest_path}")

            log_file_register(
                file_id=file_id, file_name=file_name,
                original_location=item.get("Current_Location", ""),
                new_location=dest_path, folder_id=dest_folder_id,
                action="MOVED", confidence=100,
                rule_matched=f"Fabian review: {instruction}",
                status="ACTIVE",
            )
            log_change(
                file_id=file_id, file_name=file_name,
                change_type="REVIEW_MOVE",
                before_state=item.get("Current_Location", ""),
                after_state=dest_path,
                script_phase="phase3", run_id=run_id,
                operator="fabian",
                notes=f"Review instruction: {instruction}",
            )

            mark_review_resolved(row_num, f"Moved to {dest_path}")
            processed += 1
        except Exception as e:
            print(f"    ERROR: {e}")

    return processed


def process_file(service, file_info, to_sort_id, run_id):
    """Process a single file from TO SORT. Logs every action."""
    file_id = file_info["id"]
    filename = file_info["name"]
    mime_type = file_info.get("mimeType", "")

    print(f"\n  Processing: {filename}")

    # Read content if possible
    content = ""
    readable_types = [
        "application/vnd.google-apps.document",
        "text/plain",
        "text/csv",
    ]
    if mime_type in readable_types:
        try:
            content = get_file_content(service, file_id, mime_type)
        except Exception as e:
            print(f"    Could not read content: {e}")

    # Classify
    destination, confidence, keywords = classify_file(filename, content)
    rule_str = ", ".join(keywords) if keywords else "none"

    if destination is None:
        print(f"    No match found. Leaving in TO SORT.")
        log_file_register(
            file_id=file_id, file_name=filename, file_type=mime_type,
            original_location="TO SORT", new_location="TO SORT",
            folder_id=to_sort_id, action="SKIPPED",
            confidence=0, rule_matched="none",
            status="ACTIVE",
        )
        log_change(
            file_id=file_id, file_name=filename,
            change_type="NO_MATCH", before_state="TO SORT",
            after_state="TO SORT (no rule matched)",
            script_phase="phase3", run_id=run_id,
        )
        return "skipped"

    if confidence >= CONFIDENCE_THRESHOLD:
        # Move to destination
        dest_folder_id = get_folder_id_by_path(service, destination, WORKSPACE_FOLDER_ID)
        if not dest_folder_id:
            print(f"    ERROR: Destination folder not found: {destination}")
            log_file_register(
                file_id=file_id, file_name=filename, file_type=mime_type,
                original_location="TO SORT", new_location=destination,
                action="SKIPPED", confidence=confidence,
                rule_matched=rule_str,
                version_notes="Destination folder not found",
                status="ACTIVE",
            )
            return "error"

        # Rename with convention
        new_name = generate_filename(filename)
        rename_file(service, file_id, new_name)
        move_file(service, file_id, dest_folder_id, to_sort_id)

        print(f"    FILED: {destination} (confidence: {confidence}%, keywords: {keywords})")
        print(f"    Renamed: {filename} -> {new_name}")

        log_file_register(
            file_id=file_id, file_name=new_name, file_type=mime_type,
            original_location="TO SORT", new_location=destination,
            folder_id=dest_folder_id, action="MOVED",
            confidence=confidence, rule_matched=rule_str,
            version_notes=f"Renamed from {filename}",
            status="ACTIVE",
        )
        log_change(
            file_id=file_id, file_name=filename,
            change_type="FILED", before_state="TO SORT",
            after_state=f"{destination} (renamed to {new_name})",
            script_phase="phase3", run_id=run_id,
            notes=f"Confidence {confidence}%, keywords: {rule_str}",
        )
        return "moved"
    else:
        # Low confidence — leave in TO SORT, flag + add to Review_Queue
        print(f"    LOW CONFIDENCE ({confidence}%): leaving in TO SORT")
        print(f"    Best guess: {destination}, keywords: {keywords}")

        try:
            service.comments().create(
                fileId=file_id,
                body={"content": (
                    f"[FILING AGENT] Low confidence ({confidence}%). "
                    f"Suggested: {destination}. Keywords: {rule_str}. "
                    f"Manual review required."
                )},
                fields="id",
            ).execute()
        except Exception:
            pass

        log_file_register(
            file_id=file_id, file_name=filename, file_type=mime_type,
            original_location="TO SORT", new_location="TO SORT",
            folder_id=to_sort_id, action="FLAGGED",
            confidence=confidence, rule_matched=rule_str,
            version_notes=f"Best guess: {destination}",
            status="ACTIVE",
        )
        log_change(
            file_id=file_id, file_name=filename,
            change_type="FLAGGED_LOW_CONFIDENCE",
            before_state="TO SORT", after_state="TO SORT (needs review)",
            script_phase="phase3", run_id=run_id,
            notes=f"Confidence {confidence}%, best guess: {destination}",
        )
        log_review_item(
            file_id=file_id, file_name=filename,
            current_location="TO SORT",
            issue_description=(
                f"Low confidence ({confidence}%). "
                f"Best guess: {destination}. Keywords: {rule_str}"
            ),
            priority="MEDIUM" if confidence >= 50 else "HIGH",
        )
        return "flagged"


def run_once(service=None):
    """Process all files currently in TO SORT. Returns count processed."""
    if service is None:
        service = get_drive_service()

    start_time = time.time()
    run_id = generate_run_id("phase3")
    log_run_start(run_id, "phase3")

    counts = {"moved": 0, "flagged": 0, "skipped": 0, "error": 0, "reviews": 0}

    # STEP 1: Process pending reviews from Fabian FIRST
    print("\n[Step 1] Checking Review_Queue for Fabian's instructions...")
    counts["reviews"] = process_pending_reviews(service, run_id)

    # STEP 2: Process TO SORT
    print("\n[Step 2] Processing TO SORT folder...")
    to_sort_id = get_to_sort_folder_id(service)
    if not to_sort_id:
        print("ERROR: TO SORT folder not found!")
        log_run_end(run_id, "phase3", status="FAILED", summary="TO SORT folder not found")
        return 0

    files = list_files_in_folder(service, to_sort_id)
    files = [f for f in files if f["mimeType"] != "application/vnd.google-apps.folder"]

    if not files:
        print("No files in TO SORT.")
    else:
        print(f"Found {len(files)} file(s) in TO SORT:")
        for f in files:
            result = process_file(service, f, to_sort_id, run_id)
            counts[result] = counts.get(result, 0) + 1

    duration = time.time() - start_time
    total = len(files) + counts["reviews"]
    status = "SUCCESS" if counts["error"] == 0 else "PARTIAL"
    summary = (
        f"Reviews: {counts['reviews']}, "
        f"Moved: {counts['moved']}, Flagged: {counts['flagged']}, "
        f"Skipped: {counts['skipped']}, Errors: {counts['error']}"
    )

    log_run_end(
        run_id, "phase3",
        files_processed=total, files_moved=counts["moved"],
        files_archived=0, files_flagged=counts["flagged"],
        files_skipped=counts["skipped"], errors=counts["error"],
        duration_seconds=duration, status=status, summary=summary,
    )

    return total


def run_watcher(poll_interval=60):
    """Continuous watcher mode — polls TO SORT periodically."""
    print("=" * 60)
    print("PHASE 3 — FILING AGENT (watcher mode)")
    print(f"Polling TO SORT every {poll_interval}s...")
    print("=" * 60)

    service = get_drive_service()
    while True:
        try:
            count = run_once(service)
            if count > 0:
                print(f"\n  Processed {count} file(s).")
        except Exception as e:
            print(f"\n  ERROR: {e}")
        time.sleep(poll_interval)


def test_filing():
    """Test the filing engine with 3 known files (dry run)."""
    print("=" * 60)
    print("PHASE 3 — FILING AGENT TEST (dry run)")
    print("=" * 60)

    test_cases = [
        ("NSP_pricing.pdf", "", "COMPANY/DISTRIBUTORS"),
        ("SHA_draft_tynan.docx", "", "LEGAL/SHA"),
        ("photo_PB4000.jpg", "", "SALES & MARKETING/MEDIA"),
    ]

    all_pass = True
    for filename, content, expected in test_cases:
        destination, confidence, keywords = classify_file(filename, content)
        status = "PASS" if destination == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"\n  [{status}] {filename}")
        print(f"    Expected:  {expected}")
        print(f"    Got:       {destination}")
        print(f"    Confidence: {confidence}%")
        print(f"    Keywords:  {keywords}")

    if all_pass:
        print("\nAll 3 test cases PASSED.")
    else:
        print("\nSome test cases FAILED. Fix filing rules before proceeding.")

    return all_pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run dry-run test")
    parser.add_argument("--once", action="store_true", help="Process TO SORT once")
    parser.add_argument("--watch", action="store_true", help="Continuous watcher mode")
    args = parser.parse_args()

    if args.test:
        test_filing()
    elif args.once:
        run_once()
    elif args.watch:
        run_watcher()
    else:
        print("Usage: python filing_agent.py --test | --once | --watch")
