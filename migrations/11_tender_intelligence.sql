-- Phase 6: Tender Intelligence & Supplier Risk
-- Government tender monitoring, bid tracking, supplier risk scoring.

-- ═══════════════════════════════════════════════════════
-- Tender Pipeline
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS tenders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,                   -- 'austender', 'tenders.nsw.gov.au', 'manual', 'agent'
    external_id TEXT,                       -- tender reference number from source
    title TEXT NOT NULL,
    description TEXT,
    issuing_authority TEXT NOT NULL,        -- e.g. 'Transport for NSW', 'VicRoads'
    jurisdiction TEXT,                      -- 'NSW', 'VIC', 'Federal', etc.
    category TEXT,                          -- 'traffic_management', 'road_works', 'events', 'infrastructure'
    estimated_value NUMERIC(15,2),
    currency TEXT DEFAULT 'AUD',
    open_date DATE,
    close_date DATE,
    decision_date DATE,
    relevance_score INTEGER CHECK (relevance_score BETWEEN 0 AND 100),
    fit_analysis TEXT,                     -- why this tender is relevant to TAS
    status TEXT DEFAULT 'identified',      -- 'identified', 'evaluating', 'bidding', 'submitted', 'won', 'lost', 'withdrawn', 'expired'
    bid_decision TEXT,                     -- 'bid', 'no_bid', 'pending'
    bid_amount NUMERIC(15,2),
    bid_submitted_at TIMESTAMPTZ,
    outcome TEXT,
    detected_by TEXT DEFAULT 'agent',
    agent_session_id UUID REFERENCES agent_sessions(id),
    deal_zoho_id TEXT,                     -- link to Zoho deal if created
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(source, external_id)
);

-- ═══════════════════════════════════════════════════════
-- Supplier Risk Assessment
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS supplier_risk (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_name TEXT NOT NULL,            -- from config_suppliers
    assessed_at TIMESTAMPTZ DEFAULT NOW(),
    overall_risk TEXT DEFAULT 'low',        -- 'low', 'medium', 'high', 'critical'
    risk_factors JSONB NOT NULL,           -- { "delivery_reliability": 85, "financial_stability": 70, "single_source": true, ... }
    lead_time_days INTEGER,
    quality_score NUMERIC(5,2),            -- 0-100
    on_time_delivery_pct NUMERIC(5,2),     -- percentage
    open_issues INTEGER DEFAULT 0,
    last_order_date DATE,
    next_review_date DATE,
    mitigation_plan TEXT,
    status TEXT DEFAULT 'PROPOSED',
    agent_session_id UUID REFERENCES agent_sessions(id),
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Bid Score Card (for evaluating whether to bid on a tender)
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS bid_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id),
    evaluated_at TIMESTAMPTZ DEFAULT NOW(),
    criteria JSONB NOT NULL,               -- { "capability_match": 90, "capacity": 70, "margin_estimate": 25, "strategic_fit": 80 }
    go_no_go_score INTEGER CHECK (go_no_go_score BETWEEN 0 AND 100),
    recommendation TEXT,                   -- 'bid', 'no_bid', 'conditional'
    conditions TEXT,                       -- conditions for a conditional bid
    status TEXT DEFAULT 'PROPOSED',
    reviewed_by TEXT,
    agent_session_id UUID REFERENCES agent_sessions(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════
-- Indexes
-- ═══════════════════════════════════════════════════════

CREATE INDEX idx_tenders_source ON tenders(source);
CREATE INDEX idx_tenders_status ON tenders(status);
CREATE INDEX idx_tenders_close ON tenders(close_date);
CREATE INDEX idx_tenders_jurisdiction ON tenders(jurisdiction);
CREATE INDEX idx_tenders_relevance ON tenders(relevance_score);
CREATE INDEX idx_supplier_risk_name ON supplier_risk(supplier_name);
CREATE INDEX idx_supplier_risk_level ON supplier_risk(overall_risk);
CREATE INDEX idx_bid_eval_tender ON bid_evaluations(tender_id);

-- ═══════════════════════════════════════════════════════
-- Permissions
-- ═══════════════════════════════════════════════════════

GRANT SELECT, INSERT, UPDATE ON tenders TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON supplier_risk TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON bid_evaluations TO fabian_app;
