# Data Ownership Matrix

| Data Type | Owner | Source System | Canonical Table | Retention |
|-----------|-------|---------------|-----------------|-----------|
| Emails (Gmail) | Fabian | Gmail API | `raw_emails` | 1 year |
| Emails (Outlook) | Fabian | Microsoft Graph | `raw_emails` | 1 year |
| Drive Files | Fabian | Google Drive API | `raw_drive_files` | Permanent (metadata) |
| Deals | Fabian | Zoho CRM | `canonical_deal` | Permanent |
| Contacts | Fabian | Zoho CRM | `canonical_contact` | Permanent |
| Ideas | Fabian | Idea Vault | `canonical_idea` | Permanent |
| Agent Findings | System | Agents (n8n) | `canonical_agent_finding` | Permanent |
| Metrics / KPIs | System | Zoho / Xero | `canonical_metric` | Permanent |
| Tasks | Fabian | Zoho Projects | `canonical_task` | Permanent |
| Products | Fabian | Zoho / Manual | `canonical_product` | Permanent |
| Event Log | System | All components | `event_log` | 2 years |
| Workflow Logs | System | n8n | `workflow_logs` | 90 days |
| Health Checks | System | All components | `health_checks` | Current state only |

## Access Control

- **fabian_admin**: Full superuser access for migrations and schema changes.
- **fabian_app**: Application-level access (SELECT, INSERT, UPDATE, DELETE on all tables except restricted).
  - `event_log`: INSERT and SELECT only (no UPDATE/DELETE) to preserve audit trail.

## Change Policy

Any changes to data ownership or access must follow the tiered change management process (see `change_management.md` when available).
