#!/usr/bin/env python3
"""
Fabian OS – Google Drive Capture Script

Captures file metadata from Google Drive and stores it in the raw_drive_files table.
Uses the Drive API changes.list for incremental sync with a fallback to full listing.

Stores raw file metadata in raw_drive_files table.
Updates health_checks on completion.
Inserts events into event_log.

Usage:
    python drive_capture.py                  # Incremental sync
    python drive_capture.py --full-sync      # Full resync

Environment variables (or .env file):
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
    DRIVE_CREDENTIALS_FILE, DRIVE_TOKEN_FILE
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("drive_capture")

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "fabian_os"),
    "user": os.getenv("POSTGRES_USER", "fabian"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

CREDENTIALS_FILE = os.getenv("DRIVE_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.getenv("DRIVE_TOKEN_FILE", "token.json")
BATCH_SIZE = 100

COMPONENT_NAME = "drive_capture"

# Fields to request from the Drive API
FILE_FIELDS = (
    "id, name, mimeType, parents, owners, webViewLink, iconLink, "
    "size, md5Checksum, createdTime, modifiedTime, shared, trashed"
)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def get_drive_service():
    """Authenticate and return a Google Drive API service instance."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(
                    f"Credentials file '{CREDENTIALS_FILE}' not found. "
                    "Download it from Google Cloud Console > APIs & Credentials."
                )
                sys.exit(1)
            logger.info("Starting OAuth2 authorization flow...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        logger.info(f"Credentials saved to {TOKEN_FILE}")

    return build("drive", "v3", credentials=creds)


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(**DB_CONFIG)


def get_last_page_token(conn):
    """Retrieve the last stored change page token for incremental sync."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT metadata->>'last_page_token' FROM health_checks WHERE component = %s",
            (COMPONENT_NAME,),
        )
        row = cur.fetchone()
        if row and row[0]:
            return row[0]
    return None


def store_file(conn, file_data):
    """Insert or update a raw drive file record. Returns True if new."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_drive_files (
                file_id, name, mime_type, parent_ids, owners,
                web_view_link, icon_link, size_bytes, md5_checksum,
                created_time, modified_time, shared, trashed,
                raw_payload, source_system
            ) VALUES (
                %(file_id)s, %(name)s, %(mime_type)s, %(parent_ids)s, %(owners)s,
                %(web_view_link)s, %(icon_link)s, %(size_bytes)s, %(md5_checksum)s,
                %(created_time)s, %(modified_time)s, %(shared)s, %(trashed)s,
                %(raw_payload)s, 'google_drive'
            )
            ON CONFLICT (file_id) DO UPDATE SET
                name = EXCLUDED.name,
                mime_type = EXCLUDED.mime_type,
                parent_ids = EXCLUDED.parent_ids,
                owners = EXCLUDED.owners,
                web_view_link = EXCLUDED.web_view_link,
                size_bytes = EXCLUDED.size_bytes,
                md5_checksum = EXCLUDED.md5_checksum,
                modified_time = EXCLUDED.modified_time,
                shared = EXCLUDED.shared,
                trashed = EXCLUDED.trashed,
                raw_payload = EXCLUDED.raw_payload,
                captured_at = NOW()
            RETURNING (xmax = 0) AS is_insert
            """,
            file_data,
        )
        result = cur.fetchone()
        return result[0] if result else False


def insert_event(conn, event_type, metadata=None):
    """Insert an event into the event_log."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO event_log (event_type, entity_type, source, metadata)
            VALUES (%s, 'raw_drive_file', %s, %s)
            """,
            (event_type, COMPONENT_NAME, json.dumps(metadata or {})),
        )


def update_health_check(conn, status, message, page_token=None):
    """Update the health_checks table for this component."""
    metadata = {}
    if page_token:
        metadata["last_page_token"] = page_token

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO health_checks (component, last_run, status, message, metadata)
            VALUES (%s, NOW(), %s, %s, %s)
            ON CONFLICT (component) DO UPDATE SET
                last_run = NOW(),
                status = EXCLUDED.status,
                message = EXCLUDED.message,
                metadata = health_checks.metadata || EXCLUDED.metadata
            """,
            (COMPONENT_NAME, status, message, json.dumps(metadata)),
        )


# ---------------------------------------------------------------------------
# File parsing
# ---------------------------------------------------------------------------


