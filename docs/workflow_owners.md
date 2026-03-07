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
| Zoho Sync | Sam | Every 4 hours (cron) | Phase 2 |
| Warranty Engine | Sam | Daily 7 AM (cron) | Phase 2 |
| Warranty Register Webhook | Sam | On demand (API) | Phase 2 |
| Warranty Claim Webhook | Sam | On demand (API) | Phase 2 |
| Daily Flash Webhook | Sam | On demand (Glance) | Phase 2 |
| Personal Agent Trigger | Sam | Daily 6 AM + 5:30 PM (cron) + on demand | Phase 3 |
| Company Agent Trigger | Sam | Weekdays 7 AM + Monday 8 AM (cron) + on demand | Phase 3 |
| Agent Status Webhook | Sam | On demand (Glance) | Phase 3 |
| Zoho CRM MCP Server | Sam | Persistent (stdio) | Phase 3 |
| Zoho Desk MCP Server | Sam | Persistent (stdio) | Phase 3 |
| Zoho Books MCP Server | Sam | Persistent (stdio) | Phase 3 |
| Email Classification | Sam | Hourly (cron) | Reconciliation |
| Health Summary Webhook | Sam | On demand (Glance) | Reconciliation |
| Metrics Webhook | Sam | On demand (Glance) | Reconciliation |
| Quarterly Planning | Sam | 1st day of quarter 8 AM (cron) | Reconciliation |
| Weekly Scorecard | Sam | Monday 7 AM (cron) | Reconciliation |
| Meeting Agenda Generator | Sam | Friday 4 PM (cron) | Reconciliation |
| Xero Sync | Sam | Daily 6 AM (cron) | Reconciliation |
| Competitor Intelligence | Sam | Monday 6 AM (cron) | Reconciliation |
| Rocks Progress Webhook | Sam | On demand (Glance) | Reconciliation |
| Scorecard Webhook | Sam | On demand (Glance) | Reconciliation |
| Upcoming Meetings Webhook | Sam | On demand (Glance) | Reconciliation |
| Agent Findings Webhook | Sam | On demand (Glance) | Reconciliation |
| Gmail Capture (script) | Sam | Hourly (cron) | Reconciliation |
| Outlook Capture (script) | Sam | Hourly offset 30m (cron) | Reconciliation |
| Drive Sync (script) | Sam | Daily 3 AM (cron) | Reconciliation |

| Pipeline Forecast | Sam | Monday 6 AM (cron) | Phase 4 |
| Deal Scoring Agent | Sam | Monday 7 AM (cron) | Phase 4 |
| Forecast Webhook | Sam | On demand (Glance) | Phase 4 |
| Regulatory Change Monitor | Sam | Wednesday 5 AM (cron) | Phase 5 |
| Certification Expiry Check | Sam | Daily 7:30 AM (cron) | Phase 5 |
| Tender Scanner | Sam | Tuesday 5:30 AM (cron) | Phase 6 |
| Supplier Risk Assessment | Sam | Monthly 1st 6 AM (cron) | Phase 6 |
| Tenders Webhook | Sam | On demand (Glance) | Phase 6 |
| TZ30 Launch Tracker | Sam | Friday 8 AM (cron) | Phase 7 |
| Tech Scout Agent | Sam | Thursday 4 AM (cron) | Phase 7 |
| TZ30 Milestones Webhook | Sam | On demand (Glance) | Phase 7 |

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
