"""
Google Drive API client wrapper.
Handles authentication, rate limiting, and common operations.
"""
import os
import time
import json
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Rate limiting: max 100 requests per 10 seconds
_request_times = []
RATE_LIMIT = 100
RATE_WINDOW = 10.0
MIN_DELAY = 0.1  # sleep(0.1) between bulk API calls


def _rate_limit():
    """Enforce rate limiting: max 100 requests per 10 seconds."""
    now = time.time()
    _request_times.append(now)
    # Remove entries older than the window
    while _request_times and _request_times[0] < now - RATE_WINDOW:
        _request_times.pop(0)
    if len(_request_times) >= RATE_LIMIT:
        sleep_time = RATE_WINDOW - (now - _request_times[0])
        if sleep_time > 0:
            print(f"  [rate-limit] sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
    time.sleep(MIN_DELAY)


def get_credentials():
    """Build credentials from environment variables or token.json."""
    token_path = os.path.join(os.path.dirname(__file__), "..", "token.json")

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Build from env vars (refresh token flow)
            client_id = os.environ["GOOGLE_CLIENT_ID"]
            client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
            refresh_token = os.environ["GOOGLE_REFRESH_TOKEN"]
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                token_uri="https://oauth2.googleapis.com/token",
                scopes=SCOPES,
            )
            creds.refresh(Request())

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds


def get_drive_service():
    """Return authenticated Google Drive v3 service."""
    return build("drive", "v3", credentials=get_credentials())


def get_sheets_service():
    """Return authenticated Google Sheets v4 service."""
    return build("sheets", "v4", credentials=get_credentials())


def list_files_in_folder(service, folder_id, page_size=100):
    """List all files/folders in a given folder."""
    _rate_limit()
    results = []
    page_token = None
    while True:
        resp = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, shortcutDetails)",
            pageSize=page_size,
            pageToken=page_token,
        ).execute()
        results.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
        _rate_limit()
    return results


def create_folder(service, name, parent_id):
    """Create a folder and return its ID."""
    _rate_limit()
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def move_file(service, file_id, new_parent_id, current_parent_id=None):
    """Move a file to a new parent folder (no copy-and-delete)."""
    _rate_limit()
    kwargs = {"addParents": new_parent_id, "fields": "id, parents"}
    if current_parent_id:
        kwargs["removeParents"] = current_parent_id
    return service.files().update(fileId=file_id, **kwargs).execute()


def rename_file(service, file_id, new_name):
    """Rename a file."""
    _rate_limit()
    return service.files().update(
        fileId=file_id, body={"name": new_name}, fields="id, name"
    ).execute()


def trash_file(service, file_id):
    """Move a file/folder to Google Trash (not permanent delete)."""
    _rate_limit()
    return service.files().update(
        fileId=file_id, body={"trashed": True}, fields="id, trashed"
    ).execute()


def get_file_content(service, file_id, mime_type):
    """Read first ~500 words of a Google Doc or text file."""
    _rate_limit()
    if mime_type == "application/vnd.google-apps.document":
        content = service.files().export(
            fileId=file_id, mimeType="text/plain"
        ).execute()
        text = content.decode("utf-8") if isinstance(content, bytes) else content
    elif mime_type.startswith("text/"):
        content = service.files().get_media(fileId=file_id).execute()
        text = content.decode("utf-8") if isinstance(content, bytes) else content
    else:
        return ""
    words = text.split()
    return " ".join(words[:500])


def find_folder_by_name(service, name, parent_id):
    """Find a folder by name within a parent. Returns ID or None."""
    _rate_limit()
    resp = service.files().list(
        q=(
            f"'{parent_id}' in parents and "
            f"name = '{name}' and "
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"trashed = false"
        ),
        fields="files(id, name)",
        pageSize=1,
    ).execute()
    files = resp.get("files", [])
    return files[0]["id"] if files else None


def find_or_create_folder(service, name, parent_id):
    """Find a folder by name or create it if it doesn't exist."""
    folder_id = find_folder_by_name(service, name, parent_id)
    if folder_id:
        return folder_id
    return create_folder(service, name, parent_id)


def get_folder_id_by_path(service, path, root_id):
    """Resolve a path like 'LEGAL/CONTRACTS' to a folder ID starting from root."""
    parts = path.split("/")
    current_id = root_id
    for part in parts:
        folder_id = find_folder_by_name(service, part, current_id)
        if not folder_id:
            return None
        current_id = folder_id
    return current_id
