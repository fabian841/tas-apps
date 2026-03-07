# Fabian Operating System – Final Architecture

**Version:** 5.0 (Final)
**Date:** March 2026
**Status:** Locked – Ready for Implementation

This document defines the complete architecture of your Life & Business Operating System. It is the result of extensive research, multiple independent critiques, stress tests, and refinements. The design is now stable; all subsequent work is implementation according to the Phase 0 build manual.

---

## 1. System Overview

The Fabian OS is a founder-scale data and intelligence platform that automatically captures information from multiple sources, stores it in a layered data platform, orchestrates workflows and agents, and provides a unified dashboard. It is built with strict phase gates, canonical data contracts, and built-in governance to prevent technical debt and operational failure.

**Core Principles:**

- **Layered Data Platform:** Raw → Canonical → Event Log.
- **System Role Separation:** Data, Automation, Research, External, Interface, Control layers.
- **Minimum Viable Architecture (MVA):** Start with a core set of proven tools; add only when proven necessary.
- **Hard Phase Gates:** Do not advance until measurable success criteria are met.
- **Canonical Data Contracts:** All workflows produce standardised objects; schemas versioned in a registry.
- **Health Monitoring:** Every component reports status; the system knows when it is broken.
- **Failure Design:** Every workflow defines retries, error paths, logging, and alerts.

---

## 2. System Role Separation

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| Control Layer | GitHub, Docs, Migrations, Schema Registry, Staging/Prod environments | Governance, version control, change management, rollback, schema validation, environment separation |
| Data Platform | PostgreSQL + pgvector | Stores all data in three sub-layers: Raw, Canonical, Event Log |
| – Raw Layer | `raw_*` tables | Immutable source data exactly as received (emails, files, agent outputs) |
| – Canonical Layer | `canonical_*` tables | Normalised business objects (deal, contact, idea, metric, task, product, agent_finding) |
| – Event Log | `event_log` table | Chronological record of all business events (DealCreated, IdeaAdded, etc.) |
| Automation Layer | n8n (self-hosted) | Orchestrates workflows, agents, integrations, scheduled jobs, error handling, health checks |
| Research Layer | Claude + Perplexity + NotebookLM | Human-facing synthesis, live research, document reasoning |
| External Systems | Zoho, Xero | Business operations (CRM, accounting, projects); integrated via API (never MCP for writes) |
| Interface Layer | Glance | Lightweight dashboard showing system health, business metrics, and alerts |

---

## 3. Data Platform Details

### 3.1 Raw Layer Tables (examples)

- `raw_emails` – Gmail and Outlook messages
- `raw_drive_files` – Google Drive file metadata
- `raw_agent_output` – Raw responses from Perplexity, etc.

All raw tables preserve original data for later reprocessing.

### 3.2 Canonical Layer Tables

- `canonical_deal`
- `canonical_contact`
- `canonical_idea`
- `canonical_agent_finding`
- `canonical_metric`
- `canonical_task`
- `canonical_product`

Each table uses `UUID PRIMARY KEY DEFAULT gen_random_uuid()` (with pgcrypto extension) and includes `source_system`, `external_id`, `metadata` fields to maintain traceability.

### 3.3 Event Log Table

```sql
CREATE TABLE event_log (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id UUID,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    source TEXT,
    metadata JSONB
);
```

Every workflow that creates or updates a canonical object must insert a corresponding event.

### 3.4 Health Checks Table

```sql
CREATE TABLE health_checks (
    component TEXT PRIMARY KEY,
    last_run TIMESTAMPTZ,
    status TEXT,
    message TEXT,
    metadata JSONB
);
```

- `component` uniquely identifies a monitored component (e.g., `gmail_capture`, `competitor_agent`).
- Used by the `/health-summary` endpoint to display system health in Glance.

---

## 4. Control Layer

