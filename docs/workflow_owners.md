# Workflow Owners

All workflows are owned by Sam until formally transitioned.

| Workflow | Owner | Schedule | Phase |
|----------|-------|----------|-------|
| PLAUD Pipeline | Sam | On webhook (Zapier) | Phase 0 |
| PLAUD Status Webhook | Sam | On demand (Glance) | Phase 0 |
| Email Status Webhook | Sam | On demand (Glance) | Phase 0 |
| Backup (script) | Sam | Daily 2 AM (cron) | Phase 0 |
| PLAUD Extraction | Sam | After PLAUD pipeline | Phase 1 |
| Gate Review Webhook | Sam | On demand (Glance) | Phase 1 |
| Gate Action Webhook | Sam | On demand (Fabian) | Phase 1 |
| Midday Check-in Webhook | Sam | On demand (Glance) | Phase 1 |
| Evening Review Webhook | Sam | On demand (Glance) | Phase 1 |
| Weekly Reflection | Sam | Sunday 6 PM (cron) | Phase 1 |
| Register Stats Webhook | Sam | On demand (Glance) | Phase 1 |

## Sam's Monitoring Responsibilities

| Frequency | Check | Action if Failed |
|-----------|-------|-----------------|
| Daily | PLAUD pipeline: did transcripts process overnight? | Diagnose and fix within 4 hours. Alert Fabian if >4 hours. |
| Daily | Morning Pulse: Glance loading correctly? | Check Docker container health. Restart if needed. |
| Weekly | Register row counts: are registers growing? | Flag to Fabian if any register has zero new rows in 7 days. |
| Weekly | Confidence gate log: any silent drops? | Review error log. Fix any data being silently discarded. |
| Monthly | n8n workflow health: any failing workflows? | Review all execution logs. Fix failures. Report to Fabian. |

## Ownership Transfer

To transfer ownership:
1. Document the handover in this file.
2. Ensure the new owner understands the workflow logic, error handling, and monitoring.
3. Update health_checks component names if necessary.
