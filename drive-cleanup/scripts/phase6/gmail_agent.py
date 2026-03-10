"""
PHASE 6 — Gmail Email Filing Agent

Monitors Gmail for emails with a specific label (default: "TO FILE"),
then for each labelled email:
1. Saves the full email body as a Google Doc in Google Drive
2. Downloads all attachments and uploads them to Google Drive
3. Classifies each file using the existing filing engine rules
4. Moves files to the correct folder (or TO SORT if low confidence)
5. Renames files per naming convention: YYYYMMDD_Topic_Source.ext
6. Logs EVERY action to File_Register + Change_Log
7. Removes the label (and optionally archives) the email once processed

Supports --once (process and exit) and --watch (continuous polling) modes.
"""
import os
import sys
import time
import base64
import email
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.drive_client import (
    get_drive_service, get_gmail_service,
    move_file, rename_file, get_file_content,
    get_folder_id_by_path, find_or_create_folder,
)
from lib.filing_engine import classify_file, generate_filename
from lib.audit_logger import (
    log_file_register, log_change, log_review_item,
    log_run_start, log_run_end, generate_run_id,
)

load_dotenv()

WORKSPACE_FOLDER_ID = os.environ.get(
    "WORKSPACE_FOLDER_ID", "1klBbAXcsqy0yYi_MAgLZJj_Pg7xEsCWm"
)
GMAIL_LABEL_NAME = os.environ.get("GMAIL_FILING_LABEL", "TO FILE")
ARCHIVE_AFTER_FILING = os.environ.get("GMAIL_ARCHIVE_AFTER_FILING", "true").lower() == "true"
CONFIDENCE_THRESHOLD = 70


# ──────────────────────────────────────────────────────────
# GMAIL HELPERS
# ──────────────────────────────────────────────────────────

def get_or_create_label(gmail, label_name):
    """Find or create a Gmail label. Returns the label ID."""
    resp = gmail.users().labels().list(userId="me").execute()
    for label in resp.get("labels", []):
        if label["name"].lower() == label_name.lower():
            return label["id"]

    # Create the label if it doesn't exist
    body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    created = gmail.users().labels().create(userId="me", body=body).execute()
    print(f"  Created Gmail label: {label_name}")
    return created["id"]


