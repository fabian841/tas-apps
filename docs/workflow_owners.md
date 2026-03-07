# Workflow Owners

All workflows are owned by Sam until formally transitioned.

| Workflow | Owner | Schedule | Phase |
|----------|-------|----------|-------|
| Email Classification | Sam | Hourly | Phase 0 |
| Weekly Scorecard | Sam | Monday 8 AM | Phase 0 |
| Gmail Capture (script) | Sam | Hourly (cron) | Phase 0 |
| Outlook Capture (script) | Sam | Hourly (cron) | Phase 0 |
| Drive Sync (script) | Sam | Daily 3 AM (cron) | Phase 0 |
| Backup (script) | Sam | Daily 2 AM (cron) | Phase 0 |
| Health Summary Webhook | Sam | On demand | Phase 0 |
| Metrics Webhook | Sam | On demand | Phase 0 |

## Ownership Transfer

To transfer ownership:
1. Document the handover in this file.
2. Ensure the new owner understands the workflow logic, error handling, and monitoring.
3. Update health_checks component names if necessary.
