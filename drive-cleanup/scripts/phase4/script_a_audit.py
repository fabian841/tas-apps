"""
PHASE 4 — SCRIPT A: Full Workspace Audit
Scan entire workspace. List every file with metadata.
Flag files not modified in 12+ months and zero-size/stub files.
"""
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import get_drive_service, list_files_in_folder
from lib.audit_logger import log_batch

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")
TWELVE_MONTHS_AGO = datetime(2025, 3, 8, tzinfo=timezone.utc)  # 08/03/2025

STUB_MIME_TYPES = {
    "application/vnd.google-apps.shortcut",
}


def scan_folder_recursive(service, folder_id, path=""):
    """Recursively scan a folder and return all files with metadata."""
    items = list_files_in_folder(service, folder_id)
    results = []
    stubs = []
    old_files = []

    for item in items:
        item_path = f"{path}/{item['name']}" if path else item["name"]

        if item["mimeType"] == "application/vnd.google-apps.folder":
            sub_results, sub_stubs, sub_old = scan_folder_recursive(
                service, item["id"], item_path
            )
            results.extend(sub_results)
            stubs.extend(sub_stubs)
            old_files.extend(sub_old)
        else:
            size = item.get("size", "0")
            modified = item.get("modifiedTime", "")
            mime = item.get("mimeType", "")

            flags = []
            # Check for stub/shortcut
            is_stub = (
                mime in STUB_MIME_TYPES
                or item.get("shortcutDetails") is not None
                or size == "0"
            )
            if is_stub:
                flags.append("STUB")
                stubs.append({
                    "name": item["name"],
                    "id": item["id"],
                    "location": item_path,
                    "size": size,
                    "type": mime,
                })

            # Check for old files
            if modified:
                try:
                    mod_dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                    if mod_dt < TWELVE_MONTHS_AGO:
                        flags.append("OLD_12M+")
                        old_files.append({
                            "name": item["name"],
                            "id": item["id"],
                            "location": item_path,
                            "modified": modified,
                        })
                except ValueError:
                    pass

            results.append({
                "name": item["name"],
                "id": item["id"],
                "location": item_path,
                "type": mime,
                "modified": modified,
                "size": size,
                "flags": ", ".join(flags) if flags else "",
            })

    return results, stubs, old_files


def run():
    print("=" * 60)
    print("PHASE 4 — SCRIPT A: FULL WORKSPACE AUDIT")
    print("=" * 60)

    service = get_drive_service()

    print("\n[Scanning workspace recursively...]")
    all_files, stubs, old_files = scan_folder_recursive(service, WORKSPACE_FOLDER_ID)

    print(f"\n  Total files found: {len(all_files)}")
    print(f"  Stub/zero-size files: {len(stubs)}")
    print(f"  Files older than 12 months: {len(old_files)}")

    # Log full audit
    print("\n[Logging to FULL_AUDIT tab...]")
    audit_rows = [
        [f["name"], f["id"], f["location"], f["type"], f["modified"], f["size"], f["flags"]]
        for f in all_files
    ]
    if audit_rows:
        log_batch("FULL_AUDIT", audit_rows)

    # Log stubs
    print("[Logging to STUBS tab...]")
    stub_rows = [
        [s["name"], s["id"], s["location"], s["size"], s["type"], "Undownloaded/stub file"]
        for s in stubs
    ]
    if stub_rows:
        log_batch("STUBS", stub_rows)

    print(f"\nScript A COMPLETE. {len(all_files)} files audited.")
    return all_files, stubs, old_files


if __name__ == "__main__":
    run()
