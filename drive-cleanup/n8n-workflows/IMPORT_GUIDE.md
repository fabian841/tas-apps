# N8N Workflow Import Guide

## Prerequisites

1. Set environment variables in your n8n instance:
   - `N8N_BASE_URL` — Your n8n URL (e.g. `https://n8n.yourdomain.com`)
   - `N8N_API_KEY` — API key from n8n Settings > API
   - `GOOGLE_ACCOUNT` — Email for reports (default: fabian@fdnxt.com)

2. Create an HTTP Header Auth credential named **"n8n API Key"**:
   - Header Name: `X-N8N-API-KEY`
   - Header Value: your n8n API key

## Workflows

### 01 — Stale Workflow Detection & Deactivation
- **Schedule:** Daily
- **What it does:** Finds workflows not updated in 90+ days, auto-deactivates any that are still active, emails a report
- **Import:** n8n > Workflows > Import from File > select `01_stale_workflow_detection.json`

### 02 — Old Execution Cleanup
- **Schedule:** Weekly (Sunday 3AM)
- **What it does:** Deletes successful and failed executions older than 30 days, emails a cleanup report
- **Import:** n8n > Workflows > Import from File > select `02_execution_cleanup.json`

### 03 — Workflow Organiser (Tags & Folders)
- **Trigger:** Manual (run once, then as needed)
- **What it does:** Scans all workflow names, auto-creates and applies tags based on keyword patterns, generates a folder-grouping report via email
- **Import:** n8n > Workflows > Import from File > select `03_workflow_organiser.json`
- **Customise:** Edit the `TAG_RULES` and `FOLDER_RULES` arrays in the "Classify by Tags & Folders" node to match your naming conventions

## After Import

1. Import all 3 JSON files via n8n UI
2. Set up the HTTP Header Auth credential (see Prerequisites)
3. Activate workflows 01 and 02 (they run on schedule)
4. Run workflow 03 manually once to tag and organise existing workflows
5. Review the email reports
