"""
PHASE 2 — Create Folder Structure + TAS_Drive_Intelligence sheet
1. Create the TAS_Drive_Intelligence master Google Sheet
2. Create all 18 top-level folders in the workspace
3. Create all subfolders per TARGET_STRUCTURE
4. Create _ARCHIVE inside every folder and subfolder
5. Log every folder to Folder_Map tab
6. Save folder_registry.json
7. Verify ALL folders and _ARCHIVE presence
"""
import os
import sys
import json
import time
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, find_or_create_folder, list_files_in_folder,
    find_folder_by_name,
)
from lib.audit_logger import (
    ensure_sheet_exists, log_folder_map, log_run_start, log_run_end,
    log_change, generate_run_id,
)
from config.folder_structure import TARGET_STRUCTURE

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")


def _print_plan():
    """Print the full folder structure that will be created."""
    total = 0
    for folder_name, subfolders in TARGET_STRUCTURE.items():
        total += 1  # top-level
        total += 1  # its _ARCHIVE
        for sub in subfolders:
            total += 1  # subfolder
            total += 1  # subfolder _ARCHIVE
    print(f"\n  Plan: {len(TARGET_STRUCTURE)} top-level folders, {total} total folders (including _ARCHIVE)")
    print()
    for folder_name, subfolders in TARGET_STRUCTURE.items():
        print(f"  {folder_name}/")
        for sub in subfolders:
            print(f"    {sub}/")
            print(f"      _ARCHIVE/")
        print(f"    _ARCHIVE/")
    print()


