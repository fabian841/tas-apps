-- Phase 0 Reconciliation: Canonical Tables
-- These are the universal data model from the original Fabian OS architecture.
-- All source systems (Zoho, Xero, agents) normalize into these tables.
-- The zoho_* mirror tables (migration 06) feed INTO these via sync workflows.

-- ═══════════════════════════════════════════════════════
-- Canonical Deal
-- ═══════════════════════════════════════════════════════

CREATE TABLE canonical_deal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system TEXT NOT NULL,          -- 'zoho_crm', 'manual', 'agent'
    external_id TEXT,
    name TEXT NOT NULL,
    stage TEXT,
    value NUMERIC,
    currency TEXT DEFAULT 'AUD',
    owner TEXT,
    account_name TEXT,
    contact_name TEXT,
    closing_date DATE,
    probability INTEGER,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(source_system, external_id)
);

-- ═══════════════════════════════════════════════════════
-- Canonical Contact
-- ═══════════════════════════════════════════════════════

CREATE TABLE canonical_contact (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system TEXT NOT NULL,          -- 'zoho_crm', 'manual'
    external_id TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    company TEXT,
    title TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(source_system, external_id)
);

-- ═══════════════════════════════════════════════════════
-- Canonical Idea
-- ═══════════════════════════════════════════════════════

CREATE TABLE canonical_idea (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'unknown',     -- 'software', 'hardware', 'service', 'other', 'unknown'
    status TEXT DEFAULT 'new',           -- 'new', 'researched', 'mvp_ready', 'product_created', 'archived'
    feasibility_score INTEGER,           -- 1-10 from research
    feasibility_summary TEXT,
    market_size TEXT,
    competitor_count INTEGER,
    recommended_category TEXT,
    mvp_link TEXT,
    source TEXT,                          -- 'plaud', 'form', 'email', 'manual'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Canonical Agent Finding
-- ═══════════════════════════════════════════════════════

CREATE TABLE canonical_agent_finding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,            -- 'competitor_intel', 'regulatory_monitor', etc.
    source TEXT,                          -- 'perplexity', 'arxiv', 'news_api'
    title TEXT,
    summary TEXT,
    raw_data JSONB,
    relevance_score INTEGER,             -- 1-10
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Canonical Metric
-- ═══════════════════════════════════════════════════════

CREATE TABLE canonical_metric (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name TEXT NOT NULL,           -- 'cash_balance', 'pipeline_total', 'deals_count', 'receivables', 'payables'
    value NUMERIC NOT NULL,
    unit TEXT DEFAULT 'AUD',
    source TEXT,                          -- 'xero', 'zoho', 'manual', 'computed'
    period_start DATE,
    period_end DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Canonical Task
-- ═══════════════════════════════════════════════════════

CREATE TABLE canonical_task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system TEXT,                  -- 'zoho_projects', 'manual', 'agent'
    external_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'open',          -- 'open', 'in_progress', 'completed', 'cancelled'
    priority TEXT DEFAULT 'medium',      -- 'low', 'medium', 'high', 'urgent'
    assignee TEXT,
    due_date DATE,
    completed_at TIMESTAMPTZ,
    rock_quarter TEXT,                   -- links to Rockefeller Habits rocks if applicable
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    metadata JSONB,
    UNIQUE(source_system, external_id)
);

-- ═══════════════════════════════════════════════════════
-- Canonical Product
-- ═══════════════════════════════════════════════════════

CREATE TABLE canonical_product (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system TEXT,                  -- 'zoho_crm', 'manual'
    external_id TEXT,
    name TEXT NOT NULL,
    category TEXT,                       -- 'hardware', 'software', 'service'
    stage TEXT DEFAULT 'concept',        -- 'concept', 'sample', 'testing', 'production', 'launch'
    idea_id UUID REFERENCES canonical_idea(id),
    bom TEXT,                            -- bill of materials
    manufacturer TEXT,
    target_launch_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    metadata JSONB,
    UNIQUE(source_system, external_id)
);

-- ═══════════════════════════════════════════════════════
-- Workflow Logs (for production rules compliance)
-- ═══════════════════════════════════════════════════════

CREATE TABLE workflow_logs (
    id BIGSERIAL PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    run_id TEXT,
    status TEXT NOT NULL,                -- 'started', 'completed', 'error'
    input_summary TEXT,
    output_summary TEXT,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Config Tables (for agents and monitoring)
-- ═══════════════════════════════════════════════════════

CREATE TABLE config_competitors (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    website TEXT,
    description TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- ═══════════════════════════════════════════════════════
-- Indexes
-- ═══════════════════════════════════════════════════════

CREATE INDEX idx_canonical_deal_source ON canonical_deal(source_system);
CREATE INDEX idx_canonical_deal_stage ON canonical_deal(stage);
CREATE INDEX idx_canonical_deal_closing ON canonical_deal(closing_date);
CREATE INDEX idx_canonical_contact_source ON canonical_contact(source_system);
CREATE INDEX idx_canonical_contact_email ON canonical_contact(email);
CREATE INDEX idx_canonical_idea_status ON canonical_idea(status);
CREATE INDEX idx_canonical_agent_finding_agent ON canonical_agent_finding(agent_name);
CREATE INDEX idx_canonical_agent_finding_created ON canonical_agent_finding(created_at);
CREATE INDEX idx_canonical_metric_name ON canonical_metric(metric_name);
CREATE INDEX idx_canonical_metric_created ON canonical_metric(created_at);
CREATE INDEX idx_canonical_task_status ON canonical_task(status);
CREATE INDEX idx_canonical_task_assignee ON canonical_task(assignee);
CREATE INDEX idx_canonical_product_stage ON canonical_product(stage);
CREATE INDEX idx_workflow_logs_name ON workflow_logs(workflow_name);
CREATE INDEX idx_workflow_logs_status ON workflow_logs(status);
CREATE INDEX idx_workflow_logs_started ON workflow_logs(started_at);

-- ═══════════════════════════════════════════════════════
-- Permissions
-- ═══════════════════════════════════════════════════════

GRANT SELECT, INSERT, UPDATE, DELETE ON canonical_deal TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON canonical_contact TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON canonical_idea TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON canonical_agent_finding TO fabian_app;
GRANT SELECT, INSERT ON canonical_metric TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON canonical_task TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON canonical_product TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON workflow_logs TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON config_competitors TO fabian_app;
GRANT USAGE ON SEQUENCE workflow_logs_id_seq TO fabian_app;
GRANT USAGE ON SEQUENCE config_competitors_id_seq TO fabian_app;
