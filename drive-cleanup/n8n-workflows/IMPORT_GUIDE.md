# N8N Workflow Import Guide — TAS Drive Cleanup

## Prerequisites

### 1. Google Sheet — Central Audit Dashboard

Create a single Google Sheet called **"TAS_N8N_Audit"** with 3 tabs:

| Tab Name | Written By | Contains |
|----------|-----------|----------|
| `Stale_Workflows` | Workflow 01 | Every stale workflow detected, action taken, protection status |
| `Execution_Cleanup` | Workflow 02 | Cleanup stats per run — deleted, failed, skipped, by status |
| `Workflow_Organisation` | Workflow 03 | Every workflow classified — tags, folder, confidence scores |

Add these column headers to each tab:

**Stale_Workflows:**
`Timestamp | Workflow ID | Workflow Name | Active | Tags | Days Since Update | Days Since Created | Action | Reason | Protected`

**Execution_Cleanup:**
`Timestamp | Retention Days | Cutoff Date | Total Scanned | Total Deleted | Total Failed | Total Skipped | Success Deleted | Error Deleted | Dry Run | Oldest Found | Newest Deleted | Errors`

**Workflow_Organisation:**
`Timestamp | Workflow ID | Workflow Name | Active | Node Count | Existing Tags | New Tags Applied | All Tags | Folder | Folder Confidence | Folder Rule | Needed Update`

Copy the Sheet ID from the URL and set it as `TAS_AUDIT_SHEET_ID` in your n8n environment variables.

### 2. N8N Credentials

Create these credentials in n8n:

- **"n8n API Key"** (HTTP Header Auth):
  - Header Name: `X-N8N-API-KEY`
  - Header Value: your n8n API key

- **"Google Sheets OAuth2"** (Google Sheets OAuth2):
  - Connect your Google account that has access to the audit sheet

### 3. N8N Environment Variables

Set these in n8n Settings > Environment Variables:

| Variable | Description |
|----------|-------------|
| `N8N_BASE_URL` | Your n8n URL (e.g. `https://n8n.yourdomain.com`) — no trailing slash |
| `N8N_API_KEY` | API key from n8n Settings > API |
| `TAS_AUDIT_SHEET_ID` | Google Sheet ID for the central audit dashboard |

## Workflows

### 01 — Stale Workflow Detection & Deactivation
- **Schedule:** Daily 6AM
- **What it does:** Scans all workflows, flags those untouched for 90+ days, auto-deactivates stale active ones (with protection rules), logs every action to Google Sheet, emails summary
- **Config:** `STALE_DAYS`, `EMAIL_RECIPIENT`, `SHEET_ID`, `AUTO_DEACTIVATE`, `PROTECTED_PATTERNS`

### 02 — Old Execution Cleanup
- **Schedule:** Weekly Sunday 3AM
- **What it does:** Deletes successful and failed executions older than 30 days, tracks stats by workflow and status, logs to Google Sheet, emails report
- **Config:** `RETENTION_DAYS`, `MAX_PER_RUN`, `BATCH_SIZE`, `EMAIL_RECIPIENT`, `SHEET_ID`, `STATUSES_TO_CLEAN`, `AUTO_DELETE`

### 03 — Workflow Organiser (Tags & Folders)
- **Schedule:** Weekly Monday 7AM
- **What it does:** Scans all workflow names + node types, auto-tags with confidence scoring, groups into logical folders, creates missing tags via API, logs everything to Google Sheet, emails organisation report
- **Config:** `TAG_RULES[]`, `FOLDER_RULES[]`, `EMAIL_RECIPIENT`, `SHEET_ID`, `AUTO_APPLY_TAGS`

## Import Steps

1. In n8n: **Workflows > Import from File** — import all 3 JSON files
2. Open each workflow and verify the "⚙️ Configuration" node has correct values
3. Verify credentials are connected (n8n API Key + Google Sheets OAuth2)
4. **Activate** all 3 workflows
5. Optionally run each once manually to verify they work

## Configuration

All configurable values live in the **"⚙️ Configuration"** node at the start of each workflow. Edit thresholds, rules, and recipients there without touching any logic nodes.

Each workflow also supports **dry-run mode** — set `AUTO_DEACTIVATE`, `AUTO_DELETE`, or `AUTO_APPLY_TAGS` to `false` to get reports without making changes.
