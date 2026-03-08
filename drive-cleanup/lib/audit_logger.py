"""
Audit logger — writes all actions to TAS_Drive_Audit Google Sheet.
Creates the sheet if it doesn't exist.
"""
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from lib.drive_client import get_sheets_service, get_drive_service, find_folder_by_name, create_folder

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get("WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm")
SHEET_NAME = "TAS_Drive_Audit"

# Tab names used across phases
TABS = [
    "FILING_AGENT",
    "MIGRATION",
    "CONSOLIDATION",
    "DUPLICATES",
    "ARCHIVED",
    "STUBS",
    "DAILY_LOG",
    "FULL_AUDIT",
]

_sheet_id_cache = None


def _find_or_create_sheet():
    """Find the TAS_Drive_Audit spreadsheet or create it."""
    global _sheet_id_cache
    if _sheet_id_cache:
        return _sheet_id_cache

    drive = get_drive_service()
    # Search for existing sheet
    resp = drive.files().list(
        q=(
            f"name = '{SHEET_NAME}' and "
            f"mimeType = 'application/vnd.google-apps.spreadsheet' and "
            f"trashed = false"
        ),
        fields="files(id, name)",
        pageSize=1,
    ).execute()

    files = resp.get("files", [])
    if files:
        _sheet_id_cache = files[0]["id"]
        return _sheet_id_cache

    # Create new spreadsheet
    sheets = get_sheets_service()
    body = {
        "properties": {"title": SHEET_NAME},
        "sheets": [{"properties": {"title": tab}} for tab in TABS],
    }
    spreadsheet = sheets.spreadsheets().create(body=body, fields="spreadsheetId").execute()
    sheet_id = spreadsheet["spreadsheetId"]

    # Move to workspace folder
    drive.files().update(
        fileId=sheet_id,
        addParents=WORKSPACE_FOLDER_ID,
        fields="id, parents",
    ).execute()

    # Add header rows to each tab
    for tab in TABS:
        _write_header(sheets, sheet_id, tab)

    _sheet_id_cache = sheet_id
    return sheet_id


def _write_header(sheets_service, sheet_id, tab_name):
    """Write header row to a tab."""
    headers = {
        "FILING_AGENT": ["Timestamp", "File Name", "Original Location", "Destination", "Confidence", "Action", "Notes"],
        "MIGRATION": ["Timestamp", "File Name", "File ID", "Old Folder", "New Folder", "Status"],
        "CONSOLIDATION": ["Timestamp", "File Name", "File ID", "Old Folder", "New Folder", "Status"],
        "DUPLICATES": ["Timestamp", "File Name", "File ID", "Folder", "Kept Version", "Archived Version", "Action"],
        "ARCHIVED": ["Timestamp", "File Name", "File ID", "Original Folder", "Archive Folder", "Last Modified", "Reason"],
        "STUBS": ["Timestamp", "File Name", "File ID", "Location", "Size", "Type", "Notes"],
        "DAILY_LOG": ["Timestamp", "File Name", "File ID", "Found In", "Moved To", "Action"],
        "FULL_AUDIT": ["Timestamp", "File Name", "File ID", "Location", "Type", "Last Modified", "Size", "Flags"],
    }
    row = headers.get(tab_name, ["Timestamp", "Action", "Details"])
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'{tab_name}'!A1",
        valueInputOption="RAW",
        body={"values": [row]},
    ).execute()


def log_action(tab_name, row_data):
    """Append a row to the specified tab in TAS_Drive_Audit."""
    sheet_id = _find_or_create_sheet()
    sheets = get_sheets_service()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    row = [timestamp] + list(row_data)
    sheets.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"'{tab_name}'!A:Z",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()
    time.sleep(0.1)  # rate limit


def log_batch(tab_name, rows):
    """Append multiple rows at once."""
    sheet_id = _find_or_create_sheet()
    sheets = get_sheets_service()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    data = [[timestamp] + list(row) for row in rows]
    # Process in batches of 50
    for i in range(0, len(data), 50):
        batch = data[i:i + 50]
        sheets.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A:Z",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": batch},
        ).execute()
        time.sleep(0.5)
