"""
Gmail → Google Doc → NotebookLM Enterprise Ingestion Pipeline
TAS / Traffic & Access Solutions Pty Ltd

What this does:

1. Polls Gmail for new emails matching a label or query filter
2. Converts email body + attachments into a Google Doc (stays in your GCP/Drive)
3. Pushes the Doc ID directly to a NotebookLM Enterprise notebook via the official API
4. Logs each ingestion to a simple JSON log file

Auth strategy:

- Uses OAuth 2.0 user credentials (required for Google Docs/Drive sources in NotebookLM)
- Service accounts cannot be used for NotebookLM source ingestion per Google's docs
- Run once interactively to generate token.json, then fully headless thereafter

Requirements:
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests

GCP Setup checklist (do once in Console):

1. Enable APIs: Gmail API, Google Docs API, Google Drive API, Discovery Engine API
2. Create OAuth 2.0 Client ID (Desktop app) → download as credentials.json
3. Enable NotebookLM Enterprise under Gemini Enterprise → get your NOTEBOOK_ID from the URL
4. Assign yourself Cloud NotebookLM User IAM role
"""

import os
import json
import base64
import logging
import re
import datetime
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

GCP_PROJECT_NUMBER = os.environ.get("GCP_PROJECT_NUMBER", "YOUR_GCP_PROJECT_NUMBER")
GCP_LOCATION       = os.environ.get("GCP_LOCATION", "global")
NOTEBOOK_ID        = os.environ.get("NOTEBOOK_ID", "YOUR_NOTEBOOK_ID")
DRIVE_FOLDER_ID    = os.environ.get("DRIVE_FOLDER_ID", None)

# Gmail filter — adjust to match what you want ingested
# Examples: "label:portaboom", "from:jack@factory.com", "subject:QC Report"
GMAIL_QUERY = os.environ.get("GMAIL_QUERY", "label:to-notebooklm is:unread")

# File paths
CREDENTIALS_FILE = os.environ.get("CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE       = os.environ.get("TOKEN_FILE", "token.json")
INGESTION_LOG    = os.environ.get("INGESTION_LOG", "notebooklm_ingestion_log.json")

# OAuth scopes needed
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",       # read + mark as read
    "https://www.googleapis.com/auth/documents",           # create Google Docs
    "https://www.googleapis.com/auth/drive.file",          # manage Docs we create
    "https://www.googleapis.com/auth/cloud-platform",      # NotebookLM API token
]

# ─── LOGGING ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("gmail_to_notebooklm")

# ─── AUTH ─────────────────────────────────────────────────────────────────────


def get_credentials() -> Credentials:
    """Load or refresh OAuth2 user credentials. Opens browser on first run."""
    creds = None
    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


# ─── GMAIL ────────────────────────────────────────────────────────────────────


def get_unread_emails(gmail_service, query: str) -> list[dict]:
    """Return list of message dicts matching the Gmail query."""
    result = gmail_service.users().messages().list(
        userId="me", q=query, maxResults=50
    ).execute()
    messages = result.get("messages", [])
    log.info(f"Found {len(messages)} email(s) matching query: '{query}'")
    return messages


def parse_email(gmail_service, msg_id: str) -> dict:
    """
    Fetch a full email and return:
    - subject, sender, date
    - body_text (plain text, falls back to HTML stripped)
    - attachments: list of {filename, mime_type, data (bytes)}
    """
    msg = gmail_service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()

    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    subject  = headers.get("Subject", "(no subject)")
    sender   = headers.get("From", "unknown")
    date_str = headers.get("Date", "")

    body_text   = ""
    attachments = []

    def walk_parts(parts):
        nonlocal body_text
        for part in parts:
            mime = part.get("mimeType", "")
            if mime == "text/plain" and not body_text:
                data = part["body"].get("data", "")
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            elif mime == "text/html" and not body_text:
                data = part["body"].get("data", "")
                if data:
                    html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    body_text = re.sub(r"<[^>]+>", "", html)
            elif part.get("filename") and part["body"].get("attachmentId"):
                att = gmail_service.users().messages().attachments().get(
                    userId="me", messageId=msg_id, id=part["body"]["attachmentId"]
                ).execute()
                attachments.append({
                    "filename":  part["filename"],
                    "mime_type": mime,
                    "data":      base64.urlsafe_b64decode(att["data"]),
                })
            if "parts" in part:
                walk_parts(part["parts"])

    if "parts" in msg["payload"]:
        walk_parts(msg["payload"]["parts"])
    else:
        data = msg["payload"]["body"].get("data", "")
        if data:
            body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return {
        "id":          msg_id,
        "subject":     subject,
        "sender":      sender,
        "date":        date_str,
        "body":        body_text.strip(),
        "attachments": attachments,
    }


