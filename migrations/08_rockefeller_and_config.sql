-- Phase 1 Reconciliation: Rockefeller Habits + Configuration Tables
-- From original Fabian OS Phase 1 Build Manual.
-- Supports quarterly planning, weekly rocks, meeting agendas, and scorecards.

-- ═══════════════════════════════════════════════════════
-- Canonical Quarter (Rockefeller Habits)
-- ═══════════════════════════════════════════════════════

CREATE TABLE canonical_quarter (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,              -- 1..4
    name TEXT,                              -- e.g. 'Q2 2026 — TZ30 Launch Prep'
    start_date DATE,
    end_date DATE,
    status TEXT DEFAULT 'planning',         -- 'planning', 'active', 'review', 'closed'
    rocks JSONB,                            -- array of rock objects {name, owner, progress_pct, status}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    UNIQUE(year, quarter)
);

-- ═══════════════════════════════════════════════════════
-- Canonical Meeting
-- ═══════════════════════════════════════════════════════

CREATE TABLE canonical_meeting (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,                     -- 'weekly', 'monthly', 'quarterly'
    scheduled_date DATE NOT NULL,
    agenda TEXT,
    attendees TEXT[],
    notes TEXT,
    action_items JSONB,                     -- extracted actions from PLAUD if recorded
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- ═══════════════════════════════════════════════════════
-- Canonical Scorecard (Weekly KPIs)
-- ═══════════════════════════════════════════════════════

CREATE TABLE canonical_scorecard (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week DATE NOT NULL,                     -- Monday of the reporting week
    metric_name TEXT NOT NULL,
    value NUMERIC,
    target NUMERIC,
    variance NUMERIC,                       -- computed: value - target
    source TEXT,                            -- 'zoho_crm', 'zoho_books', 'xero', 'manual'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════
-- Compliance Reports (Phase 4 prep)
-- ═══════════════════════════════════════════════════════

CREATE TABLE compliance_reports (
    id SERIAL PRIMARY KEY,
    report_type TEXT NOT NULL,              -- 'weekly_compliance', 'data_quality', 'credential_expiry'
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    summary TEXT,
    details JSONB,
    status TEXT                             -- 'pass', 'warn', 'fail'
);

-- ═══════════════════════════════════════════════════════
-- Config: Suppliers (for supplier risk monitoring)
-- ═══════════════════════════════════════════════════════

CREATE TABLE config_suppliers (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    country TEXT,
    contact_name TEXT,
    contact_email TEXT,
    product_lines TEXT[],                   -- e.g. {'PB4000', 'MINIBOOM'}
    payment_terms TEXT,
    lead_time_days INTEGER,
    active BOOLEAN DEFAULT TRUE,
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Config: Regulatory Countries (for Phase 6 agent)
-- ═══════════════════════════════════════════════════════

CREATE TABLE config_regulatory_countries (
    id SERIAL PRIMARY KEY,
    country TEXT UNIQUE NOT NULL,
    source_urls TEXT[],                     -- RSS feeds, government portals
    keywords TEXT[],                        -- e.g. {'traffic management', 'portable barrier'}
    active BOOLEAN DEFAULT TRUE
);

-- ═══════════════════════════════════════════════════════
-- Config: Tender Sources (for Phase 6 agent)
-- ═══════════════════════════════════════════════════════

CREATE TABLE config_tender_sources (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,              -- 'AusTender', 'TED', 'grants.gov'
    country TEXT,
    url TEXT,
    feed_type TEXT,                         -- 'rss', 'api', 'scrape'
    keywords TEXT[],
    active BOOLEAN DEFAULT TRUE
);

-- ═══════════════════════════════════════════════════════
-- Seed: Key Suppliers
-- ═══════════════════════════════════════════════════════

INSERT INTO config_suppliers (name, country, contact_name, product_lines, payment_terms, active) VALUES
('Ankuai (Jack)', 'China', 'Jack', ARRAY['PB4000', 'MINIBOOM'], '30% deposit, 70% on shipment', true),
('Trafficon (Fiona)', 'Australia', 'Fiona', ARRAY['signage', 'accessories'], 'Net 30', true);

-- ═══════════════════════════════════════════════════════
-- Seed: Competitors (from TAS-001.3)
-- ═══════════════════════════════════════════════════════

INSERT INTO config_competitors (name, website, description, active) VALUES
('BARTCO', NULL, 'Competitor — portable traffic devices', true),
('ARROWES', NULL, 'Competitor — portable traffic devices', true),
('DATSA', NULL, 'Competitor — portable traffic devices', true);

-- ═══════════════════════════════════════════════════════
-- Seed: Regulatory Countries
-- ═══════════════════════════════════════════════════════

INSERT INTO config_regulatory_countries (country, keywords, active) VALUES
('Australia', ARRAY['traffic management', 'portable barrier', 'TCAWS', 'work zone'], true),
('United States', ARRAY['traffic management', 'work zone', 'MUTCD', 'portable barrier'], true),
('United Kingdom', ARRAY['traffic management', 'Chapter 8', 'portable barrier'], true);

-- ═══════════════════════════════════════════════════════
-- Indexes
-- ═══════════════════════════════════════════════════════

CREATE INDEX idx_canonical_quarter_year ON canonical_quarter(year, quarter);
CREATE INDEX idx_canonical_quarter_status ON canonical_quarter(status);
CREATE INDEX idx_canonical_meeting_date ON canonical_meeting(scheduled_date);
CREATE INDEX idx_canonical_meeting_type ON canonical_meeting(type);
CREATE INDEX idx_canonical_scorecard_week ON canonical_scorecard(week);
CREATE INDEX idx_canonical_scorecard_metric ON canonical_scorecard(metric_name);
CREATE INDEX idx_compliance_reports_type ON compliance_reports(report_type);

-- ═══════════════════════════════════════════════════════
-- Permissions
-- ═══════════════════════════════════════════════════════

GRANT SELECT, INSERT, UPDATE ON canonical_quarter TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON canonical_meeting TO fabian_app;
GRANT SELECT, INSERT ON canonical_scorecard TO fabian_app;
GRANT SELECT, INSERT ON compliance_reports TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON config_suppliers TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON config_regulatory_countries TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON config_tender_sources TO fabian_app;
GRANT USAGE ON SEQUENCE compliance_reports_id_seq TO fabian_app;
GRANT USAGE ON SEQUENCE config_suppliers_id_seq TO fabian_app;
GRANT USAGE ON SEQUENCE config_regulatory_countries_id_seq TO fabian_app;
GRANT USAGE ON SEQUENCE config_tender_sources_id_seq TO fabian_app;