- **GitHub Repository:** `fabian-os-config` stores all configuration (n8n exports, Glance YAML, capture scripts, schemas, migrations, documentation).
- **Schema Registry:** JSON Schema files for each canonical object, versioned in the repo.
- **Migrations:** Versioned SQL files in `migrations/`; applied to staging first, then production.
- **Staging Environment:** Separate database (`fabian_os_dev`) and n8n workspace; all changes tested in dev before production.
- **Change Management:** Google Doc proposal → automated impact analysis → approval → PR → merge → deploy.
- **Workflow Ownership:** Every n8n workflow has a named owner documented in `workflow_owners.md`.
- **Documentation:** `README.md`, `restore_procedure.md`, and runbooks.

---

## 5. Automation Layer (n8n)

- Self-hosted with PostgreSQL backend.
- Production rules for every workflow: timeout, retry, error path, logging, idempotency, owner.
- Health endpoints:
  - `/healthz/readiness` – n8n service health (used by Docker).
  - `/health-summary` – custom webhook that queries `health_checks` table and returns system status for Glance.
- Alerting: Scheduled workflow checks for non-ok status and sends email/Slack.

---

## 6. Research Layer

- **Claude:** Used for synthesis, classification, and structured output generation (via API).
- **Perplexity:** Used for live web research (competitor intelligence, regulatory updates, etc.).
- **NotebookLM:** Human-facing research workspace; all data uploaded manually or via Google Drive sync. Never automated reads/writes.

---

## 7. Interface Layer (Glance)

- Self-hosted lightweight dashboard.
- Widgets:
  - System health (from `/health-summary`)
  - Business snapshot (cash, deals, pipeline from `canonical_metric`)
  - Recent events (RSS from `event_log`)
- Configuration stored in GitHub and versioned.

---

## 8. External Systems Integration

- **Zoho:** CRM, Books, Projects – integrated via n8n using official APIs (not MCP for writes).
- **Xero:** Accounting – integrated via n8n using official APIs; MCP allowed only for conversational queries (e.g., Claude asking for balance).
- **Rule:** All operational writes go through n8n + API; MCP is strictly for assistant-style access.

---

## 9. Phase Overview (0–7)

| Phase | Objective | Key Tools | Success Gate |
|-------|-----------|-----------|-------------|
| 0 | Core foundation | PostgreSQL, n8n, NotebookLM, Glance, capture scripts | 7 days stable capture + 2 workflows + canonical objects defined + raw/canonical/event tables exist |
| 1 | Business OS | n8n, Zoho, Xero | 14 days stable workflows + trusted metrics + canonical objects populated |
| 2 | Agent POC | n8n, Perplexity, Claude | 30 days useful output + agent logs in canonical format |
| 3 | Ideation to MVP | n8n, Perplexity, Claude, Postgres | 1 software MVP + 1 hardware record + ideas stored canonically |
| 4 | Governance | n8n compliance, GitHub, change mgmt | 4 weeks compliance runs + DR test + control layer active |
| 5 | Advanced intelligence | MemCP, claude-brain, Ghost, seekdb (if needed) | 3 months stable core + proven need |
| 6 | Agent swarm | Multiple agents | 3 agents operational + each proven for 30 days |
| 7 | Team scaling | Multi-user tools | Brother onboarded successfully + shared memory works |

---

## 10. Operational Philosophy

- Build only what produces value.
- Every phase must prove usefulness before expansion.
- Avoid tool proliferation – MVA is sacred.
- Prefer stable, productised tools over experimental ones.
- Complexity must grow slowly.
- If it's not documented, it doesn't exist.
- If it doesn't provide value, it gets deleted.
- Health monitoring is not optional – the system must know when it is broken.
- Staging environment protects production.
- Credential expiry, API rate limits, and schema drift are actively monitored.

---

## 11. Final Implementation Notes

- PostgreSQL must include pgcrypto extension for reliable UUID generation.
- Gmail incremental sync uses `users.history.list` with a fallback to date-based resync when historyId expires.
- Health checks table enforces unique component constraint.
- n8n health endpoint for system status is separate from n8n's own readiness probe.

All other implementation details are contained in the Phase 0 build manual (separate document). This architecture document serves as the master reference.

---

## 12. Conclusion

The Fabian Operating System is now fully designed and hardened. It is a disciplined, layered platform that will capture and compound your business and personal knowledge over time. The architecture is locked; the next step is execution of Phase 0 according to the build manual.

Proceed to Phase 0.
