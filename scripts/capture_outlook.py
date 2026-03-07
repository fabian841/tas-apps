#!/usr/bin/env python3
"""Microsoft 365 Email Capture Script — Phase 0, Fabian OS

Polls Microsoft Graph API for new emails using device code flow.
Stores in raw_emails table with source='outlook'.
Updates health_checks on completion.

Schedule: Hourly via cron
    30 * * * * cd /opt/fabian-os/scripts && python3 capture_outlook.py >> /opt/fabian-os/logs/outlook.log 2>&1

Requirements: msal, requests, psycopg2-binary
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta

import requests
import psycopg2
from psycopg2.extras import Json

try:
    import msal
except ImportError:
    print("ERROR: msal not installed. Run: pip install msal")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("capture_outlook")

CLIENT_ID = os.environ.get("OUTLOOK_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("OUTLOOK_CLIENT_SECRET", "")
TENANT_ID = os.environ.get("OUTLOOK_TENANT_ID", "")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]
TOKEN_CACHE_PATH = "/opt/fabian-os/secrets/outlook_token_cache.json"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "fabian_os")
DB_USER = os.environ.get("DB_USER", "fabian_app")
DB_PASSWORD = os.environ.get("APP_DB_PASSWORD", "")
LAST_SYNC_FILE = "/opt/fabian-os/data/outlook_last_sync.txt"


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def update_health(conn, status, message=""):
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO health_checks (component, last_run, status, message)
           VALUES ('outlook_capture', NOW(), %s, %s)
           ON CONFLICT (component) DO UPDATE
           SET last_run = EXCLUDED.last_run, status = EXCLUDED.status, message = EXCLUDED.message""",
        (status, message),
    )
    conn.commit()


def get_access_token():
    """Get access token using client credentials flow."""
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        log.error("Missing Outlook credentials (OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET, OUTLOOK_TENANT_ID)")
        sys.exit(1)

    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_PATH):
        with open(TOKEN_CACHE_PATH) as f:
            cache.deserialize(f.read())

    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache,
    )

    result = app.acquire_token_silent(SCOPES, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=SCOPES)

    if "access_token" in result:
        os.makedirs(os.path.dirname(TOKEN_CACHE_PATH), exist_ok=True)
        with open(TOKEN_CACHE_PATH, "w") as f:
            f.write(cache.serialize())
        return result["access_token"]

    log.error(f"Failed to get token: {result.get('error_description', 'Unknown error')}")
    sys.exit(1)


def get_last_sync_time():
    """Read last sync timestamp."""
    if os.path.exists(LAST_SYNC_FILE):
        with open(LAST_SYNC_FILE) as f:
            return f.read().strip()
    return (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"


def save_last_sync_time():
    """Save current time as last sync."""
    os.makedirs(os.path.dirname(LAST_SYNC_FILE), exist_ok=True)
    with open(LAST_SYNC_FILE, "w") as f:
        f.write(datetime.utcnow().isoformat() + "Z")


def fetch_messages(token, since):
    """Fetch messages received after the given timestamp."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE}/me/messages"
    params = {
        "$filter": f"receivedDateTime ge {since}",
        "$orderby": "receivedDateTime desc",
        "$top": 100,
        "$select": "id,receivedDateTime,from,subject,bodyPreview,hasAttachments",
    }

    messages = []
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    messages.extend(data.get("value", []))

    # Handle pagination
    while "@odata.nextLink" in data:
        resp = requests.get(data["@odata.nextLink"], headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        messages.extend(data.get("value", []))

    return messages


def store_email(conn, msg):
    """Insert email into raw_emails, skip duplicates."""
    sender = ""
    if msg.get("from", {}).get("emailAddress"):
        sender = msg["from"]["emailAddress"].get("address", "")

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO raw_emails (message_id, received_at, sender, subject, body, raw_data, source)
           VALUES (%s, %s, %s, %s, %s, %s, 'outlook')
           ON CONFLICT (message_id) DO NOTHING""",
        (
            msg["id"],
            msg.get("receivedDateTime"),
            sender,
            msg.get("subject", ""),
            msg.get("bodyPreview", ""),
            Json(msg),
        ),
    )
    conn.commit()
    return cur.rowcount > 0


def main():
    conn = get_db_connection()
    try:
        token = get_access_token()
        since = get_last_sync_time()

        messages = fetch_messages(token, since)
        inserted = 0
        for msg in messages:
            if store_email(conn, msg):
                inserted += 1

        save_last_sync_time()
        log.info(f"Outlook sync: {inserted} new emails (total fetched: {len(messages)})")
        update_health(conn, "ok", f"{inserted} emails synced")

    except Exception as e:
        log.error(f"Outlook capture failed: {e}")
        update_health(conn, "error", str(e)[:500])
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
