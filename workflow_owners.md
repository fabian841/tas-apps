# Fabian OS – Workflow Ownership Registry

Every n8n workflow must have a named owner responsible for its operation, monitoring, and maintenance.

| Workflow | Owner | Phase | Description | Schedule |
|----------|-------|-------|-------------|----------|
| Health Summary Webhook | Fabian | 0 | `/health-summary` endpoint – returns component health status for Glance dashboard | On-demand (webhook) |
| System Health Check | Fabian | 0 | Checks for unhealthy components, logs alerts, sends notifications | Every 15 minutes |
| Gmail Capture | Fabian | 0 | Triggers `gmail_capture.py` for incremental email sync | Every 15 minutes (via cron or n8n) |
| Drive Capture | Fabian | 0 | Triggers `drive_capture.py` for incremental file metadata sync | Every 30 minutes (via cron or n8n) |

## Ownership Rules

1. Every workflow **must** have an owner before activation.
2. The owner is responsible for monitoring execution logs and health status.
3. If a workflow enters error state, the owner is the first responder.
4. Ownership transfers must be documented here with the date of transfer.
5. Orphaned workflows (no owner) must be deactivated until ownership is assigned.

## Adding a New Workflow

When adding a new workflow to n8n:

1. Add a row to this table with the workflow name, owner, phase, description, and schedule.
2. Ensure the workflow has: timeout, retry logic, error path, logging, and idempotency.
3. Register the component in the `health_checks` table.
4. Export the workflow JSON to `n8n/workflows/` and commit to the repository.
