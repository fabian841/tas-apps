# LIFE OS

Unified operating system for Fabian Diaz and Traffic & Access Solutions.
Two layers — Personal and Company — share infrastructure but never share data.

**Spec:** STR-003.1 LIFE OS Unified Specification (supersedes PIL v2.1, GPX v1.1, BRAIN-001.x, Fabian OS Phase 0-7)

## Architecture

- **pgvector** (0.8.2-pg17) — Vector database for semantic memory across all registers
- **n8n** (2.9.0) — Workflow orchestration — all automation pipelines
- **Glance** (v0.7.4) — Morning Pulse dashboard — personal intelligence surface
- **Mac mini** (24/7) — Always-on host at `/opt/fabian-os/`

## Repository Structure

```
├── docker-compose.yml          # pgvector + n8n + Glance stack
├── migrations/                 # SQL migration files (run on first start)
├── n8n-workflows/              # Exported n8n workflow definitions
├── glance/                     # Morning Pulse dashboard configuration
├── scripts/                    # Backup and utility scripts
├── docs/
│   ├── email_triage_sop.md     # Phase 0 email triage procedure
│   ├── drive_structure.md      # Google Drive 12-folder structure
│   ├── restore_procedure.md    # Disaster recovery procedure
│   ├── workflow_owners.md      # Workflow ownership registry
│   ├── changelog.md            # All changes logged here
│   └── adr/                    # Architecture Decision Records
└── .env.example                # Environment variables template
```

## Phases

| Phase | Name | Stability Gate | What It Delivers |
|-------|------|---------------|-----------------|
| **0** | Core Foundation | 14 days | PLAUD pipeline, Morning Pulse, email triage habit, Drive structure |
| **1** | Personal OS Live | 14 days | 8 registers, confidence gating, 4 daily touchpoints, PLAUD extraction |
| **2** | Company OS (GPX) | 14 days | Zoho config, PB4000 doctrine, warranty engine, Daily Flash |
| **3** | Automation & Agents | 30 days | Clawdbot personal + company, Zoho MCP |
| **4** | Governance | 28 days | Compliance agent, DR drills, change control |
| **5** | Advanced Intelligence | 30 days (optional) | MemCP, claude-brain, Ghost |
| **6** | Agent Swarm | 30 days/agent | Regulatory, tech scout, supplier risk, etc. |
| **7** | Team Scaling | 14 days | Multi-user access, role-based dashboards |

## Governing Principles

1. Only CONFIRMED is truth
2. AI outputs are proposals — never authoritative
3. State is defined by position, not labels
4. Patterns, not events (3+ occurrences minimum)
5. Evidence-backed, confidence-labelled
6. Learning only counts if it changes behaviour
7. Personal and Company data are a hard boundary
8. The system observes and surfaces — never prescribes

## Quick Start (Phase 0)

1. Copy `.env.example` to `/opt/fabian-os/.env`, fill in credentials, `chmod 600 .env`
2. `docker-compose up -d` — starts pgvector, n8n, and Glance
3. Fix PLAUD > Zapier > n8n pipeline (Sam's first task)
4. Begin 14-day email triage habit (manual, no automation)
5. Check Morning Pulse dashboard every morning at 6:30am
