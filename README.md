# TAS Operating System — Intelligence & Automation Layer

Unified operating system for Fabian Diaz and Traffic & Access Solutions.
Two systems work together: **Zoho One** (source of truth for business operations) and **this repo** (intelligence, automation, and personal OS).

**Architecture documents:**
- **TAS-001.3** — TAS Operating System Foundation Architecture (Zoho-centric, Joel supervises)
- **Fabian OS Build Manuals 0-7** — Intelligence layer architecture (PostgreSQL/n8n/Glance, Claude builds)
- **PIL/GPX extensions** — Personal registers, confidence gating, PB4000 doctrine, warranty engine

## Integrated Architecture

```
┌─────────────────────────────────────────────────────────┐
│  ZOHO ONE (Source of Truth — TAS-001.3)                 │
│  CRM · Desk · Inventory · Books · Projects · Flow       │
│  Joel supervises · Claude reads/writes via Zoho MCP     │
└────────────────────────┬────────────────────────────────┘
                         │ Zoho Sync (every 4h) + MCP (real-time)
┌────────────────────────▼────────────────────────────────┐
│  THIS REPO — Intelligence & Automation Layer            │
│                                                         │
│  pgvector (0.8.2-pg17)    n8n (2.9.0)    Glance (v0.7.4)│
│  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐   │
│  │ Canonical │  │ Workflows│  │ Dashboards          │   │
│  │ Tables    │  │ 20+      │  │ Morning Pulse       │   │
│  │ PIL Regs  │  │ Agents   │  │ Midday · Evening    │   │
│  │ Agent     │  │ Sync     │  │ Daily Flash · Agent  │   │
│  │ Findings  │  │ Xero     │  │ Rocks · Financial    │   │
│  └──────────┘  └──────────┘  └─────────────────────┘   │
│                                                         │
│  Claude Code Agents (Personal + Company, hard-isolated) │
│  MCP Servers: Zoho CRM/Desk/Books, Postgres, Sheets    │
│  Mac mini (24/7) at /opt/fabian-os/                     │
└─────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  EXTERNAL INTEGRATIONS                                  │
│  Xero (statutory accounting) · Gmail · M365 · PLAUD    │
│  Google Drive · Google Sheets · Perplexity              │
└─────────────────────────────────────────────────────────┘
```

## Repository Structure

```
├── docker-compose.yml          # pgvector + n8n + Glance stack
├── migrations/                 # SQL migration files (run in order)
│   ├── 01_raw_tables.sql       # Raw ingestion (emails, drive, transcripts)
│   ├── 02_canonical_tables.sql # Universal data model (deal, contact, idea, metric, task, product)
│   ├── 03_event_log.sql        # Append-only audit trail
│   ├── 04_health.sql           # Health checks + credential expiry
│   ├── 05_registers_and_gating.sql  # PIL registers + confidence gate
│   ├── 06_company_os.sql       # Zoho mirror tables + PB4000 doctrine + warranty
│   ├── 07_agent_framework.sql  # MCP registry + agent sessions + findings
│   ├── 08_rockefeller_and_config.sql  # Quarters, meetings, scorecards, config tables
│   ├── 09_forecasting.sql       # Pipeline forecast, deal scoring, revenue targets
│   ├── 10_compliance.sql        # Regulatory changes, compliance checklists, certifications
│   ├── 11_tender_intelligence.sql  # Tenders, supplier risk, bid evaluations
│   └── 12_tz30_launch.sql       # TZ30 milestones, subscriptions, tech scout, agent swarm
├── n8n-workflows/              # 38 exported n8n workflow definitions
├── glance/                     # Dashboard configuration (10 pages)
├── scripts/
│   ├── backup.sh               # Daily DB backup + Healthchecks.io ping
│   ├── capture_gmail.py        # Gmail incremental sync to raw_emails
│   ├── capture_outlook.py      # M365 Graph API polling to raw_emails
│   ├── sync_drive.py           # Google Drive metadata + download sync
│   └── requirements.txt        # Python dependencies for capture scripts
├── schemas/
│   ├── pil_registers.json      # 8 PIL register definitions
│   └── pb4000_doctrine.json    # PB4000 product family specs
├── agents/
│   ├── personal/               # Personal agent (CLAUDE.md + .mcp.json)
│   └── company/                # Company agent (CLAUDE.md + .mcp.json)
├── mcp-servers/
│   ├── zoho-crm/               # Zoho CRM MCP server (contacts, accounts, deals)
│   ├── zoho-desk/              # Zoho Desk MCP server (tickets)
│   └── zoho-books/             # Zoho Books MCP server (invoices)
├── docs/
│   ├── adr/                    # Architecture Decision Records
│   ├── agent_architecture.md   # Claude Code agent design
│   ├── changelog.md            # All changes logged here
│   ├── confidence_gating.md    # PIL confidence gate lifecycle
│   ├── data_ownership.md       # Data ownership matrix
│   ├── drive_structure.md      # Google Drive 12-folder structure
│   ├── email_triage_sop.md     # Email triage procedure
│   ├── pb4000_doctrine.md      # PB4000 product reference
│   ├── restore_procedure.md    # Disaster recovery procedure
│   ├── touchpoints.md          # 4 daily touchpoints
│   ├── warranty_engine.md      # Warranty lifecycle
│   └── workflow_owners.md      # Workflow ownership registry
└── .env.example                # Environment variables template
```

