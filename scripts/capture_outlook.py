#!/usr/bin/env python3
"""
Microsoft 365 (Outlook) Capture Script – Phase 0

Uses Microsoft Graph API with device code flow to poll for new emails.
Stores results in raw_emails with source='outlook'.

Dependencies:
    pip install msal requests psycopg2-binary

Schedule via cron (hourly):
    0 * * * * cd /opt/fabian-os/scripts && python3 capture_outlook.py >> /opt/fabian-os/logs/outlook.log 2>&1
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta, timezone

import msal
import requests
import psycopg2
from psycopg2.extras import Json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("capture_outlook")

CLIENT_ID = os.environ.get("OUTLOOK_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("OUTLOOK_CLIENT_SECRET", "")
TENANT_ID = os.environ.get("OUTLOOK_TENANT_ID", "")
TOKEN_CACHE_PATH = "/opt/fabian-os/secrets/outlook_token_cache.json"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["https://graph.microsoft.com/Mail.Read"]

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
            ("outlook_capture", status, message),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Failed to update health_checks: %s", e)


def get_msal_app():
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_PATH):
        with open(TOKEN_CACHE_PATH) as f:
            cache.deserialize(f.read())

    app = msal.PublicClientApplication(
        CLIENT_ID, authority=authority, token_cache=cache
    )
    return app, cache


def acquire_token(app, cache):
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
    if not result:
        # Device code flow – requires initial interactive setup
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow initiation failed: {json.dumps(flow)}")
        logger.info("To authenticate, visit %s and enter code: %s", flow["verification_uri"], flow["user_code"])
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(f"Token acquisition failed: {result.get('error_description', 'Unknown error')}")

    # Persist cache
    if cache.has_state_changed:
        with open(TOKEN_CACHE_PATH, "w") as f:
            f.write(cache.serialize())

    return result["access_token"]


def fetch_emails(token, since_hours=24):
    """Fetch emails received in the last N hours."""
    since = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{GRAPH_BASE}/me/messages"
    params = {
        "$filter": f"receivedDateTime ge {since}",
        "$top": 50,
        "$orderby": "receivedDateTime desc",
        "$select": "id,receivedDateTime,from,subject,body,hasAttachments",
    }
    headers = {"Authorization": f"Bearer {token}"}

    emails = []
    while url:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        emails.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
        params = None  # nextLink already contains params

    return emails


def store_email(conn, msg):
    cur = conn.cursor()
    received_at = msg.get("receivedDateTime")
    sender = ""
    from_field = msg.get("from", {}).get("emailAddress", {})
    if from_field:
        sender = f"{from_field.get('name', '')} <{from_field.get('address', '')}>"

    cur.execute(
        """
        INSERT INTO raw_emails (message_id, received_at, sender, subject, body, attachments, raw_data, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'outlook')
        ON CONFLICT (message_id) DO NOTHING
        """,
        (
            msg["id"],
            received_at,
            sender,
            msg.get("subject", ""),
            msg.get("body", {}).get("content", ""),
            Json([]),  # attachments not fetched in detail
            Json(msg),
        ),
    )
    conn.commit()


def main():
    logger.info("Starting Outlook capture")
    try:
        app, cache = get_msal_app()
        token = acquire_token(app, cache)
        emails = fetch_emails(token)
        logger.info("Found %d emails", len(emails))

        conn = get_db_connection()
        for msg in emails:
            store_email(conn, msg)
        conn.close()

        update_health("ok")
        logger.info("Outlook capture complete")

    except Exception as e:
        logger.exception("Outlook capture failed: %s", e)
        update_health("error", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
