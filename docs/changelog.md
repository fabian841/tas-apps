# Changelog

All notable changes to TAS Operating System are documented here.

## Architecture Reconciliation (March 2026)

- Reconciled three architecture sources: STR-003.1 (original rebuild), Fabian OS Build Manuals (Phases 0-7), and TAS-001.3 (Zoho-centric foundation).
- Decision: Zoho is source of truth for TAS operations; PostgreSQL/n8n/Glance is the intelligence layer. Both coexist. (ADR-001)
- Added migration 02_canonical_tables.sql: universal data model (deal, contact, idea, agent_finding, metric, task, product).
- Added migration 08_rockefeller_and_config.sql: quarters, meetings, scorecards, config tables, supplier/competitor seeds.
- Added capture scripts: capture_gmail.py (hourly), capture_outlook.py (hourly), sync_drive.py (daily 3 AM).
- Added 12 n8n workflows from original build manuals: email_classification, health_summary_webhook, metrics_webhook, quarterly_planning, weekly_scorecard, meeting_agenda, xero_sync, competitor_intelligence, rocks_progress_webhook, scorecard_webhook, upcoming_meetings_webhook, agent_findings_webhook.
- Glance expanded to 7 pages: added Business Snapshot and Rocks & Scorecard.
- README.md rewritten with integrated architecture diagram and week-based timeline from TAS-001.3.
- .env.example updated with Xero and Perplexity credentials.

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

## Phase 3 — Automation & Agents (March 2026)

- Architecture: Claude Code remote agents replace custom Clawdbot — native MCP, tool use, context.
- Database: mcp_servers, agent_sessions, agent_findings tables (migration 07).
- Two agent contexts: Personal (PIL) and Company (GPX), hard-isolated via separate CLAUDE.md and .mcp.json.
- 3 Zoho MCP servers: zoho-crm (contacts, accounts, deals), zoho-desk (tickets), zoho-books (invoices).
- MCP server registry with 7 servers seeded (postgres-personal, postgres-company, google-sheets, zoho-crm, zoho-desk, zoho-books, filesystem).
- Personal agent: scheduled morning prep (6 AM), evening prep (5:30 PM), on-demand via POST /agent-personal.
- Company agent: scheduled Daily Flash prep (7 AM weekdays), weekly pipeline review (Monday 8 AM), on-demand via POST /agent-company.
- Agent findings follow same confidence gate as PIL: all output is PROPOSED, only Fabian confirms.
- Agent Monitor: new Glance page with session history, findings stats, and MCP server health.
- n8n webhooks: /agent-status, /agent-personal, /agent-company.
- Documentation: agent architecture, MCP server setup, agent CLAUDE.md system prompts.