def parse_file(file_resource):
    """Extract structured data from a Drive API file resource."""
    owners = file_resource.get("owners")
    if owners:
        owners = json.dumps(owners)

    size_str = file_resource.get("size")
    size_bytes = int(size_str) if size_str else None

    return {
        "file_id": file_resource["id"],
        "name": file_resource.get("name", "Untitled"),
        "mime_type": file_resource.get("mimeType"),
        "parent_ids": file_resource.get("parents", []),
        "owners": owners,
        "web_view_link": file_resource.get("webViewLink"),
        "icon_link": file_resource.get("iconLink"),
        "size_bytes": size_bytes,
        "md5_checksum": file_resource.get("md5Checksum"),
        "created_time": file_resource.get("createdTime"),
        "modified_time": file_resource.get("modifiedTime"),
        "shared": file_resource.get("shared", False),
        "trashed": file_resource.get("trashed", False),
        "raw_payload": json.dumps(file_resource),
    }


# ---------------------------------------------------------------------------
# Sync strategies
# ---------------------------------------------------------------------------


def incremental_sync(service, conn, start_page_token):
    """Sync file changes since the given page token using changes.list."""
    logger.info(f"Starting incremental sync from pageToken={start_page_token[:20]}...")
    captured = 0
    updated = 0
    page_token = start_page_token

    while page_token:
        try:
            response = (
                service.changes()
                .list(
                    pageToken=page_token,
                    pageSize=BATCH_SIZE,
                    fields=f"nextPageToken, newStartPageToken, changes(fileId, removed, file({FILE_FIELDS}))",
                    includeRemoved=True,
                    spaces="drive",
                )
                .execute()
            )
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning("Page token expired or invalid. Falling back to full sync.")
                return None
            raise

        for change in response.get("changes", []):
            if change.get("removed"):
                continue

            file_resource = change.get("file")
            if not file_resource:
                continue

            try:
                file_data = parse_file(file_resource)
                is_new = store_file(conn, file_data)
                if is_new:
                    insert_event(conn, "DriveFileCaptured", {"file_id": file_resource["id"]})
                    captured += 1
                else:
                    updated += 1
            except Exception as e:
                logger.warning(f"Failed to process file {change.get('fileId')}: {e}")
                continue

        page_token = response.get("nextPageToken")
        new_start_token = response.get("newStartPageToken")

    conn.commit()
    logger.info(f"Incremental sync complete. New: {captured}, Updated: {updated}")
    return new_start_token or start_page_token


def full_sync(service, conn):
    """Full sync: list all files in Drive and store metadata."""
    logger.info("Starting full Drive sync...")
    captured = 0
    updated = 0
    page_token = None

    while True:
        params = {
            "pageSize": BATCH_SIZE,
            "fields": f"nextPageToken, files({FILE_FIELDS})",
            "orderBy": "modifiedTime desc",
        }
        if page_token:
            params["pageToken"] = page_token

        response = service.files().list(**params).execute()

        for file_resource in response.get("files", []):
            try:
                file_data = parse_file(file_resource)
                is_new = store_file(conn, file_data)
                if is_new:
                    insert_event(conn, "DriveFileCaptured", {"file_id": file_resource["id"]})
                    captured += 1
                else:
                    updated += 1
            except Exception as e:
                logger.warning(f"Failed to process file {file_resource.get('id')}: {e}")
                continue

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    conn.commit()

    # Get a start page token for future incremental syncs
    start_token_response = service.changes().getStartPageToken().execute()
    new_page_token = start_token_response.get("startPageToken")

    logger.info(f"Full sync complete. New: {captured}, Updated: {updated}")
    return new_page_token


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Fabian OS – Google Drive Capture")
    parser.add_argument("--full-sync", action="store_true", help="Force full file listing resync")
    args = parser.parse_args()

    conn = None
    try:
        logger.info("Connecting to database...")
        conn = get_db_connection()
        conn.autocommit = False

        logger.info("Authenticating with Google Drive API...")
        service = get_drive_service()

        if args.full_sync:
            new_page_token = full_sync(service, conn)
        else:
            last_page_token = get_last_page_token(conn)
            if last_page_token:
                new_page_token = incremental_sync(service, conn, last_page_token)
                if new_page_token is None:
                    # Token expired — fall back to full sync
                    new_page_token = full_sync(service, conn)
            else:
                logger.info("No previous page token found. Running initial full sync.")
                new_page_token = full_sync(service, conn)

        update_health_check(
            conn, "ok",
            f"Sync complete at {datetime.now(timezone.utc).isoformat()}",
            new_page_token,
        )
        conn.commit()
        logger.info("Drive capture completed successfully.")

    except Exception as e:
        logger.error(f"Drive capture failed: {e}", exc_info=True)
        if conn:
            conn.rollback()
            try:
                update_health_check(conn, "error", str(e)[:500])
                conn.commit()
            except Exception:
                pass
        sys.exit(1)

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
