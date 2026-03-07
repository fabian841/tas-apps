# Changelog

All notable changes to LIFE OS are documented here.

## Phase 0 — Core Foundation (March 2026)

- Rebuilt repository from LIFE OS Unified Specification (STR-003.1).
- Infrastructure: Docker stack with pgvector (0.8.2-pg17), n8n (2.9.0), Glance (v0.7.4).
- Database: raw_emails, raw_drive_files, raw_transcripts, raw_agent_output, event_log, health_checks.
- PLAUD pipeline: n8n workflow (Zapier webhook > Drive 00_INBOX > Gmail confirm).
- Morning Pulse: Glance dashboard (time, weather, calendar, email status, PLAUD status).
- n8n webhooks for Glance: /plaud-status, /email-status.
- Documentation: email triage SOP, Drive 12-folder structure, restore procedure, workflow owners.
- Backup script with Healthchecks.io integration.

## Phase 1 — Personal OS Live (March 2026)

- Database: register_metadata, confidence_gate_log, extraction_run tables (migration 05).
- 8 PIL register schemas: decisions, commitments, ideas, learnings, relationships, health, finance, patterns.
- Confidence gating engine: PROPOSED -> CONFIRMED/REJECTED lifecycle. Only Fabian promotes.
- PLAUD extraction workflow: Claude API (claude-sonnet-4-6) extracts structured items from transcripts.
- Gate action webhook: POST /gate-action for Fabian to confirm/reject items.
- 4 daily touchpoints via Glance: Morning Pulse, Midday Check-in, Evening Review (+ Weekly Reflection email).
- n8n webhooks: /gate-review, /gate-action, /midday-checkin, /evening-review, /register-stats.
- Weekly reflection email: Sunday 6 PM with gate summary, confirmation rate, backlog.
- Documentation: confidence gating, touchpoints, register schemas.

## Phase 2 — Company OS / GPX (March 2026)

- Database: zoho_contacts, zoho_accounts, zoho_deals, zoho_tickets, zoho_invoices, product_doctrine, warranty_registrations, warranty_claims, zoho_sync_log tables (migration 06).
- Zoho sync workflow: CRM (contacts, accounts, deals), Desk (tickets), Books (invoices) synced every 4 hours.
- PB4000 doctrine: codified product knowledge for all PORTABOOM variants (basic, TASTrack, TMA, event, rapid) and MINIBOOM TZ30. Seeded in DB + JSON schema.
- Warranty engine: registration, claims, daily expiry checks (30-day warning), email alerts.
- Warranty webhooks: POST /warranty-register, POST /warranty-claim.
- Daily Flash: company intelligence surface in Glance — pipeline, revenue MTD, overdue invoices, support tickets, warranty status, deals closing this week.
- Hard isolation boundary enforced: Daily Flash queries Company tables only.
- Documentation: PB4000 doctrine, warranty engine, updated data ownership matrix.
