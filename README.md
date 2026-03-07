# Fabian Operating System

A founder-scale operating system that captures, organises, and automates business operations.

## Architecture

- **PostgreSQL** (pgvector) – Central data store with raw ingestion tables, canonical business objects, event log, and health monitoring.
- **n8n** – Workflow automation engine for email classification, scorecards, and future agent workflows.
- **Glance** – Lightweight dashboard for real-time system health and business metrics.
- **Capture Scripts** – Python scripts for Gmail, Outlook, and Google Drive ingestion.

## Quick Start

1. Copy `.env.example` to `.env` and fill in credentials (`chmod 600 .env`).
2. Start the stack: `docker-compose up -d`
3. Apply migrations (auto-run on first PostgreSQL start via `postgres/init/`).
4. Configure cron jobs for capture scripts and backups.
5. Build n8n workflows (email classification, weekly scorecard) in the n8n UI.
6. Start Glance dashboard.

See the Phase 0 Build Manual for detailed instructions.

## Repository Structure

```
├── docker-compose.yml          # PostgreSQL + n8n stack
├── schemas/                    # JSON schemas for canonical objects
├── migrations/                 # SQL migration files
├── n8n-workflows/              # Exported n8n workflow definitions
├── glance/                     # Glance dashboard configuration
├── scripts/                    # Capture and backup scripts
├── docs/                       # Documentation
│   ├── data_ownership.md
│   ├── workflow_owners.md
│   ├── restore_procedure.md
│   ├── changelog.md
│   └── adr/                    # Architecture Decision Records
└── .env.example                # Environment variables template
```

## Phases

- **Phase 0** – Foundation: database, capture, monitoring, backup _(current)_
- **Phase 1** – Business OS: Rockefeller Habits, Zoho/Xero integration
- **Phase 2** – Agent POC: Competitor intelligence agent
- **Phase 3** – Ideation pipeline: Idea vault, feasibility research, MVP tracking
- **Phase 4** – Governance: Compliance checks, data retention, DR drills
- **Phase 5** – Advanced intelligence (optional): MemCP, claude-brain, Ghost
- **Phase 6** – Agent swarm: Regulatory, tech scout, supplier risk, and more
- **Phase 7** – Team scaling: Multi-user access and role-based dashboards