def run(dry_run=False):
    print("=" * 60)
    print("PHASE 2 — CREATE FOLDER STRUCTURE")
    if dry_run:
        print("         *** DRY RUN — no changes will be made ***")
    print("=" * 60)

    start_time = time.time()

    # Show plan
    _print_plan()

    if dry_run:
        print("[DRY RUN] Would create TAS_Drive_Intelligence sheet")
        print("[DRY RUN] Would create all folders listed above")
        print("[DRY RUN] Would save folder_registry.json")
        print("\nDry run complete. Use 'python run.py phase2' to execute for real.")
        return {}

    run_id = generate_run_id("phase2")

    # Step 0: Create the intelligence sheet FIRST
    print("[Step 0] Creating TAS_Drive_Intelligence sheet...")
    try:
        ensure_sheet_exists()
        print("  DONE — sheet ready")
    except Exception as e:
        print(f"  ERROR creating sheet: {e}")
        print("  Continuing — sheet logging may be unavailable for this run")

    try:
        log_run_start(run_id, "phase2")
    except Exception:
        pass  # non-fatal if sheet logging fails

    try:
        service = get_drive_service()
    except KeyError as e:
        print(f"\n  FATAL: Missing environment variable {e}")
        print("  Phase 2 requires Google OAuth credentials.")
        print("  Copy .env.example to .env and fill in:")
        print("    GOOGLE_CLIENT_ID=<your-client-id>")
        print("    GOOGLE_CLIENT_SECRET=<your-client-secret>")
        print("    GOOGLE_REFRESH_TOKEN=<your-refresh-token>")
        print("\n  Or provide a token.json file from a previous OAuth flow.")
        return {}
    except Exception as e:
        print(f"\n  FATAL: Could not authenticate with Google Drive: {e}")
        return {}

    created_count = 0
    skipped_count = 0
    error_count = 0
    folder_registry = {}  # path -> folder_id

    # Step 1: Create top-level folders + subfolders + _ARCHIVEs
    print(f"\n[Step 1] Creating {len(TARGET_STRUCTURE)} top-level folders + subfolders...\n")

    for i, (folder_name, subfolders) in enumerate(TARGET_STRUCTURE.items(), 1):
        progress = f"[{i}/{len(TARGET_STRUCTURE)}]"

        try:
            folder_id = find_or_create_folder(service, folder_name, WORKSPACE_FOLDER_ID)
            folder_registry[folder_name] = folder_id
            print(f"  {progress} {folder_name} ({folder_id})")
            created_count += 1

            try:
                log_folder_map(folder_name, folder_id, parent_folder="WORKSPACE ROOT")
                log_change(
                    file_id=folder_id, file_name=folder_name,
                    change_type="FOLDER_CREATED", before_state="",
                    after_state="Created in workspace root",
                    script_phase="phase2", run_id=run_id,
                )
            except Exception as log_err:
                print(f"    WARN: logging failed ({log_err})")

            # Create subfolders
            for sub in subfolders:
                try:
                    sub_id = find_or_create_folder(service, sub, folder_id)
                    path = f"{folder_name}/{sub}"
                    folder_registry[path] = sub_id
                    print(f"    + {sub} ({sub_id})")
                    created_count += 1

                    try:
                        log_folder_map(sub, sub_id, parent_folder=folder_name)
                        log_change(
                            file_id=sub_id, file_name=sub,
                            change_type="FOLDER_CREATED", before_state="",
                            after_state=f"Created in {folder_name}",
                            script_phase="phase2", run_id=run_id,
                        )
                    except Exception:
                        pass

                    # _ARCHIVE inside subfolder
                    try:
                        archive_id = find_or_create_folder(service, "_ARCHIVE", sub_id)
                        folder_registry[f"{path}/_ARCHIVE"] = archive_id
                        print(f"      + _ARCHIVE ({archive_id})")
                        created_count += 1
                    except Exception as arch_err:
                        print(f"      ERROR creating _ARCHIVE in {path}: {arch_err}")
                        error_count += 1

                except Exception as sub_err:
                    print(f"    ERROR creating subfolder {sub}: {sub_err}")
                    error_count += 1

            # _ARCHIVE inside top-level folder
            try:
                archive_id = find_or_create_folder(service, "_ARCHIVE", folder_id)
                folder_registry[f"{folder_name}/_ARCHIVE"] = archive_id
                print(f"    + _ARCHIVE ({archive_id})")
                created_count += 1
            except Exception as arch_err:
                print(f"    ERROR creating _ARCHIVE in {folder_name}: {arch_err}")
                error_count += 1

        except Exception as e:
            print(f"  {progress} ERROR creating {folder_name}: {e}")
            error_count += 1

    # Save registry for use by other scripts
    registry_path = os.path.join(os.path.dirname(__file__), "..", "..", "folder_registry.json")
    try:
        with open(registry_path, "w") as f:
            json.dump(folder_registry, f, indent=2)
        print(f"\nFolder registry saved to: {registry_path}")
    except Exception as e:
        print(f"\nERROR saving folder_registry.json: {e}")
        error_count += 1

    # Step 2: Verify ALL folders (not just a sample)
    print(f"\n[Step 2] Verifying ALL {len(TARGET_STRUCTURE)} top-level folders...\n")
    verify_pass = 0
    verify_fail = 0

    for folder_name in TARGET_STRUCTURE:
        if folder_name not in folder_registry:
            print(f"  FAIL: {folder_name} — not in registry (creation failed)")
            verify_fail += 1
            continue

        folder_id = folder_registry[folder_name]
        try:
            archive = find_folder_by_name(service, "_ARCHIVE", folder_id)
            if archive:
                print(f"  PASS: {folder_name} — has _ARCHIVE")
                verify_pass += 1
            else:
                print(f"  FAIL: {folder_name} — missing _ARCHIVE!")
                verify_fail += 1
        except Exception as e:
            print(f"  FAIL: {folder_name} — verify error: {e}")
            verify_fail += 1

    # Verify subfolders have _ARCHIVE too
    subfolder_checks = 0
    subfolder_fails = 0
    for folder_name, subfolders in TARGET_STRUCTURE.items():
        for sub in subfolders:
            path = f"{folder_name}/{sub}"
            if path not in folder_registry:
                subfolder_fails += 1
                continue
            sub_id = folder_registry[path]
            try:
                archive = find_folder_by_name(service, "_ARCHIVE", sub_id)
                if archive:
                    subfolder_checks += 1
                else:
                    print(f"  FAIL: {path} — missing _ARCHIVE!")
                    subfolder_fails += 1
            except Exception:
                subfolder_fails += 1

    # Summary
    duration = time.time() - start_time
    all_ok = verify_fail == 0 and subfolder_fails == 0 and error_count == 0
    status = "SUCCESS" if all_ok else "PARTIAL"

    print("\n" + "=" * 60)
    print("PHASE 2 — SUMMARY")
    print("=" * 60)
    print(f"  Folders created/found:     {created_count}")
    print(f"  Errors during creation:    {error_count}")
    print(f"  Top-level verified:        {verify_pass}/{len(TARGET_STRUCTURE)}")
    print(f"  Subfolder _ARCHIVE OK:     {subfolder_checks}/{subfolder_checks + subfolder_fails}")
    print(f"  Duration:                  {duration:.1f}s")
    print(f"  Status:                    {status}")
    print("=" * 60)

    summary = (
        f"Created {created_count} folders. "
        f"Verified {verify_pass}/{len(TARGET_STRUCTURE)} top-level, "
        f"{subfolder_checks} subfolder _ARCHIVEs. "
        f"Errors: {error_count}."
    )

    try:
        log_run_end(
            run_id, "phase2",
            files_processed=created_count, files_moved=0,
            files_archived=0, files_flagged=verify_fail + subfolder_fails,
            files_skipped=skipped_count,
            errors=error_count,
            duration_seconds=duration, status=status, summary=summary,
        )
    except Exception:
        pass

    if all_ok:
        print(f"\nPhase 2 COMPLETE. All folders created and verified.")
    else:
        print(f"\nWARNING: Phase 2 completed with issues. Review above output.")

    return folder_registry


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv or "--dry" in sys.argv
    run(dry_run=dry)
