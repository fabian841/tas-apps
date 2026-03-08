"""
TAS_Drive_Intelligence — Central audit sheet for all Drive operations.

6 tabs:
  1. File_Register    — master record of every file touched
  2. Change_Log       — immutable append-only audit trail
  3. Review_Queue     — Fabian reviews incorrect filings, Claude scans this
  4. Improvement_Log  — lessons learned that improve filing rules
  5. Run_History      — every script execution (start + end row)
  6. Folder_Map       — live map of all 18 folders

Every phase script calls this logger on EVERY file action.
"""
import os
import time
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from lib.drive_client import get_sheets_service, get_drive_service

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")
SHEET_NAME = "TAS_Drive_Intelligence"

TABS = [
    "File_Register",
    "Change_Log",
    "Review_Queue",
    "Improvement_Log",
    "Run_History",
    "Folder_Map",
]

HEADERS = {
    "File_Register": [
        "Timestamp", "File_ID", "File_Name", "File_Type",
        "Original_Location", "New_Location", "Folder_Link",
        "Action_Taken", "Confidence_Score", "Rule_Matched",
        "Version_Notes", "Supersedes_File_ID", "Status",
        "Last_Reviewed", "Reviewed_By",
    ],
    "Change_Log": [
        "Timestamp", "Change_ID", "File_ID", "File_Name",
        "Change_Type", "Before_State", "After_State",
        "Script_Phase", "Run_ID", "Operator", "Notes",
    ],
    "Review_Queue": [
        "Timestamp", "File_ID", "File_Name", "Current_Location",
        "Issue_Description", "Fabian_Instruction", "Priority",
        "Status", "Resolution_Notes", "Resolved_Timestamp",
    ],
    "Improvement_Log": [
        "Timestamp", "Trigger", "Old_Rule", "New_Rule",
        "Rule_File_Updated", "Applied_From_Date", "Notes",
    ],
    "Run_History": [
        "Run_ID", "Timestamp", "Phase", "Files_Processed",
        "Files_Moved", "Files_Archived", "Files_Flagged",
        "Files_Skipped", "Errors", "Duration_Seconds",
        "Status", "Summary",
    ],
    "Folder_Map": [
        "Folder_Name", "Folder_ID", "Drive_Link",
        "Parent_Folder", "File_Count", "Last_Updated", "Notes",
    ],
}

_sheet_id_cache = None


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _drive_link(file_or_folder_id):
    """Generate a clickable Google Drive link."""
    return f"https://drive.google.com/drive/folders/{file_or_folder_id}"


def _find_or_create_sheet():
    """Find or create the TAS_Drive_Intelligence spreadsheet in the workspace root."""
    global _sheet_id_cache
    if _sheet_id_cache:
        return _sheet_id_cache

    drive = get_drive_service()

    # Search for existing sheet
    resp = drive.files().list(
        q=(
            f"name = '{SHEET_NAME}' and "
            f"mimeType = 'application/vnd.google-apps.spreadsheet' and "
            f"'{WORKSPACE_FOLDER_ID}' in parents and "
            f"trashed = false"
        ),
        fields="files(id, name)",
        pageSize=1,
    ).execute()

    files = resp.get("files", [])
    if files:
        _sheet_id_cache = files[0]["id"]
        return _sheet_id_cache

    # Create new spreadsheet with all 6 tabs
    sheets = get_sheets_service()
    body = {
        "properties": {"title": SHEET_NAME},
        "sheets": [{"properties": {"title": tab}} for tab in TABS],
    }
    spreadsheet = sheets.spreadsheets().create(
        body=body, fields="spreadsheetId"
    ).execute()
    sheet_id = spreadsheet["spreadsheetId"]

    # Move into workspace root folder
    drive.files().update(
        fileId=sheet_id,
        addParents=WORKSPACE_FOLDER_ID,
        fields="id, parents",
    ).execute()

    # Write headers to every tab
    for tab in TABS:
        header_row = HEADERS[tab]
        sheets.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{tab}'!A1",
            valueInputOption="RAW",
            body={"values": [header_row]},
        ).execute()
        time.sleep(0.1)

    _sheet_id_cache = sheet_id
    print(f"  Created TAS_Drive_Intelligence sheet: {sheet_id}")
    return sheet_id


def _append_rows(tab_name, rows):
    """Append rows to a tab. Handles batching for large sets."""
    sheet_id = _find_or_create_sheet()
    sheets = get_sheets_service()
    for i in range(0, len(rows), 50):
        batch = rows[i:i + 50]
        sheets.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A:Z",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": batch},
        ).execute()
        time.sleep(0.3)


def _append_row(tab_name, row):
    """Append a single row to a tab."""
    _append_rows(tab_name, [row])


# ──────────────────────────────────────────────────────────
# PUBLIC API — called by every phase script
# ──────────────────────────────────────────────────────────

def generate_run_id(phase):
    """Generate a unique run ID for a script execution."""
    short_id = uuid.uuid4().hex[:8]
    return f"{phase}_{short_id}"


def log_run_start(run_id, phase):
    """Log the START of a script execution to Run_History."""
    _append_row("Run_History", [
        run_id, _now(), phase,
        "", "", "", "", "", "",  # counts filled at end
        "", "RUNNING", f"Started {phase}",
    ])
    return run_id


