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