def get_labelled_messages(gmail, label_id):
    """Get all message IDs with the given label."""
    messages = []
    page_token = None
    while True:
        resp = gmail.users().messages().list(
            userId="me", labelIds=[label_id], pageToken=page_token,
        ).execute()
        messages.extend(resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return messages


def get_message_detail(gmail, msg_id):
    """Get full message details including headers and parts."""
    return gmail.users().messages().get(
        userId="me", id=msg_id, format="full",
    ).execute()


def get_header(headers, name):
    """Extract a header value by name from a list of header dicts."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def decode_body(data):
    """Decode base64url-encoded body data to text."""
    if not data:
        return ""
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")


def extract_email_text(payload):
    """Recursively extract the plain-text body from a message payload."""
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return decode_body(data)

    if mime_type == "text/html" and not extract_email_text.__dict__.get("_found_plain"):
        # Fallback: use HTML if no plain text found
        data = payload.get("body", {}).get("data", "")
        return decode_body(data)

    parts = payload.get("parts", [])
    for part in parts:
        text = extract_email_text(part)
        if text.strip():
            return text
    return ""


def extract_attachments(gmail, msg_id, payload):
    """Extract attachment metadata and data from a message payload.
    Returns list of dicts: {filename, mime_type, data_bytes}
    """
    attachments = []
    _walk_parts_for_attachments(gmail, msg_id, payload, attachments)
    return attachments


def _walk_parts_for_attachments(gmail, msg_id, payload, results):
    """Recursively walk message parts to find attachments."""
    parts = payload.get("parts", [])
    for part in parts:
        filename = part.get("filename", "")
        body = part.get("body", {})
        mime_type = part.get("mimeType", "application/octet-stream")

        if filename:
            # This is an attachment
            attachment_id = body.get("attachmentId")
            if attachment_id:
                att = gmail.users().messages().attachments().get(
                    userId="me", messageId=msg_id, id=attachment_id,
                ).execute()
                data = base64.urlsafe_b64decode(att["data"])
            else:
                data = base64.urlsafe_b64decode(body.get("data", ""))

            results.append({
                "filename": filename,
                "mime_type": mime_type,
                "data_bytes": data,
            })

        # Recurse into nested parts
        if part.get("parts"):
            _walk_parts_for_attachments(gmail, msg_id, part, results)


def remove_label_and_archive(gmail, msg_id, label_id):
    """Remove the filing label from the message, optionally archive it."""
    modify_body = {"removeLabelIds": [label_id]}
    if ARCHIVE_AFTER_FILING:
        modify_body["removeLabelIds"].append("INBOX")
    gmail.users().messages().modify(
        userId="me", id=msg_id, body=modify_body,
    ).execute()


# ──────────────────────────────────────────────────────────
# DRIVE UPLOAD HELPERS
# ──────────────────────────────────────────────────────────

def upload_email_as_doc(drive, subject, sender, date_str, body_text, parent_folder_id):
    """Create a Google Doc from the email body. Returns file ID."""
    from googleapiclient.http import MediaInMemoryUpload

    doc_content = (
        f"From: {sender}\n"
        f"Date: {date_str}\n"
        f"Subject: {subject}\n"
        f"{'=' * 60}\n\n"
        f"{body_text}"
    )

    media = MediaInMemoryUpload(
        doc_content.encode("utf-8"),
        mimetype="text/plain",
        resumable=False,
    )
    metadata = {
        "name": f"EMAIL_{subject[:80]}",
        "mimeType": "application/vnd.google-apps.document",
        "parents": [parent_folder_id],
    }
    created = drive.files().create(
        body=metadata, media_body=media, fields="id, name",
    ).execute()
    return created["id"], created["name"]


def upload_attachment(drive, filename, mime_type, data_bytes, parent_folder_id):
    """Upload an attachment to Google Drive. Returns file ID."""
    from googleapiclient.http import MediaInMemoryUpload

    media = MediaInMemoryUpload(data_bytes, mimetype=mime_type, resumable=False)
    metadata = {
        "name": filename,
        "parents": [parent_folder_id],
    }
    created = drive.files().create(
        body=metadata, media_body=media, fields="id, name, mimeType",
    ).execute()
    return created["id"], created["name"], created.get("mimeType", mime_type)


# ──────────────────────────────────────────────────────────
# FILE CLASSIFICATION + FILING
# ──────────────────────────────────────────────────────────

def classify_and_file(drive, file_id, filename, mime_type, content_hint,
                      date_str, staging_folder_id, run_id):
    """Classify a file and move it to the correct folder.
    Returns result string: 'moved', 'flagged', or 'skipped'.
    """
    destination, confidence, keywords = classify_file(filename, content_hint)
    rule_str = ", ".join(keywords) if keywords else "none"

    if destination is None:
        print(f"    No match found. Leaving in TO SORT.")
        # Move to TO SORT
        to_sort_id = get_folder_id_by_path(drive, "TO SORT", WORKSPACE_FOLDER_ID)
        if to_sort_id and to_sort_id != staging_folder_id:
            move_file(drive, file_id, to_sort_id, staging_folder_id)

        log_file_register(
            file_id=file_id, file_name=filename, file_type=mime_type,
            original_location="Gmail", new_location="TO SORT",
            folder_id=to_sort_id or "", action="SKIPPED",
            confidence=0, rule_matched="none", status="ACTIVE",
        )
        log_change(
            file_id=file_id, file_name=filename,
            change_type="GMAIL_NO_MATCH", before_state="Gmail",
            after_state="TO SORT (no rule matched)",
            script_phase="phase6", run_id=run_id,
        )
        return "skipped"

    if confidence >= CONFIDENCE_THRESHOLD:
        dest_folder_id = get_folder_id_by_path(drive, destination, WORKSPACE_FOLDER_ID)
        if not dest_folder_id:
            print(f"    ERROR: Destination folder not found: {destination}")
            return "error"

        # Rename with convention
        new_name = generate_filename(filename, date_str)
        rename_file(drive, file_id, new_name)
        move_file(drive, file_id, dest_folder_id, staging_folder_id)

        print(f"    FILED: {destination} (confidence: {confidence}%, keywords: {keywords})")
        print(f"    Renamed: {filename} -> {new_name}")

        log_file_register(
            file_id=file_id, file_name=new_name, file_type=mime_type,
            original_location="Gmail", new_location=destination,
            folder_id=dest_folder_id, action="MOVED",
            confidence=confidence, rule_matched=rule_str,
            version_notes=f"Renamed from {filename} (via Gmail agent)",
            status="ACTIVE",
        )
        log_change(
            file_id=file_id, file_name=filename,
            change_type="GMAIL_FILED", before_state="Gmail",
            after_state=f"{destination} (renamed to {new_name})",
            script_phase="phase6", run_id=run_id,
            notes=f"Confidence {confidence}%, keywords: {rule_str}",
        )
        return "moved"
    else:
        # Low confidence — move to TO SORT and flag for review
        print(f"    LOW CONFIDENCE ({confidence}%): moving to TO SORT")
        to_sort_id = get_folder_id_by_path(drive, "TO SORT", WORKSPACE_FOLDER_ID)
        if to_sort_id and to_sort_id != staging_folder_id:
            move_file(drive, file_id, to_sort_id, staging_folder_id)

        log_file_register(
            file_id=file_id, file_name=filename, file_type=mime_type,
            original_location="Gmail", new_location="TO SORT",
            folder_id=to_sort_id or "", action="FLAGGED",
            confidence=confidence, rule_matched=rule_str,
            version_notes=f"Best guess: {destination} (via Gmail agent)",
            status="ACTIVE",
        )
        log_change(
            file_id=file_id, file_name=filename,
            change_type="GMAIL_FLAGGED", before_state="Gmail",
            after_state="TO SORT (needs review)",
            script_phase="phase6", run_id=run_id,
            notes=f"Confidence {confidence}%, best guess: {destination}",
        )
        log_review_item(
            file_id=file_id, file_name=filename,
            current_location="TO SORT",
            issue_description=(
                f"Gmail attachment, low confidence ({confidence}%). "
                f"Best guess: {destination}. Keywords: {rule_str}"
            ),
            priority="MEDIUM" if confidence >= 50 else "HIGH",
        )
        return "flagged"


# ──────────────────────────────────────────────────────────
# MAIN EMAIL PROCESSING
# ──────────────────────────────────────────────────────────

def process_email(gmail, drive, msg_id, staging_folder_id, run_id):
    """Process a single email: save body as doc, download + file attachments."""
    msg = get_message_detail(gmail, msg_id)
    headers = msg.get("payload", {}).get("headers", [])
    payload = msg.get("payload", {})

    subject = get_header(headers, "Subject") or "(No Subject)"
    sender = get_header(headers, "From") or "unknown"
    date_raw = get_header(headers, "Date") or ""

    # Parse the email date
    date_str = "000000"
    try:
        dt = parsedate_to_datetime(date_raw)
        date_str = dt.strftime("%Y%m%d")
    except Exception:
        pass

    print(f"\n  Email: {subject}")
    print(f"    From: {sender}")
    print(f"    Date: {date_raw}")

    results = {"moved": 0, "flagged": 0, "skipped": 0, "error": 0}

    # 1. Save email body as a Google Doc
    body_text = extract_email_text(payload)
    if body_text.strip():
        try:
            doc_id, doc_name = upload_email_as_doc(
                drive, subject, sender, date_raw, body_text, staging_folder_id,
            )
            print(f"    Saved email body as Doc: {doc_name}")

            # Classify and file the email doc
            content_hint = f"{subject} {sender} {body_text[:500]}"
            result = classify_and_file(
                drive, doc_id, doc_name,
                "application/vnd.google-apps.document",
                content_hint, date_str, staging_folder_id, run_id,
            )
            results[result] = results.get(result, 0) + 1
        except Exception as e:
            print(f"    ERROR saving email body: {e}")
            results["error"] += 1
    else:
        print("    (empty body, skipping doc creation)")

    # 2. Process attachments
    attachments = extract_attachments(gmail, msg_id, payload)
    if attachments:
        print(f"    Found {len(attachments)} attachment(s):")
        for att in attachments:
            att_filename = att["filename"]
            print(f"      - {att_filename} ({len(att['data_bytes'])} bytes)")

            try:
                file_id, uploaded_name, mime = upload_attachment(
                    drive, att_filename, att["mime_type"],
                    att["data_bytes"], staging_folder_id,
                )

                # Use subject + sender as content hints for classification
                content_hint = f"{subject} {sender} {att_filename}"
                result = classify_and_file(
                    drive, file_id, uploaded_name, mime,
                    content_hint, date_str, staging_folder_id, run_id,
                )
                results[result] = results.get(result, 0) + 1
            except Exception as e:
                print(f"      ERROR uploading attachment: {e}")
                results["error"] += 1
    else:
        print("    No attachments.")

    return results


def run_once(gmail=None, drive=None):
    """Process all emails with the filing label. Returns total count processed."""
    if gmail is None:
        gmail = get_gmail_service()
    if drive is None:
        drive = get_drive_service()

    start_time = time.time()
    run_id = generate_run_id("phase6")
    log_run_start(run_id, "phase6")

    counts = {"moved": 0, "flagged": 0, "skipped": 0, "error": 0}

    # Get or create the filing label
    label_id = get_or_create_label(gmail, GMAIL_LABEL_NAME)
    print(f"\n[Gmail Agent] Watching for label: '{GMAIL_LABEL_NAME}' (ID: {label_id})")

    # Get staging folder (TO SORT) to temporarily hold uploaded files
    staging_folder_id = get_folder_id_by_path(drive, "TO SORT", WORKSPACE_FOLDER_ID)
    if not staging_folder_id:
        print("ERROR: TO SORT folder not found! Run Phase 2 first.")
        log_run_end(run_id, "phase6", status="FAILED",
                    summary="TO SORT folder not found")
        return 0

    # Fetch labelled messages
    messages = get_labelled_messages(gmail, label_id)
    if not messages:
        print("  No emails with the filing label found.")
        log_run_end(run_id, "phase6", files_processed=0, status="SUCCESS",
                    summary="No emails to process")
        return 0

    print(f"  Found {len(messages)} email(s) to process:")

    total_files = 0
    for msg_ref in messages:
        msg_id = msg_ref["id"]
        try:
            results = process_email(gmail, drive, msg_id, staging_folder_id, run_id)
            for k, v in results.items():
                counts[k] = counts.get(k, 0) + v
            total_files += sum(results.values())

            # Remove the filing label (and optionally archive)
            remove_label_and_archive(gmail, msg_id, label_id)
            print(f"    Label '{GMAIL_LABEL_NAME}' removed from email.")
        except Exception as e:
            print(f"    ERROR processing email {msg_id}: {e}")
            counts["error"] += 1

    duration = time.time() - start_time
    status = "SUCCESS" if counts["error"] == 0 else "PARTIAL"
    summary = (
        f"Emails: {len(messages)}, "
        f"Files moved: {counts['moved']}, Flagged: {counts['flagged']}, "
        f"Skipped: {counts['skipped']}, Errors: {counts['error']}"
    )
    print(f"\n  {summary}")

    log_run_end(
        run_id, "phase6",
        files_processed=total_files, files_moved=counts["moved"],
        files_archived=0, files_flagged=counts["flagged"],
        files_skipped=counts["skipped"], errors=counts["error"],
        duration_seconds=duration, status=status, summary=summary,
    )

    return total_files


def run_watcher(poll_interval=60):
    """Continuous watcher mode — polls Gmail periodically for labelled emails."""
    print("=" * 60)
    print("PHASE 6 — GMAIL EMAIL FILING AGENT (watcher mode)")
    print(f"Watching for label: '{GMAIL_LABEL_NAME}'")
    print(f"Polling every {poll_interval}s...")
    print(f"Archive after filing: {ARCHIVE_AFTER_FILING}")
    print("=" * 60)

    gmail = get_gmail_service()
    drive = get_drive_service()

    while True:
        try:
            count = run_once(gmail, drive)
            if count > 0:
                print(f"\n  Processed {count} file(s) from Gmail.")
        except Exception as e:
            print(f"\n  ERROR: {e}")
        time.sleep(poll_interval)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gmail Email Filing Agent")
    parser.add_argument("--once", action="store_true",
                        help="Process labelled emails once and exit")
    parser.add_argument("--watch", action="store_true",
                        help="Continuous watcher mode")
    parser.add_argument("--interval", type=int, default=60,
                        help="Poll interval in seconds (default: 60)")
    args = parser.parse_args()

    if args.once:
        run_once()
    elif args.watch:
        run_watcher(args.interval)
    else:
        print("Usage: python gmail_agent.py --once | --watch [--interval 60]")
