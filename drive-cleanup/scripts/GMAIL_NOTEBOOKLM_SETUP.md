# Gmail → NotebookLM Ingestion Pipeline

## Traffic & Access Solutions Pty Ltd

-----

## What It Does

1. Polls Gmail for emails matching your filter (label, sender, subject, etc.)
2. Converts each email body into a Google Doc (stays inside your Google Cloud/Drive)
3. Pushes that Doc ID directly to your NotebookLM Enterprise notebook via the official API
4. Marks the email as read and logs every ingestion so nothing runs twice

-----

## One-Time GCP Setup (15 minutes)

### 1. Enable APIs in GCP Console

Go to APIs & Services → Library and enable:

- Gmail API
- Google Docs API
- Google Drive API
- Discovery Engine API (this is the NotebookLM Enterprise API)

### 2. Create OAuth 2.0 Credentials

- APIs & Services → Credentials → Create Credentials → OAuth client ID
- Application type: **Desktop app**
- Download the JSON file → rename it to `credentials.json`
- Place it in the same folder as the script

### 3. Enable NotebookLM Enterprise

- GCP Console → Gemini Enterprise → NotebookLM Enterprise → Manage
- Start a free 14-day trial (5,000 licenses) or activate your subscription
- Assign yourself the **Cloud NotebookLM User** IAM role

### 4. Get Your Notebook ID

- Open NotebookLM Enterprise at: `https://notebooklm.google.com` (or your org's URL)
- Create a notebook or open an existing one
- The URL will contain your NOTEBOOK_ID — copy it

### 5. Get Your GCP Project Number

- GCP Console → Home → Project info card → Project number (numeric, not the name)

-----

## Configure the Script

Open `gmail_to_notebooklm.py` and set these values via environment variables or edit the defaults at the top:

```python
GCP_PROJECT_NUMBER = "123456789012"        # your numeric project number
GCP_LOCATION       = "global"              # or "us" or "eu"
NOTEBOOK_ID        = "abc123xyz"           # from the NotebookLM URL
DRIVE_FOLDER_ID    = None                  # optional: paste a Drive folder ID to organise Docs
GMAIL_QUERY        = "label:to-notebooklm is:unread"  # your Gmail filter
```

**Gmail query examples:**

- `label:portaboom is:unread` — emails with a specific label
- `from:jack@factory.com is:unread` — everything from Jack
- `subject:QC Report is:unread` — subject keyword filter
- `is:unread` — all unread (use with caution on a busy inbox)

-----

## Install & Run

```bash
# Install dependencies (once)
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests

# First run — opens browser for Google login
python gmail_to_notebooklm.py
```

On first run a browser window opens asking you to log in with your Google/Workspace account. After that, `token.json` is saved and all future runs are fully headless.

-----

## Run Automatically (Schedule It)

**Mac/Linux — cron job (every 15 minutes):**

```
*/15 * * * * cd /path/to/script && python gmail_to_notebooklm.py >> pipeline.log 2>&1
```

**n8n — Schedule trigger → Execute Command node:**

```
python /path/to/gmail_to_notebooklm.py
```

Or run it as an n8n HTTP webhook trigger if you want on-demand execution.

-----

## Output Files

| File                            | Purpose                                                 |
|---------------------------------|---------------------------------------------------------|
| `credentials.json`              | Your GCP OAuth client secret (never commit this)        |
| `token.json`                    | Auto-generated auth token (never commit this)           |
| `notebooklm_ingestion_log.json` | Full log of every ingestion with Doc IDs and timestamps |

-----

## How to Extend It

**Route different emails to different notebooks:** Add a routing dict mapping Gmail labels to NOTEBOOK_IDs and swap the target notebook per email.

**Include PDF attachments:** The script currently notes non-text attachments but doesn't convert them. PDFs can be uploaded to Drive directly as PDF sources — add a `drive_service.files().create()` call for each PDF attachment, then push the resulting file ID to NotebookLM with `mimeType: application/pdf`.

**Post confirmation to Notion:** After `push_doc_to_notebooklm()` succeeds, add a `requests.post()` call to your Notion API endpoint to log the ingestion in your BRAIN OS database.

-----

## Troubleshooting

| Problem                                   | Fix                                                                   |
|-------------------------------------------|-----------------------------------------------------------------------|
| `403 Forbidden` from NotebookLM API       | Check you have Cloud NotebookLM User IAM role assigned                |
| `invalid_grant` on token                  | Delete `token.json` and re-run to re-authenticate                     |
| No emails found                           | Test your Gmail query directly in Gmail search first                  |
| Doc created but not appearing in notebook  | NotebookLM indexing takes 1–3 minutes; check the notebook sources tab |
