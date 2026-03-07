# Data Ownership Matrix

## Isolation Rule (Non-Negotiable)

No function in the Company layer may read Personal layer data.
No Personal register may be visible in any staff-facing output.
If a Personal insight becomes relevant to the Company, Fabian promotes it manually — logged, deliberate, bounded.

## Phase 0 Data

| Data Type | Layer | Owner | Storage | Retention |
|-----------|-------|-------|---------|-----------|
| PLAUD transcripts | Personal | Fabian | `raw_transcripts` + Drive 00_INBOX | Permanent |
| Emails (Gmail) | Both | Fabian | `raw_emails` | 1 year |
| Emails (M365 forwarded) | Both | Fabian | `raw_emails` | 1 year |
| Drive file metadata | Both | Fabian | `raw_drive_files` | Permanent |
| Event log | System | System | `event_log` | 2 years |
| Health checks | System | System | `health_checks` | Current state only |

## Future Phases

| Data Type | Layer | Phase | Storage |
|-----------|-------|-------|---------|
| PIL Registers (8 sheets) | Personal | Phase 1 | Google Sheets |
| Zoho CRM/Desk/Books data | Company | Phase 2 | Zoho + canonical tables |
| Agent findings | Company | Phase 3+ | `canonical_agent_finding` |

## Access Control

- **fabian_admin**: Full superuser access for migrations and schema changes.
- **fabian_app**: Application-level access (SELECT, INSERT, UPDATE, DELETE on all tables except restricted).
  - `event_log`: INSERT and SELECT only (no UPDATE/DELETE) to preserve audit trail.

## Change Policy

Any changes to data ownership or access must follow the tiered change management process.