def mark_as_read(gmail_service, msg_id: str):
    """Remove UNREAD label so we don't reprocess."""
    gmail_service.users().messages().modify(
        userId="me", id=msg_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


# ─── GOOGLE DOCS ──────────────────────────────────────────────────────────────


def create_doc_from_email(docs_service, drive_service, email: dict) -> str:
    """
    Create a Google Doc containing the email body (and attachment text if any).
    Returns the document ID.
    """
    title = f"[Email] {email['subject']} – {email['date'][:16]}"

    content_lines = [
        f"From: {email['sender']}",
        f"Date: {email['date']}",
        f"Subject: {email['subject']}",
        "",
        "\u2500" * 60,
        "",
        email["body"],
    ]

    for att in email["attachments"]:
        if att["mime_type"].startswith("text/"):
            content_lines += [
                "",
                f"\u2500\u2500 Attachment: {att['filename']} \u2500\u2500",
                "",
                att["data"].decode("utf-8", errors="replace"),
            ]
        else:
            content_lines += [
                "",
                f"\u2500\u2500 Attachment (non-text, not included): {att['filename']} [{att['mime_type']}] \u2500\u2500",
            ]

    full_text = "\n".join(content_lines)

    doc = docs_service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [{
                "insertText": {
                    "location": {"index": 1},
                    "text": full_text,
                }
            }]
        }
    ).execute()

    if DRIVE_FOLDER_ID:
        drive_service.files().update(
            fileId=doc_id,
            addParents=DRIVE_FOLDER_ID,
            fields="id, parents"
        ).execute()

    log.info(f"Created Google Doc: '{title}' (ID: {doc_id})")
    return doc_id


# ─── NOTEBOOKLM API ───────────────────────────────────────────────────────────


def push_doc_to_notebooklm(creds: Credentials, doc_id: str, display_name: str) -> dict:
    """
    Add a Google Doc as a source in the configured NotebookLM Enterprise notebook.
    Uses notebooks.sources.batchCreate via the Discovery Engine API.
    """
    endpoint = (
        f"https://{GCP_LOCATION}-discoveryengine.googleapis.com/v1alpha"
        f"/projects/{GCP_PROJECT_NUMBER}/locations/{GCP_LOCATION}"
        f"/notebooks/{NOTEBOOK_ID}/sources:batchCreate"
    )

    payload = {
        "userContents": [
            {
                "googleDriveContent": {
                    "documentId": doc_id,
                    "mimeType":   "application/vnd.google-apps.document",
                    "sourceName": display_name[:200],
                }
            }
        ]
    }

    if not creds.valid:
        creds.refresh(Request())

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type":  "application/json",
    }

    response = requests.post(endpoint, headers=headers, json=payload, timeout=30)

    if response.status_code in (200, 201):
        log.info(f"Pushed to NotebookLM   doc_id={doc_id}")
        return response.json()
    else:
        log.error(f"NotebookLM API error {response.status_code}: {response.text}")
        response.raise_for_status()


# ─── INGESTION LOG ────────────────────────────────────────────────────────────


def load_log() -> list:
    if Path(INGESTION_LOG).exists():
        with open(INGESTION_LOG) as f:
            return json.load(f)
    return []


def save_log(entries: list):
    with open(INGESTION_LOG, "w") as f:
        json.dump(entries, f, indent=2)


def already_ingested(log_entries: list, msg_id: str) -> bool:
    return any(e["gmail_message_id"] == msg_id for e in log_entries)


# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────


def run_pipeline():
    log.info("=" * 60)
    log.info("Gmail -> NotebookLM pipeline starting")
    log.info("=" * 60)

    creds         = get_credentials()
    gmail_service = build("gmail",  "v1", credentials=creds)
    docs_service  = build("docs",   "v1", credentials=creds)
    drive_service = build("drive",  "v3", credentials=creds)

    ingestion_log = load_log()
    messages      = get_unread_emails(gmail_service, GMAIL_QUERY)

    if not messages:
        log.info("No new emails to process. Done.")
        return

    processed = 0
    errors    = 0

    for msg_meta in messages:
        msg_id = msg_meta["id"]

        if already_ingested(ingestion_log, msg_id):
            log.info(f"Skipping {msg_id} — already ingested")
            continue

        try:
            email = parse_email(gmail_service, msg_id)
            log.info(f"Processing: '{email['subject']}' from {email['sender']}")

            doc_id = create_doc_from_email(docs_service, drive_service, email)

            display_name = f"{email['subject']} ({email['sender']})"
            push_doc_to_notebooklm(creds, doc_id, display_name)

            mark_as_read(gmail_service, msg_id)

            ingestion_log.append({
                "gmail_message_id": msg_id,
                "subject":          email["subject"],
                "sender":           email["sender"],
                "google_doc_id":    doc_id,
                "ingested_at":      datetime.datetime.utcnow().isoformat() + "Z",
                "status":           "success",
            })
            save_log(ingestion_log)
            processed += 1

        except Exception as e:
            log.error(f"Failed on message {msg_id}: {e}")
            ingestion_log.append({
                "gmail_message_id": msg_id,
                "ingested_at":      datetime.datetime.utcnow().isoformat() + "Z",
                "status":           "error",
                "error":            str(e),
            })
            save_log(ingestion_log)
            errors += 1

    log.info("=" * 60)
    log.info(f"Done. Processed: {processed}  Errors: {errors}")
    log.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
