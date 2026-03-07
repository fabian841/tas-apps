#!/usr/bin/env python3
"""
Gmail Capture Script – Phase 0

Uses Gmail API with incremental history sync. Falls back to date-based
fetch (last 7 days) when the stored historyId has expired (404).

Dependencies:
    pip install google-api-python-client google-auth-oauthlib psycopg2-binary requests

Schedule via cron (hourly):
    0 * * * * cd /opt/fabian-os/scripts && python3 capture_gmail.py >> /opt/fabian-os/logs/gmail.log 2>&1
"""

import os
import sys
import json
import base64
import logging
from datetime import datetime, timedelta, timezone

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
logger = logging.getLogger("capture_gmail")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = os.environ.get(
    "GMAIL_CREDENTIALS_PATH", "/opt/fabian-os/secrets/gmail_credentials.json"
)
TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", "/opt/fabian-os/secrets/gmail_token.json")
HISTORY_ID_PATH = "/opt/fabian-os/secrets/gmail_history_id.txt"

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "fabian_os")
DB_USER = os.environ.get("DB_USER", "fabian_app")
DB_PASSWORD = os.environ.get("APP_DB_PASSWORD", "")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def update_health(status, message=None):
    """Update health_checks table for this component."""
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
            ("gmail_capture", status, message),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Failed to update health_checks: %s", e)


def authenticate():
    """Authenticate with Gmail API using OAuth2."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def load_history_id():
    if os.path.exists(HISTORY_ID_PATH):
        with open(HISTORY_ID_PATH) as f:
            return f.read().strip()
    return None


def save_history_id(history_id):
    with open(HISTORY_ID_PATH, "w") as f:
        f.write(str(history_id))


def parse_message(msg):
    """Extract fields from a Gmail API message resource."""
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    body = ""
    attachments = []

    def _extract_body(payload):
        nonlocal body
        if payload.get("mimeType", "").startswith("text/plain") and payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        for part in payload.get("parts", []):
            if part.get("filename"):
                attachments.append({"filename": part["filename"], "mimeType": part.get("mimeType")})
            _extract_body(part)

    _extract_body(msg.get("payload", {}))

    received_at = None
    if "internalDate" in msg:
        received_at = datetime.fromtimestamp(int(msg["internalDate"]) / 1000, tz=timezone.utc)

    return {
        "message_id": msg["id"],
        "received_at": received_at,
        "sender": headers.get("from", ""),
        "subject": headers.get("subject", ""),
        "body": body,
        "attachments": attachments,
        "raw_data": msg,
    }


def store_email(conn, email_data):
    """Insert an email into raw_emails, skipping duplicates."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO raw_emails (message_id, received_at, sender, subject, body, attachments, raw_data, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'gmail')
        ON CONFLICT (message_id) DO NOTHING
        """,
        (
            email_data["message_id"],
            email_data["received_at"],
            email_data["sender"],
            email_data["subject"],
            email_data["body"],
            Json(email_data["attachments"]),
            Json(email_data["raw_data"]),
        ),
    )
    conn.commit()


def fetch_via_history(service, history_id):
    """Incremental fetch using Gmail history API."""
    message_ids = []
    try:
        results = service.users().history().list(
            userId="me", startHistoryId=history_id, historyTypes=["messageAdded"]
        ).execute()
        for history in results.get("history", []):
            for msg_added in history.get("messagesAdded", []):
                message_ids.append(msg_added["message"]["id"])
        new_history_id = results.get("historyId", history_id)
        return message_ids, new_history_id
    except Exception as e:
        if hasattr(e, "resp") and e.resp.status == 404:
            logger.warning("History ID expired, falling back to date-based fetch")
            return None, None
        raise


def fetch_via_date(service, days=7):
    """Fallback: fetch messages from the last N days."""
    after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    query = f"after:{after}"
    message_ids = []
    results = service.users().messages().list(userId="me", q=query, maxResults=500).execute()
    message_ids.extend(m["id"] for m in results.get("messages", []))
    while "nextPageToken" in results:
        results = service.users().messages().list(
            userId="me", q=query, maxResults=500, pageToken=results["nextPageToken"]
        ).execute()
        message_ids.extend(m["id"] for m in results.get("messages", []))
    return message_ids


def main():
    logger.info("Starting Gmail capture")
    try:
        service = authenticate()
        conn = get_db_connection()

        history_id = load_history_id()
        new_history_id = None

        if history_id:
            message_ids, new_history_id = fetch_via_history(service, history_id)
            if message_ids is None:
                # History expired – fall back
                message_ids = fetch_via_date(service)
        else:
            message_ids = fetch_via_date(service)

        logger.info("Found %d messages to process", len(message_ids))

        for msg_id in message_ids:
            msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
            email_data = parse_message(msg)
            store_email(conn, email_data)

        # Update history ID for next run
        if new_history_id:
            save_history_id(new_history_id)
        else:
            profile = service.users().getProfile(userId="me").execute()
            save_history_id(profile["historyId"])

        conn.close()
        update_health("ok")
        logger.info("Gmail capture complete")

    except Exception as e:
        logger.exception("Gmail capture failed: %s", e)
        update_health("error", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
