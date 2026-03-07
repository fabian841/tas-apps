#!/usr/bin/env python3
"""
Fabian OS – Gmail Capture Script

Incrementally syncs emails from Gmail using the Gmail API.
Uses users.history.list for efficient incremental sync with a fallback
to date-based resync when historyId expires.

Stores raw messages in raw_emails table.
Updates health_checks on completion.
Inserts events into event_log.

Usage:
    python gmail_capture.py                # Incremental sync
    python gmail_capture.py --full-sync    # Full resync (last 30 days)
    python gmail_capture.py --days 7       # Resync last N days

Environment variables (or .env file):
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
    GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE, GMAIL_USER_ID, GMAIL_CAPTURE_BATCH_SIZE
"""

import argparse
import base64
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
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
logger = logging.getLogger("gmail_capture")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "fabian_os"),
    "user": os.getenv("POSTGRES_USER", "fabian"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
USER_ID = os.getenv("GMAIL_USER_ID", "me")
BATCH_SIZE = int(os.getenv("GMAIL_CAPTURE_BATCH_SIZE", "100"))

COMPONENT_NAME = "gmail_capture"


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
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

    return build("gmail", "v1", credentials=creds)


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(**DB_CONFIG)


def get_last_history_id(conn):
    """Retrieve the last stored historyId for incremental sync."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT metadata->>'last_history_id' FROM health_checks WHERE component = %s",
            (COMPONENT_NAME,),
        )
        row = cur.fetchone()
        if row and row[0]:
            return row[0]
    return None


def store_email(conn, msg_data):
    """Insert or update a raw email record. Returns True if new, False if updated."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_emails (
                message_id, thread_id, history_id, from_address,
                to_addresses, cc_addresses, subject, body_text, body_html,
                labels, has_attachments, received_at, raw_payload, source_system
            ) VALUES (
                %(message_id)s, %(thread_id)s, %(history_id)s, %(from_address)s,
                %(to_addresses)s, %(cc_addresses)s, %(subject)s, %(body_text)s, %(body_html)s,
                %(labels)s, %(has_attachments)s, %(received_at)s, %(raw_payload)s, 'gmail'
            )
            ON CONFLICT (message_id) DO UPDATE SET
                labels = EXCLUDED.labels,
                raw_payload = EXCLUDED.raw_payload,
                captured_at = NOW()
            RETURNING (xmax = 0) AS is_insert
            """,
            msg_data,
        )
        result = cur.fetchone()
        return result[0] if result else False


def insert_event(conn, event_type, entity_id, metadata=None):
    """Insert an event into the event_log."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO event_log (event_type, entity_type, entity_id, source, metadata)
            VALUES (%s, 'raw_email', %s, %s, %s)
            """,
            (event_type, entity_id, COMPONENT_NAME, json.dumps(metadata or {})),
        )


def update_health_check(conn, status, message, history_id=None):
    """Update the health_checks table for this component."""
    metadata = {}
    if history_id:
        metadata["last_history_id"] = str(history_id)

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
# Message parsing
# ---------------------------------------------------------------------------


def parse_message(msg):
    """Extract structured data from a Gmail API message resource."""
    headers = {}
    payload = msg.get("payload", {})
    for header in payload.get("headers", []):
        name = header["name"].lower()
        if name in ("from", "to", "cc", "bcc", "subject", "date"):
            headers[name] = header["value"]

    # Extract body
    body_text = ""
    body_html = ""
    has_attachments = False

    def extract_parts(part):
        nonlocal body_text, body_html, has_attachments
        mime_type = part.get("mimeType", "")
        if part.get("filename"):
            has_attachments = True
        if "body" in part and "data" in part["body"]:
            data = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            if mime_type == "text/plain":
                body_text = data
            elif mime_type == "text/html":
                body_html = data
        for sub_part in part.get("parts", []):
            extract_parts(sub_part)

    extract_parts(payload)

    # Parse addresses
    def parse_addresses(header_value):
        if not header_value:
            return []
        return [addr for _, addr in [parseaddr(a.strip()) for a in header_value.split(",")] if addr]

    # Parse received timestamp
    received_at = None
    internal_date = msg.get("internalDate")
    if internal_date:
        received_at = datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc)

    _, from_addr = parseaddr(headers.get("from", ""))

    return {
        "message_id": msg["id"],
        "thread_id": msg.get("threadId"),
        "history_id": msg.get("historyId"),
        "from_address": from_addr or None,
        "to_addresses": parse_addresses(headers.get("to")),
        "cc_addresses": parse_addresses(headers.get("cc")),
        "subject": headers.get("subject"),
        "body_text": body_text or None,
        "body_html": body_html or None,
        "labels": msg.get("labelIds", []),
        "has_attachments": has_attachments,
        "received_at": received_at,
        "raw_payload": json.dumps(msg),
    }


# ---------------------------------------------------------------------------
# Sync strategies
# ---------------------------------------------------------------------------


def incremental_sync(service, conn, start_history_id):
    """Sync emails since the given historyId using users.history.list."""
    logger.info(f"Starting incremental sync from historyId={start_history_id}")
    captured = 0
    max_history_id = int(start_history_id)
    page_token = None

    while True:
        try:
            params = {
                "userId": USER_ID,
                "startHistoryId": start_history_id,
                "historyTypes": ["messageAdded"],
                "maxResults": BATCH_SIZE,
            }
            if page_token:
                params["pageToken"] = page_token

            response = service.users().history().list(**params).execute()
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning("historyId expired. Falling back to date-based resync.")
                return None  # Signal caller to fall back
            raise

        for record in response.get("history", []):
            history_id = int(record.get("id", 0))
            max_history_id = max(max_history_id, history_id)

            for added in record.get("messagesAdded", []):
                msg_ref = added.get("message", {})
                msg_id = msg_ref.get("id")
                if not msg_id:
                    continue

                try:
                    full_msg = (
                        service.users()
                        .messages()
                        .get(userId=USER_ID, id=msg_id, format="full")
                        .execute()
                    )
                    msg_data = parse_message(full_msg)
                    is_new = store_email(conn, msg_data)
                    if is_new:
                        insert_event(conn, "EmailCaptured", None, {"message_id": msg_id})
                        captured += 1
                except HttpError as e:
                    logger.warning(f"Failed to fetch message {msg_id}: {e}")
                    continue

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    conn.commit()
    logger.info(f"Incremental sync complete. Captured {captured} new emails.")
    return str(max_history_id)


def date_based_sync(service, conn, days=30):
    """Fallback: sync emails from the last N days using messages.list."""
    after_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    query = f"after:{after_date}"
    logger.info(f"Starting date-based sync: {query}")

    captured = 0
    max_history_id = 0
    page_token = None

    while True:
        params = {
            "userId": USER_ID,
            "q": query,
            "maxResults": BATCH_SIZE,
        }
        if page_token:
            params["pageToken"] = page_token

        response = service.users().messages().list(**params).execute()

        for msg_ref in response.get("messages", []):
            msg_id = msg_ref["id"]
            try:
                full_msg = (
                    service.users()
                    .messages()
                    .get(userId=USER_ID, id=msg_id, format="full")
                    .execute()
                )
                msg_data = parse_message(full_msg)
                is_new = store_email(conn, msg_data)

                history_id = int(full_msg.get("historyId", 0))
                max_history_id = max(max_history_id, history_id)

                if is_new:
                    insert_event(conn, "EmailCaptured", None, {"message_id": msg_id})
                    captured += 1
            except HttpError as e:
                logger.warning(f"Failed to fetch message {msg_id}: {e}")
                continue

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    conn.commit()
    logger.info(f"Date-based sync complete. Captured {captured} emails.")
    return str(max_history_id) if max_history_id > 0 else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Fabian OS – Gmail Capture")
    parser.add_argument("--full-sync", action="store_true", help="Force full date-based resync")
    parser.add_argument("--days", type=int, default=30, help="Days to look back for date-based sync (default: 30)")
    args = parser.parse_args()

    conn = None
    try:
        logger.info("Connecting to database...")
        conn = get_db_connection()
        conn.autocommit = False

        logger.info("Authenticating with Gmail API...")
        service = get_gmail_service()

        if args.full_sync:
            new_history_id = date_based_sync(service, conn, days=args.days)
        else:
            last_history_id = get_last_history_id(conn)
            if last_history_id:
                new_history_id = incremental_sync(service, conn, last_history_id)
                if new_history_id is None:
                    # historyId expired — fall back
                    new_history_id = date_based_sync(service, conn, days=args.days)
            else:
                logger.info("No previous historyId found. Running initial date-based sync.")
                new_history_id = date_based_sync(service, conn, days=args.days)

        update_health_check(conn, "ok", f"Sync complete at {datetime.now(timezone.utc).isoformat()}", new_history_id)
        conn.commit()
        logger.info("Gmail capture completed successfully.")

    except Exception as e:
        logger.error(f"Gmail capture failed: {e}", exc_info=True)
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
