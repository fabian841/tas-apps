-- Migration 003: Canonical Layer Tables
-- Normalised business objects. All tables share standard traceability columns:
--   id, source_system, external_id, metadata, created_at, updated_at

-- Helper: auto-update updated_at on row modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- canonical_deal – Sales opportunities and business deals
-- =============================================================================
CREATE TABLE IF NOT EXISTS canonical_deal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'lead',
    status TEXT NOT NULL DEFAULT 'open',
    value_amount NUMERIC(15, 2),
    value_currency TEXT DEFAULT 'AUD',
    contact_id UUID,
    company_name TEXT,
    description TEXT,
    expected_close_date DATE,
    actual_close_date DATE,
    probability INTEGER CHECK (probability >= 0 AND probability <= 100),
    tags TEXT[],
    source_system TEXT NOT NULL,
    external_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_canonical_deal_stage ON canonical_deal(stage);
CREATE INDEX idx_canonical_deal_status ON canonical_deal(status);
CREATE INDEX idx_canonical_deal_contact ON canonical_deal(contact_id);
CREATE INDEX idx_canonical_deal_external ON canonical_deal(source_system, external_id);

CREATE TRIGGER trg_canonical_deal_updated
    BEFORE UPDATE ON canonical_deal
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- canonical_contact – People and organisations
-- =============================================================================
CREATE TABLE IF NOT EXISTS canonical_contact (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT,
    last_name TEXT,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    company_name TEXT,
    job_title TEXT,
    contact_type TEXT DEFAULT 'person',
    tags TEXT[],
    notes TEXT,
    source_system TEXT NOT NULL,
    external_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_canonical_contact_email ON canonical_contact(email);
CREATE INDEX idx_canonical_contact_company ON canonical_contact(company_name);
CREATE INDEX idx_canonical_contact_external ON canonical_contact(source_system, external_id);

CREATE TRIGGER trg_canonical_contact_updated
    BEFORE UPDATE ON canonical_contact
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- canonical_idea – Business ideas, product concepts, opportunities
-- =============================================================================
CREATE TABLE IF NOT EXISTS canonical_idea (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    status TEXT NOT NULL DEFAULT 'captured',
    priority TEXT DEFAULT 'medium',
    feasibility_score INTEGER CHECK (feasibility_score >= 0 AND feasibility_score <= 10),
    impact_score INTEGER CHECK (impact_score >= 0 AND impact_score <= 10),
    tags TEXT[],
    related_ideas UUID[],
    source_system TEXT NOT NULL,
    external_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_canonical_idea_status ON canonical_idea(status);
CREATE INDEX idx_canonical_idea_category ON canonical_idea(category);
CREATE INDEX idx_canonical_idea_external ON canonical_idea(source_system, external_id);

CREATE TRIGGER trg_canonical_idea_updated
    BEFORE UPDATE ON canonical_idea
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- canonical_agent_finding – Structured output from AI research agents
-- =============================================================================
CREATE TABLE IF NOT EXISTS canonical_agent_finding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    finding_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    detail TEXT,
    confidence NUMERIC(3, 2) CHECK (confidence >= 0 AND confidence <= 1),
    relevance_score INTEGER CHECK (relevance_score >= 0 AND relevance_score <= 10),
    action_required BOOLEAN DEFAULT FALSE,
    tags TEXT[],
    raw_output_id UUID,
    source_system TEXT NOT NULL,
    external_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_canonical_agent_finding_agent ON canonical_agent_finding(agent_name);
CREATE INDEX idx_canonical_agent_finding_type ON canonical_agent_finding(finding_type);
CREATE INDEX idx_canonical_agent_finding_action ON canonical_agent_finding(action_required);
CREATE INDEX idx_canonical_agent_finding_external ON canonical_agent_finding(source_system, external_id);

CREATE TRIGGER trg_canonical_agent_finding_updated
    BEFORE UPDATE ON canonical_agent_finding
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- canonical_metric – Business KPIs and measurements
-- =============================================================================
CREATE TABLE IF NOT EXISTS canonical_metric (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name TEXT NOT NULL,
    metric_category TEXT NOT NULL,
    value_numeric NUMERIC(15, 4),
    value_text TEXT,
    unit TEXT,
    period_start DATE,
    period_end DATE,
    measured_at TIMESTAMPTZ DEFAULT NOW(),
    tags TEXT[],
    source_system TEXT NOT NULL,
    external_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_canonical_metric_name ON canonical_metric(metric_name);
CREATE INDEX idx_canonical_metric_category ON canonical_metric(metric_category);
CREATE INDEX idx_canonical_metric_measured ON canonical_metric(measured_at);
CREATE INDEX idx_canonical_metric_external ON canonical_metric(source_system, external_id);

CREATE TRIGGER trg_canonical_metric_updated
    BEFORE UPDATE ON canonical_metric
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- canonical_task – Actionable work items
-- =============================================================================
CREATE TABLE IF NOT EXISTS canonical_task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'todo',
    priority TEXT DEFAULT 'medium',
    assignee TEXT,
    due_date DATE,
    completed_at TIMESTAMPTZ,
    project TEXT,
    parent_task_id UUID,
    tags TEXT[],
    source_system TEXT NOT NULL,
    external_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_canonical_task_status ON canonical_task(status);
CREATE INDEX idx_canonical_task_priority ON canonical_task(priority);
CREATE INDEX idx_canonical_task_assignee ON canonical_task(assignee);
CREATE INDEX idx_canonical_task_due ON canonical_task(due_date);
CREATE INDEX idx_canonical_task_external ON canonical_task(source_system, external_id);

CREATE TRIGGER trg_canonical_task_updated
    BEFORE UPDATE ON canonical_task
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- canonical_product – Products, services, and offerings
-- =============================================================================
CREATE TABLE IF NOT EXISTS canonical_product (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    product_type TEXT NOT NULL DEFAULT 'software',
    status TEXT NOT NULL DEFAULT 'concept',
    version TEXT,
    price_amount NUMERIC(15, 2),
    price_currency TEXT DEFAULT 'AUD',
    category TEXT,
    tags TEXT[],
    source_system TEXT NOT NULL,
    external_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_canonical_product_type ON canonical_product(product_type);
CREATE INDEX idx_canonical_product_status ON canonical_product(status);
CREATE INDEX idx_canonical_product_external ON canonical_product(source_system, external_id);

CREATE TRIGGER trg_canonical_product_updated
    BEFORE UPDATE ON canonical_product
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
