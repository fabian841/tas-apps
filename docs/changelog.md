# Changelog

All notable changes to the Fabian Operating System are documented here.

## Phase 0 – Initial Commit (March 2026)

- Created database schema: raw tables (`raw_emails`, `raw_drive_files`, `raw_agent_output`).
- Created canonical tables: `canonical_deal`, `canonical_contact`, `canonical_idea`, `canonical_agent_finding`, `canonical_metric`, `canonical_task`, `canonical_product`.
- Created `event_log` with BRIN indexes for efficient time-range queries.
- Created `health_checks` and `credential_expiry` tables for monitoring.
- Added JSON schemas for all canonical objects.
- Created `docker-compose.yml` with PostgreSQL (pgvector) and n8n services.
- Created capture scripts: `capture_gmail.py`, `capture_outlook.py`, `sync_drive.py`.
- Created `backup.sh` with Healthchecks.io integration.
- Created Glance dashboard configuration (`config.yml`).
- Created documentation: data ownership matrix, workflow owners, restore procedure.
- Added `.env.example` template for environment variables.
