# Fabian Operating System

A founder-scale life & business operating system that automatically captures information from multiple sources, stores it in a layered data platform, orchestrates workflows and agents, and provides a unified dashboard.

## Architecture

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| Control | GitHub, Migrations, Schema Registry | Governance, version control, change management |
| Data Platform | PostgreSQL + pgvector | Raw → Canonical → Event Log (three sub-layers) |
| Automation | n8n (self-hosted) | Workflow orchestration, agents, integrations |
| Research | Claude + Perplexity + NotebookLM | Synthesis, live research, document reasoning |
| Interface | Glance | Lightweight dashboard: health, metrics, alerts |
| External | Zoho, Xero | CRM, accounting (API integration via n8n) |

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env
# Edit .env with your credentials

# 2. Start all services
docker compose up -d

# 3. Run database migrations (production)
./migrations/run_migrations.sh prod

# 4. Run database migrations (staging)
./migrations/run_migrations.sh dev

# 5. Access services
#    n8n:    http://localhost:5678
#    Glance: http://localhost:8080
#    PostgreSQL: localhost:5432
```

## Directory Structure

```
migrations/     Versioned SQL migration files + runner script
schemas/        JSON Schema registry for canonical objects
config/         Service configuration (Glance YAML)
scripts/        Capture scripts (Gmail, Google Drive)
n8n/workflows/  n8n workflow export templates
docs/           Architecture docs, runbooks, restore procedures
```

## Phase 0 Success Gate

- [ ] 7 days stable capture
- [ ] 2 workflows operational
- [ ] Canonical objects defined (schemas + tables)
- [ ] Raw / Canonical / Event Log tables exist and populated

See [docs/architecture.md](docs/architecture.md) for the full architecture document.
