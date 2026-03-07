-- Phase 0: Canonical (normalised) tables
-- These tables store cleaned, deduplicated business objects.

CREATE TABLE canonical_deal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system TEXT,
    external_id TEXT,
    name TEXT,
    stage TEXT,
    value NUMERIC,
    currency TEXT,
    owner TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    metadata JSONB,
    UNIQUE(source_system, external_id)
);

CREATE TABLE canonical_contact (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system TEXT,
    external_id TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    company TEXT,
    role TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    metadata JSONB,
    UNIQUE(source_system, external_id)
);

CREATE TABLE canonical_idea (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    description TEXT,
    category TEXT,
    status TEXT DEFAULT 'new',
    feasibility_score INTEGER,
    feasibility_summary TEXT,
    market_size TEXT,
    competitor_count INTEGER,
    recommended_category TEXT,
    mvp_link TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    metadata JSONB
);

CREATE TABLE canonical_agent_finding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    source TEXT,
    title TEXT,
    summary TEXT,
    raw_data JSONB,
    relevance_score INTEGER,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE canonical_metric (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name TEXT NOT NULL,
    value NUMERIC,
    unit TEXT,
    period_start DATE,
    period_end DATE,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE canonical_task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system TEXT,
    external_id TEXT,
    title TEXT,
    description TEXT,
    assignee TEXT,
    status TEXT,
    priority TEXT,
    due_date DATE,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    metadata JSONB,
    UNIQUE(source_system, external_id)
);

CREATE TABLE canonical_product (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    sku TEXT,
    category TEXT,
    status TEXT,
    description TEXT,
    price NUMERIC,
    currency TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    metadata JSONB
);
