#!/usr/bin/env python3
"""
Google Drive Sync Script – Phase 0

Lists and downloads new/modified files from Google Drive.
Stores metadata in raw_drive_files.

Dependencies:
    pip install google-api-python-client google-auth-oauthlib psycopg2-binary

Schedule via cron (daily at 3 AM):
    0 3 * * * cd /opt/fabian-os/scripts && python3 sync_drive.py >> /opt/fabian-os/logs/drive.log 2>&1
"""

import os
import sys
import io
import logging
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import Json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("sync_drive")

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_PATH = os.environ.get(
    "DRIVE_CREDENTIALS_PATH", "/opt/fabian-os/secrets/drive_credentials.json"
)
TOKEN_PATH = os.environ.get("DRIVE_TOKEN_PATH", "/opt/fabian-os/secrets/drive_token.json")
DOWNLOAD_DIR = os.environ.get("DRIVE_DOWNLOAD_DIR", "/opt/fabian-os/drive_files")

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "fabian_os")
DB_USER = os.environ.get("DB_USER", "fabian_app")
DB_PASSWORD = os.environ.get("APP_DB_PASSWORD", "")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def update_health(status, message=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO health_checks (component, last_run, status, message)
            VALUES (%s, NOW(), %s, %s)
            ON CONFLICT (component) DO UPDATE
                SET last_run = EXCLUDED.last_run,
                    status   = EXCLUDED.status,
                    message  = EXCLUDED.message
            """,
            ("drive_sync", status, message),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Failed to update health_checks: %s", e)


def authenticate():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def get_last_sync_time(conn):
    """Get the most recent modified_at from raw_drive_files."""
    cur = conn.cursor()
    cur.execute("SELECT MAX(modified_at) FROM raw_drive_files")
    result = cur.fetchone()
    return result[0] if result and result[0] else None


def list_files(service, modified_after=None):
    """List files, optionally filtered by modification date."""
    query_parts = ["mimeType != 'application/vnd.google-apps.folder'", "trashed = false"]
    if modified_after:
        query_parts.append(f"modifiedTime > '{modified_after.isoformat()}'")
    query = " and ".join(query_parts)

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


def download_file(service, file_info):
    """Download a file from Google Drive."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_id = file_info["id"]
    file_name = file_info["name"]
    local_path = os.path.join(DOWNLOAD_DIR, f"{file_id}_{file_name}")

    # Skip Google Docs native formats (they need export)
    mime_type = file_info.get("mimeType", "")
    if mime_type.startswith("application/vnd.google-apps."):
        export_map = {
            "application/vnd.google-apps.document": "application/pdf",
            "application/vnd.google-apps.spreadsheet": "text/csv",
            "application/vnd.google-apps.presentation": "application/pdf",
        }
        export_mime = export_map.get(mime_type)
        if not export_mime:
            logger.info("Skipping unsupported Google format: %s (%s)", file_name, mime_type)
            return None
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        local_path += ".exported"
    else:
        request = service.files().get_media(fileId=file_id)

    fh = io.FileIO(local_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    return local_path


def store_file_metadata(conn, file_info, local_path):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO raw_drive_files (file_id, name, path, mime_type, size, modified_at, local_path, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (file_id) DO UPDATE
            SET name        = EXCLUDED.name,
                mime_type   = EXCLUDED.mime_type,
                size        = EXCLUDED.size,
                modified_at = EXCLUDED.modified_at,
                local_path  = EXCLUDED.local_path,
                metadata    = EXCLUDED.metadata,
                ingested_at = NOW()
        """,
        (
            file_info["id"],
            file_info["name"],
            ",".join(file_info.get("parents", [])),
            file_info.get("mimeType", ""),
            int(file_info.get("size", 0)) if file_info.get("size") else None,
            file_info.get("modifiedTime"),
            local_path,
            Json(file_info),
        ),
    )
    conn.commit()


def main():
    logger.info("Starting Google Drive sync")
    try:
        service = authenticate()
        conn = get_db_connection()

        last_sync = get_last_sync_time(conn)
        files = list_files(service, modified_after=last_sync)
        logger.info("Found %d new/modified files", len(files))

        for file_info in files:
            try:
                local_path = download_file(service, file_info)
                store_file_metadata(conn, file_info, local_path)
                logger.info("Synced: %s", file_info["name"])
            except Exception as e:
                logger.error("Failed to sync file %s: %s", file_info["name"], e)

        conn.close()
        update_health("ok")
        logger.info("Drive sync complete")

    except Exception as e:
        logger.exception("Drive sync failed: %s", e)
        update_health("error", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
