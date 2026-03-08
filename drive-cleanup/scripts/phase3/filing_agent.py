"""
PHASE 3 — Filing Agent (TO SORT watcher)
1. Watch the TO SORT folder for new files
2. Classify each file using filing rules
3. Move to correct folder if confidence >= 70%
4. Leave and flag if confidence < 70%
5. Log all actions to TAS_Drive_Audit
"""
import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, list_files_in_folder, move_file, rename_file,
    get_file_content, get_folder_id_by_path, find_or_create_folder
)
from lib.filing_engine import classify_file, generate_filename
from lib.audit_logger import log_action

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")
CONFIDENCE_THRESHOLD = 70


def get_to_sort_folder_id(service):
    """Get the TO SORT folder ID."""
    return get_folder_id_by_path(service, "TO SORT", WORKSPACE_FOLDER_ID)


def process_file(service, file_info, to_sort_id):
    """Process a single file from TO SORT."""
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

    if destination is None:
        print(f"    No match found. Leaving in TO SORT.")
        log_action("FILING_AGENT", [
            filename, "TO SORT", "TO SORT", "0%", "LEFT", "No matching rule"
        ])
        return

    if confidence >= CONFIDENCE_THRESHOLD:
        # Move to destination
        dest_folder_id = get_folder_id_by_path(service, destination, WORKSPACE_FOLDER_ID)
        if not dest_folder_id:
            print(f"    ERROR: Destination folder not found: {destination}")
            log_action("FILING_AGENT", [
                filename, "TO SORT", destination, f"{confidence}%", "ERROR",
                "Destination folder not found"
            ])
            return

        # Rename with convention
        new_name = generate_filename(filename)
        rename_file(service, file_id, new_name)
        move_file(service, file_id, dest_folder_id, to_sort_id)

        print(f"    FILED: {destination} (confidence: {confidence}%, keywords: {keywords})")
        print(f"    Renamed: {filename} -> {new_name}")
        log_action("FILING_AGENT", [
            filename, "TO SORT", destination, f"{confidence}%", "FILED",
            f"Renamed to {new_name}. Keywords: {', '.join(keywords)}"
        ])
    else:
        # Low confidence — leave in TO SORT, flag
        print(f"    LOW CONFIDENCE ({confidence}%): leaving in TO SORT")
        print(f"    Best guess: {destination}, keywords: {keywords}")

        # Add comment to file as flag
        try:
            service.comments().create(
                fileId=file_id,
                body={"content": (
                    f"[FILING AGENT] Low confidence ({confidence}%). "
                    f"Suggested: {destination}. Keywords: {', '.join(keywords)}. "
                    f"Manual review required."
                )},
                fields="id",
            ).execute()
        except Exception:
            pass  # Comments API may not be available for all file types

        log_action("FILING_AGENT", [
            filename, "TO SORT", destination, f"{confidence}%", "LOW CONFIDENCE",
            f"Left in TO SORT. Keywords: {', '.join(keywords)}"
        ])


def run_once(service=None):
    """Process all files currently in TO SORT. Returns count processed."""
    if service is None:
        service = get_drive_service()

    to_sort_id = get_to_sort_folder_id(service)
    if not to_sort_id:
        print("ERROR: TO SORT folder not found!")
        return 0

    files = list_files_in_folder(service, to_sort_id)
    # Filter out folders and _ARCHIVE
    files = [
        f for f in files
        if f["mimeType"] != "application/vnd.google-apps.folder"
    ]

    if not files:
        print("No files in TO SORT.")
        return 0

    print(f"Found {len(files)} file(s) in TO SORT:")
    for f in files:
        process_file(service, f, to_sort_id)

    return len(files)


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