def log_run_end(run_id, phase, files_processed=0, files_moved=0,
                files_archived=0, files_flagged=0, files_skipped=0,
                errors=0, duration_seconds=0, status="SUCCESS", summary=""):
    """Log the END of a script execution to Run_History."""
    _append_row("Run_History", [
        run_id, _now(), phase,
        str(files_processed), str(files_moved), str(files_archived),
        str(files_flagged), str(files_skipped), str(errors),
        str(round(duration_seconds, 1)), status, summary,
    ])


def log_file_register(file_id, file_name, file_type="",
                       original_location="", new_location="",
                       folder_id="", action="MOVED",
                       confidence=0, rule_matched="",
                       version_notes="", supersedes_file_id="",
                       status="ACTIVE"):
    """Log a file action to File_Register. Every file touched gets a row."""
    folder_link = _drive_link(folder_id) if folder_id else ""
    _append_row("File_Register", [
        _now(), file_id, file_name, file_type,
        original_location, new_location, folder_link,
        action, f"{confidence}%" if confidence else "",
        rule_matched, version_notes, supersedes_file_id,
        status, "", "",  # Last_Reviewed and Reviewed_By — blank initially
    ])


def log_change(file_id, file_name, change_type, before_state, after_state,
               script_phase, run_id, operator="claude", notes=""):
    """Log a change to Change_Log. APPEND-ONLY — never deleted."""
    change_id = f"CHG_{uuid.uuid4().hex[:8]}"
    _append_row("Change_Log", [
        _now(), change_id, file_id, file_name,
        change_type, before_state, after_state,
        script_phase, run_id, operator, notes,
    ])


def log_review_item(file_id, file_name, current_location,
                    issue_description, priority="MEDIUM"):
    """Add a file to the Review_Queue for Fabian to review."""
    _append_row("Review_Queue", [
        _now(), file_id, file_name, current_location,
        issue_description, "",  # Fabian_Instruction — blank, he fills this in
        priority, "PENDING", "", "",
    ])


def log_improvement(trigger, old_rule, new_rule, rule_file="",
                    applied_from="", notes=""):
    """Log a rule improvement to Improvement_Log."""
    _append_row("Improvement_Log", [
        _now(), trigger, old_rule, new_rule,
        rule_file, applied_from, notes,
    ])


def log_folder_map(folder_name, folder_id, parent_folder="",
                   file_count=0, notes=""):
    """Log a folder to the Folder_Map tab."""
    _append_row("Folder_Map", [
        folder_name, folder_id, _drive_link(folder_id),
        parent_folder, str(file_count), _now(), notes,
    ])


def get_pending_reviews():
    """Read Review_Queue and return all PENDING items with Fabian's instructions.

    Called at the START of every run so Fabian's corrections are processed first.
    Returns list of dicts with review data.
    """
    sheet_id = _find_or_create_sheet()
    sheets = get_sheets_service()

    result = sheets.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="'Review_Queue'!A:J",
    ).execute()

    rows = result.get("values", [])
    if len(rows) <= 1:  # header only
        return []

    headers = rows[0]
    pending = []
    for i, row in enumerate(rows[1:], start=2):  # row_number for sheet updates
        # Pad row to match header length
        while len(row) < len(headers):
            row.append("")

        item = dict(zip(headers, row))
        if (item.get("Status", "").strip().upper() == "PENDING"
                and item.get("Fabian_Instruction", "").strip()):
            item["_row_number"] = i
            pending.append(item)

    return pending


def mark_review_resolved(row_number, resolution_notes=""):
    """Mark a Review_Queue item as RESOLVED after processing Fabian's instruction."""
    sheet_id = _find_or_create_sheet()
    sheets = get_sheets_service()

    # Update Status (col H) and Resolution_Notes (col I) and Resolved_Timestamp (col J)
    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'Review_Queue'!H{row_number}:J{row_number}",
        valueInputOption="RAW",
        body={"values": [["RESOLVED", resolution_notes, _now()]]},
    ).execute()


def ensure_sheet_exists():
    """Ensure the TAS_Drive_Intelligence sheet exists. Called during Phase 2 setup."""
    sheet_id = _find_or_create_sheet()
    print(f"  TAS_Drive_Intelligence sheet ready: {sheet_id}")
    return sheet_id


# ──────────────────────────────────────────────────────────
# LEGACY COMPAT — keep old log_action/log_batch working
# during transition (these map to the new system)
# ──────────────────────────────────────────────────────────

def log_action(tab_name, row_data):
    """Legacy: append a row to old-style tab. Maps to Change_Log."""
    timestamp = _now()
    row = [timestamp] + list(row_data)
    # Write to Change_Log with legacy format
    change_id = f"LEGACY_{uuid.uuid4().hex[:8]}"
    _append_row("Change_Log", [
        timestamp, change_id, "", "",
        tab_name, "", str(row_data),
        tab_name, "", "claude", "Legacy log_action call",
    ])


def log_batch(tab_name, rows):
    """Legacy: append multiple rows. Maps to Change_Log."""
    timestamp = _now()
    for row_data in rows:
        change_id = f"LEGACY_{uuid.uuid4().hex[:8]}"
        _append_row("Change_Log", [
            timestamp, change_id, "", "",
            tab_name, "", str(row_data[:3]),
            tab_name, "", "claude", "Legacy log_batch call",
        ])