## Build Timeline (Week-Based, from TAS-001.3)

| Week | Deliverable | Zoho (Joel supervises) | This Repo (Claude builds) |
|------|-------------|----------------------|--------------------------|
| **1** | MCP Live + CRM | Zoho MCP connected. CRM Blueprint configured. M365 email connected. | Docker stack up. Raw tables + canonical tables. Capture scripts running. |
| **2** | Desk + Forms | Desk case management live. Pre-start inspection form. | PIL registers + confidence gating. PLAUD extraction pipeline. Email classification. |
| **3** | Inventory + Books | Inventory connected. Books-Xero sync. | Zoho sync workflow. Xero sync. Weekly scorecard. PB4000 doctrine. |
| **4** | Phase 1 Complete | All critical modules live. Phase 1 review. | Warranty engine. Daily Flash. 4 touchpoints in Glance. Rockefeller Habits. |
| **5-6** | Flow + Sign | Zoho Flow automations. Sign deployed. | Claude Code agents + MCP servers. Agent Monitor in Glance. |
| **7-8** | PLAUD + Cliq | PLAUD pipeline end-to-end. Cliq configured. | Competitor intelligence agent. n8n PLAUD processing. |
| **9** | Phase 2 Review | All Phase 2 modules live. | All agent workflows stable. |
| **10-14** | Campaigns + Analytics + Subscriptions | TZ30 subscription billing. Analytics dashboards. | Governance: compliance agent, DR drills, data retention. |
| **15-18** | People + Commerce + AI Assistant | HR, online store, customer AI (Claude API). | Agent swarm: regulatory, tech scout, supplier risk. |
| **Post Oct** | Phase 5 | TZ30 launched. System stable. | MemCP, claude-brain, Ghost (optional). Team scaling. |

## Governing Principles

1. Only CONFIRMED is truth
2. AI outputs are proposals — never authoritative
3. State is defined by position, not labels
4. Patterns, not events (3+ occurrences minimum)
5. Evidence-backed, confidence-labelled
6. Learning only counts if it changes behaviour
7. Personal and Company data are a hard boundary
8. The system observes and surfaces — never prescribes
9. Zoho is the source of truth for all TAS operations
10. No build without approved design — one build, done right

## Working Model (from TAS-001.3)

| Role | Person | Responsibility |
|------|--------|---------------|
| **Director** | Fabian Diaz | Strategy, approvals, sign-off. Reviews all designs before build. |
| **Incoming COO** | Tynan Diaz (June 2026) | Operations oversight, team management, process compliance. |
| **Project Supervisor** | Joel | Supervises Zoho config, project management, sandbox testing. |
| **Code Builder** | Claude | Writes all code in this repo. Designs processes. QAs via MCP. Generates intelligence briefs. |
| **Developer** | Sam Marciano | TASTrack IoT platform, Zoho Creator mobile apps. |

## Quick Start

1. Copy `.env.example` to `/opt/fabian-os/.env`, fill in credentials, `chmod 600 .env`
2. `docker-compose up -d` — starts pgvector, n8n, and Glance
3. `./scripts/init.sh` — creates app user, runs all 8 migrations, grants permissions
4. `./scripts/import-workflows.sh` — imports all n8n workflows via API
5. `./scripts/setup-cron.sh` — registers capture scripts + backup to crontab
6. `./scripts/smoke-test.sh` — validates tables, endpoints, MCP servers
7. Check Morning Pulse dashboard at `http://localhost:8080`
