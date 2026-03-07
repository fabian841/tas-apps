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

## Phase 1 Data

| Data Type | Layer | Owner | Storage | Retention |
|-----------|-------|-------|---------|-----------|
| PIL Registers (8 sheets) | Personal | Fabian | Google Sheets + `confidence_gate_log` | Permanent |
| Extraction runs | System | System | `extraction_run` | 2 years |
| Confidence gate log | Personal | Fabian | `confidence_gate_log` | Permanent (audit trail) |

## Phase 2 Data

| Data Type | Layer | Owner | Storage | Retention |
|-----------|-------|-------|---------|-----------|
| Zoho CRM contacts | Company | TAS | `zoho_contacts` + Zoho | Synced every 4h |
| Zoho CRM accounts | Company | TAS | `zoho_accounts` + Zoho | Synced every 4h |
| Zoho CRM deals | Company | TAS | `zoho_deals` + Zoho | Synced every 4h |
| Zoho Desk tickets | Company | TAS | `zoho_tickets` + Zoho | Synced every 4h |
| Zoho Books invoices | Company | TAS | `zoho_invoices` + Zoho | Synced every 4h |
| PB4000 product doctrine | Company | TAS | `product_doctrine` | Permanent |
| Warranty registrations | Company | TAS | `warranty_registrations` | Permanent |
| Warranty claims | Company | TAS | `warranty_claims` | Permanent (audit trail) |
| Zoho sync log | System | System | `zoho_sync_log` | 1 year |

## Future Phases

| Data Type | Layer | Phase | Storage |
|-----------|-------|-------|---------|
| Agent findings | Company | Phase 3+ | `canonical_agent_finding` |

## Access Control

- **fabian_admin**: Full superuser access for migrations and schema changes.
- **fabian_app**: Application-level access (SELECT, INSERT, UPDATE, DELETE on all tables except restricted).
  - `event_log`: INSERT and SELECT only (no UPDATE/DELETE) to preserve audit trail.

## Change Policy

Any changes to data ownership or access must follow the tiered change management process.
