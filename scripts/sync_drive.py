#!/usr/bin/env python3
"""Google Drive Sync Script — Phase 0, Fabian OS

Lists and downloads new/modified files from Google Drive.
Stores metadata in raw_drive_files table.
Updates health_checks on completion.

Schedule: Daily via cron
    0 3 * * * cd /opt/fabian-os/scripts && python3 sync_drive.py >> /opt/fabian-os/logs/drive.log 2>&1

Requirements: google-api-python-client, google-auth-oauthlib, psycopg2-binary
"""

import os
import sys
import logging
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import Json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("sync_drive")

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", "/opt/fabian-os/secrets/gmail_credentials.json")
TOKEN_PATH = os.environ.get("DRIVE_TOKEN_PATH", "/opt/fabian-os/secrets/drive_token.json")
DOWNLOAD_DIR = os.environ.get("DRIVE_DOWNLOAD_DIR", "/opt/fabian-os/data/drive")
INBOX_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_INBOX_FOLDER_ID", "")

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "fabian_os")
DB_USER = os.environ.get("DB_USER", "fabian_app")
DB_PASSWORD = os.environ.get("APP_DB_PASSWORD", "")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def update_health(conn, status, message=""):
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO health_checks (component, last_run, status, message)
           VALUES ('drive_sync', NOW(), %s, %s)
           ON CONFLICT (component) DO UPDATE
           SET last_run = EXCLUDED.last_run, status = EXCLUDED.status, message = EXCLUDED.message""",
        (status, message),
    )
    conn.commit()


def get_drive_service():
    """Authenticate and return Google Drive API service."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                log.error(f"Credentials file not found: {CREDENTIALS_PATH}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def list_recent_files(service, days=1):
    """List files modified in the last N days."""
    since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    query = f"modifiedTime > '{since}' and trashed = false"

    files = []
    page_token = None

    while True:
        results = service.files().list(
            q=query,
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)",
            pageToken=page_token,
            pageSize=100,
        ).execute()

        files.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return files


def get_file_path(service, file_info):
    """Build a basic path from parent folder names."""
    parents = file_info.get("parents", [])
    if not parents:
        return "/" + file_info["name"]

    try:
        parent = service.files().get(
            fileId=parents[0], fields="name"
        ).execute()
        return f"/{parent['name']}/{file_info['name']}"
    except Exception:
        return "/" + file_info["name"]


def store_file_metadata(conn, file_info, path):
    """Insert or update file metadata in raw_drive_files."""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO raw_drive_files (file_id, name, path, mime_type, size, modified_at, metadata)
           VALUES (%s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (file_id) DO UPDATE
           SET name = EXCLUDED.name, path = EXCLUDED.path, mime_type = EXCLUDED.mime_type,
               size = EXCLUDED.size, modified_at = EXCLUDED.modified_at, metadata = EXCLUDED.metadata,
               ingested_at = NOW()""",
        (
            file_info["id"],
            file_info["name"],
            path,
            file_info.get("mimeType", ""),
            int(file_info.get("size", 0)) if file_info.get("size") else None,
            file_info.get("modifiedTime"),
            Json(file_info),
        ),
    )
    conn.commit()
    return cur.rowcount > 0


def download_file(service, file_id, file_name, mime_type):
    """Download a file to local disk (skip Google Docs native types)."""
    # Skip Google Docs/Sheets/Slides native types (they can't be downloaded directly)
    google_native_types = [
        "application/vnd.google-apps.document",
        "application/vnd.google-apps.spreadsheet",
        "application/vnd.google-apps.presentation",
        "application/vnd.google-apps.folder",
    ]
    if mime_type in google_native_types:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    local_path = os.path.join(DOWNLOAD_DIR, file_name)

    try:
        request = service.files().get_media(fileId=file_id)
        with open(local_path, "wb") as f:
            f.write(request.execute())
        return local_path
    except Exception as e:
        log.warning(f"Failed to download {file_name}: {e}")
        return None


def main():
    conn = get_db_connection()
    try:
        service = get_drive_service()
        files = list_recent_files(service, days=1)

        synced = 0
        for file_info in files:
            path = get_file_path(service, file_info)
            store_file_metadata(conn, file_info, path)

            # Download non-native files
            local_path = download_file(
                service, file_info["id"], file_info["name"], file_info.get("mimeType", "")
            )
            if local_path:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE raw_drive_files SET local_path = %s WHERE file_id = %s",
                    (local_path, file_info["id"]),
                )
                conn.commit()

            synced += 1

        log.info(f"Drive sync: {synced} files processed")
        update_health(conn, "ok", f"{synced} files synced")

    except Exception as e:
        log.error(f"Drive sync failed: {e}")
        update_health(conn, "error", str(e)[:500])
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
