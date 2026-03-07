#!/usr/bin/env python3
"""Gmail Capture Script — Phase 0, Fabian OS

Fetches new emails from Gmail using incremental history sync.
Falls back to date-based fetch on 404 (expired historyId).
Stores in raw_emails table. Updates health_checks on completion.

Schedule: Hourly via cron
    0 * * * * cd /opt/fabian-os/scripts && python3 capture_gmail.py >> /opt/fabian-os/logs/gmail.log 2>&1

Requirements: google-api-python-client, google-auth-oauthlib, psycopg2-binary
"""

import os
import sys
import json
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
log = logging.getLogger("capture_gmail")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", "/opt/fabian-os/secrets/gmail_credentials.json")
TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", "/opt/fabian-os/secrets/gmail_token.json")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "fabian_os")
DB_USER = os.environ.get("DB_USER", "fabian_app")
DB_PASSWORD = os.environ.get("APP_DB_PASSWORD", "")
HISTORY_ID_FILE = "/opt/fabian-os/data/gmail_history_id.txt"


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def update_health(conn, status, message=""):
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO health_checks (component, last_run, status, message)
           VALUES ('gmail_capture', NOW(), %s, %s)
           ON CONFLICT (component) DO UPDATE
           SET last_run = EXCLUDED.last_run, status = EXCLUDED.status, message = EXCLUDED.message""",
        (status, message),
    )
    conn.commit()


def get_gmail_service():
    """Authenticate and return Gmail API service."""
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

    return build("gmail", "v1", credentials=creds)


def get_last_history_id():
    """Read the last known historyId from disk."""
    if os.path.exists(HISTORY_ID_FILE):
        with open(HISTORY_ID_FILE) as f:
            return f.read().strip()
    return None


def save_history_id(history_id):
    """Persist the latest historyId to disk."""
    os.makedirs(os.path.dirname(HISTORY_ID_FILE), exist_ok=True)
    with open(HISTORY_ID_FILE, "w") as f:
        f.write(str(history_id))


def fetch_message(service, msg_id):
    """Fetch a single message by ID."""
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()
    return msg


def parse_message(msg):
    """Extract structured fields from a Gmail message."""
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    return {
        "message_id": msg.get("id"),
        "received_at": headers.get("date"),
        "sender": headers.get("from", ""),
        "subject": headers.get("subject", ""),
        "body": msg.get("snippet", ""),
        "raw_data": msg,
        "source": "gmail",
    }


def store_email(conn, email_data):
    """Insert email into raw_emails, skip duplicates."""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO raw_emails (message_id, received_at, sender, subject, body, raw_data, source)
           VALUES (%(message_id)s, %(received_at)s, %(sender)s, %(subject)s, %(body)s, %(raw_data)s, %(source)s)
           ON CONFLICT (message_id) DO NOTHING""",
        {**email_data, "raw_data": Json(email_data["raw_data"])},
    )
    conn.commit()
    return cur.rowcount > 0


def fetch_via_history(service, conn, history_id):
    """Incremental fetch using Gmail history API."""
    try:
        results = service.users().history().list(
            userId="me", startHistoryId=history_id, historyTypes=["messageAdded"]
        ).execute()
    except Exception as e:
        if "404" in str(e) or "historyId" in str(e).lower():
            log.warning("History ID expired, falling back to date-based fetch")
            return fetch_via_date(service, conn, days=7)
        raise

    messages = []
    for record in results.get("history", []):
        for msg_added in record.get("messagesAdded", []):
            messages.append(msg_added["message"]["id"])

    new_history_id = results.get("historyId", history_id)
    inserted = 0

    for msg_id in messages:
        try:
            msg = fetch_message(service, msg_id)
            email_data = parse_message(msg)
            if store_email(conn, email_data):
                inserted += 1
        except Exception as e:
            log.warning(f"Failed to fetch message {msg_id}: {e}")

    save_history_id(new_history_id)
    return inserted, new_history_id


def fetch_via_date(service, conn, days=7):
    """Fallback: fetch emails from the last N days."""
    after_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y/%m/%d")
    query = f"after:{after_date}"

    results = service.users().messages().list(userId="me", q=query, maxResults=100).execute()
    messages = results.get("messages", [])

    inserted = 0
    latest_history_id = None

    for msg_ref in messages:
        try:
            msg = fetch_message(service, msg_ref["id"])
            email_data = parse_message(msg)
            if store_email(conn, email_data):
                inserted += 1
            if not latest_history_id:
                latest_history_id = msg.get("historyId")
        except Exception as e:
            log.warning(f"Failed to fetch message {msg_ref['id']}: {e}")

    if latest_history_id:
        save_history_id(latest_history_id)

    return inserted, latest_history_id


def main():
    conn = get_db_connection()
    try:
        service = get_gmail_service()
        history_id = get_last_history_id()

        if history_id:
            inserted, new_id = fetch_via_history(service, conn, history_id)
            log.info(f"History sync: {inserted} new emails, historyId={new_id}")
        else:
            inserted, new_id = fetch_via_date(service, conn, days=7)
            log.info(f"Date-based sync: {inserted} new emails, historyId={new_id}")

        update_health(conn, "ok", f"{inserted} emails synced")

    except Exception as e:
        log.error(f"Gmail capture failed: {e}")
        update_health(conn, "error", str(e)[:500])
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
