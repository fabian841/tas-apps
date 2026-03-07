-- Phase 4: Forecasting & Pipeline Intelligence
-- Revenue forecasting, deal scoring, pipeline velocity tracking.
-- Aligned with Rockefeller Habits: weekly/monthly/quarterly forecast rhythm.

-- ═══════════════════════════════════════════════════════
-- Pipeline Forecast
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pipeline_forecast (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    forecast_date DATE NOT NULL DEFAULT CURRENT_DATE,
    period_type TEXT NOT NULL,              -- 'weekly', 'monthly', 'quarterly'
    period_label TEXT NOT NULL,             -- e.g. 'W11-2026', 'Mar-2026', 'Q1-2026'
    pipeline_total NUMERIC(15,2),           -- total pipeline value
    weighted_pipeline NUMERIC(15,2),        -- sum(amount * probability/100) for open deals
    expected_close NUMERIC(15,2),           -- deals with closing_date in period
    won_to_date NUMERIC(15,2),             -- closed-won in period
    lost_to_date NUMERIC(15,2),            -- closed-lost in period
    deal_count INTEGER,
    avg_deal_size NUMERIC(15,2),
    avg_days_in_stage NUMERIC(8,1),
    conversion_rate NUMERIC(5,2),          -- won / (won + lost) * 100
    velocity_score NUMERIC(5,2),           -- custom pipeline velocity metric
    source TEXT DEFAULT 'auto',            -- 'auto' (from zoho_sync), 'manual', 'agent'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Deal Score (AI-assisted scoring for each deal)
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS deal_score (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_zoho_id TEXT NOT NULL,
    scored_at TIMESTAMPTZ DEFAULT NOW(),
    score INTEGER CHECK (score BETWEEN 0 AND 100),
    factors JSONB NOT NULL,                -- { "engagement": 70, "budget_confirmed": true, "decision_maker_met": false, ... }
    risk_flags TEXT[],                     -- ['stale_30_days', 'no_recent_activity', 'competitor_mentioned']
    recommendation TEXT,                   -- e.g. 'Follow up within 48h', 'Request site visit'
    status TEXT DEFAULT 'PROPOSED',        -- PROPOSED -> CONFIRMED/REJECTED
    agent_session_id UUID REFERENCES agent_sessions(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════
-- Revenue Target Tracking
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS revenue_target (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fiscal_year INTEGER NOT NULL,          -- e.g. 2026
    quarter INTEGER CHECK (quarter BETWEEN 1 AND 4),
    month INTEGER CHECK (month BETWEEN 1 AND 12),
    target_revenue NUMERIC(15,2) NOT NULL,
    target_units INTEGER,                  -- PB4000 units target
    product_mix JSONB,                     -- { "PB4000": 60, "TZ30": 30, "services": 10 } percentages
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fiscal_year, quarter, month)
);

-- ═══════════════════════════════════════════════════════
-- Indexes
-- ═══════════════════════════════════════════════════════

CREATE INDEX idx_forecast_date ON pipeline_forecast(forecast_date);
CREATE INDEX idx_forecast_period ON pipeline_forecast(period_type, period_label);
CREATE INDEX idx_deal_score_deal ON deal_score(deal_zoho_id);
CREATE INDEX idx_deal_score_scored ON deal_score(scored_at);
CREATE INDEX idx_deal_score_status ON deal_score(status);
CREATE INDEX idx_revenue_target_year ON revenue_target(fiscal_year);

-- ═══════════════════════════════════════════════════════
-- Permissions
-- ═══════════════════════════════════════════════════════

GRANT SELECT, INSERT, UPDATE ON pipeline_forecast TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON deal_score TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON revenue_target TO fabian_app;
