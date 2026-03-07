# ADR-001: Zoho as Source of Truth + PostgreSQL as Intelligence Layer

**Status:** Accepted
**Date:** 2026-03-07
**Decision Makers:** Fabian Diaz (Director), Claude (Code Builder)

## Context

Two architecture documents govern the TAS Operating System:

1. **Fabian OS Build Manuals (Phases 0-7)** — Define a PostgreSQL/n8n/Glance intelligence layer with 8 PIL registers, canonical tables, confidence gating, PLAUD extraction, and Claude Code agents.

2. **TAS-001.3 — TAS Operating System Foundation Architecture** — Defines Zoho One as the source of truth for all TAS business operations (CRM, Desk, Inventory, Books, Projects), with Joel supervising Zoho configuration and Claude building code.

These appeared to conflict: the build manuals assume PostgreSQL as the primary data store, while TAS-001.3 positions Zoho as authoritative.

## Decision

**Both systems coexist and integrate.** Specifically:

- **Zoho One** is the source of truth for all TAS business operations (contacts, accounts, deals, tickets, invoices, inventory, projects).
- **PostgreSQL** (this repo) is the intelligence and automation layer — it mirrors Zoho data every 4 hours into `zoho_*` tables, normalizes into `canonical_*` tables, and adds PIL registers, confidence gating, agent findings, and analytics that Zoho cannot provide.
- **n8n** orchestrates all workflows: Zoho sync, PLAUD processing, email classification, agent triggers, scorecard generation, and dashboard webhooks.
- **Glance** surfaces intelligence via 7 dashboard pages (touchpoints).
- **Claude Code agents** connect to both systems via MCP servers — reading from PostgreSQL for intelligence queries, and from Zoho directly for real-time CRM/Desk/Books operations.

## Data Flow

```
Zoho One (Source of Truth)
    │
    ├─── Zoho Sync (every 4h) ───► zoho_* tables (PostgreSQL mirror)
    │                                    │
    │                                    ├─► canonical_* tables (normalized)
    │                                    ├─► PIL registers (personal layer)
    │                                    └─► agent_findings (intelligence)
    │
    ├─── Zoho MCP (real-time) ──► Claude Code agents (read/write)
    │
    └─── Zoho Flow ─────────────► Zoho automations (Joel configures)

External Sources
    ├─── Xero ──────► canonical_metric (daily 6 AM)
    ├─── Gmail/M365 ► raw_emails (hourly)
    ├─── PLAUD ─────► raw_transcripts → PIL registers
    └─── Perplexity ► agent_findings (competitor intel)
```

## Hard Boundaries

1. **Personal vs Company data isolation** — PIL registers and personal agent context never mix with company data.
2. **Daily Flash queries Company tables only** — No personal data on company dashboards.
3. **All AI outputs are PROPOSED** — Only Fabian confirms. Confidence gating applies to both PIL and agent findings.
4. **Zoho writes require authorization** — Claude agents can read freely but write operations (deal stage updates, notes, tickets) are logged and gated.

## Consequences

**Positive:**
- Zoho serves as the business-grade source of truth with Joel's oversight
- PostgreSQL adds intelligence capabilities Zoho lacks (vector search, PIL, confidence gating, agent framework)
- No data loss — Zoho data is mirrored, not replaced
- Claude agents get the best of both worlds via MCP

**Negative:**
- Data exists in two places (Zoho + PostgreSQL mirror) — sync lag of up to 4 hours
- Additional complexity in maintaining sync workflows
- Credential management for both Zoho API and PostgreSQL

**Mitigations:**
- Zoho MCP servers provide real-time access when needed (bypasses sync lag)
- Health checks monitor sync status and alert on failures
- Event log provides audit trail for all sync operations

## Alternatives Considered

1. **PostgreSQL only (no Zoho)** — Rejected. TAS already uses Zoho for CRM, Desk, Books. Replacing it would lose Joel's expertise and existing business processes.
2. **Zoho only (no PostgreSQL)** — Rejected. Zoho cannot provide vector search, PIL registers, confidence gating, or the custom intelligence layer the build manuals define.
3. **Real-time sync (not batch)** — Deferred. Batch sync every 4 hours is sufficient for current operations. Real-time can be added via Zoho Flow webhooks if needed.
