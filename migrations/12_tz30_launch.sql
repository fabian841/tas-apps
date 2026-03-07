-- Phase 7: TZ30 Launch & Agent Swarm
-- TZ30 launch tracking, subscription management, tech scouting, agent orchestration.

-- ═══════════════════════════════════════════════════════
-- TZ30 Launch Tracker
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS tz30_launch_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    milestone_name TEXT NOT NULL,
    category TEXT NOT NULL,                 -- 'design', 'manufacturing', 'compliance', 'marketing', 'sales', 'distribution'
    owner TEXT,                             -- 'fabian', 'joel', 'sam', 'tynan', 'ankuai'
    target_date DATE NOT NULL,
    completed_date DATE,
    status TEXT DEFAULT 'pending',          -- 'pending', 'in_progress', 'completed', 'blocked', 'at_risk'
    blocker TEXT,
    dependencies TEXT[],                   -- other milestone names this depends on
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════
-- TZ30 Subscription Management
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS tz30_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_zoho_id TEXT NOT NULL,
    contact_zoho_id TEXT,
    serial_number TEXT NOT NULL,
    plan_type TEXT NOT NULL,                -- 'weekly', 'monthly', 'annual'
    weekly_rate NUMERIC(10,2) NOT NULL,     -- $65-$125 per week
    billing_start DATE NOT NULL,
    billing_end DATE,
    status TEXT DEFAULT 'active',           -- 'trial', 'active', 'paused', 'cancelled', 'overdue'
    hardware_delivered BOOLEAN DEFAULT FALSE,
    hardware_delivery_date DATE,
    invoice_zoho_id TEXT,
    mrr NUMERIC(10,2),                     -- monthly recurring revenue
    churn_risk TEXT DEFAULT 'low',          -- 'low', 'medium', 'high'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Tech Scout Findings
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS tech_scout (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technology_name TEXT NOT NULL,
    category TEXT NOT NULL,                 -- 'iot_sensors', 'battery', 'materials', 'software', 'ai', 'manufacturing'
    source TEXT,                            -- URL or publication
    summary TEXT NOT NULL,
    relevance_to_tas TEXT,                  -- how it could benefit TAS products/ops
    relevance_score INTEGER CHECK (relevance_score BETWEEN 0 AND 100),
    maturity TEXT,                          -- 'research', 'prototype', 'commercial', 'mature'
    potential_impact TEXT,                  -- 'cost_reduction', 'new_capability', 'competitive_advantage'
    status TEXT DEFAULT 'PROPOSED',         -- PROPOSED -> CONFIRMED -> INVESTIGATING -> ADOPTED/DISMISSED
    agent_session_id UUID REFERENCES agent_sessions(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Agent Swarm Orchestration
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS agent_swarm_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    swarm_name TEXT NOT NULL,               -- 'morning_intelligence', 'weekly_review', 'tz30_launch_check'
    task_order INTEGER NOT NULL,
    agent_context TEXT NOT NULL,            -- 'personal', 'company'
    task_description TEXT NOT NULL,
    depends_on UUID[],                     -- other swarm task IDs this depends on
    input_from TEXT,                        -- 'previous_task', 'database', 'external_api'
    output_to TEXT,                         -- 'database', 'next_task', 'notification'
    timeout_seconds INTEGER DEFAULT 300,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 2,
    status TEXT DEFAULT 'pending',          -- 'pending', 'running', 'completed', 'failed', 'skipped'
    last_run_at TIMESTAMPTZ,
    last_session_id UUID REFERENCES agent_sessions(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Indexes
-- ═══════════════════════════════════════════════════════

CREATE INDEX idx_tz30_milestones_status ON tz30_launch_milestones(status);
CREATE INDEX idx_tz30_milestones_target ON tz30_launch_milestones(target_date);
CREATE INDEX idx_tz30_subs_account ON tz30_subscriptions(account_zoho_id);
CREATE INDEX idx_tz30_subs_status ON tz30_subscriptions(status);
CREATE INDEX idx_tz30_subs_churn ON tz30_subscriptions(churn_risk);
CREATE INDEX idx_tech_scout_category ON tech_scout(category);
CREATE INDEX idx_tech_scout_status ON tech_scout(status);
CREATE INDEX idx_tech_scout_relevance ON tech_scout(relevance_score);
CREATE INDEX idx_swarm_tasks_swarm ON agent_swarm_tasks(swarm_name);
CREATE INDEX idx_swarm_tasks_status ON agent_swarm_tasks(status);

-- ═══════════════════════════════════════════════════════
-- Permissions
-- ═══════════════════════════════════════════════════════

GRANT SELECT, INSERT, UPDATE ON tz30_launch_milestones TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON tz30_subscriptions TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON tech_scout TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON agent_swarm_tasks TO fabian_app;

-- ═══════════════════════════════════════════════════════
-- Seed TZ30 Launch Milestones (Target: Oct 2026)
-- ═══════════════════════════════════════════════════════

INSERT INTO tz30_launch_milestones (milestone_name, category, owner, target_date, status) VALUES
('TZ30 final design sign-off', 'design', 'fabian', '2026-04-30', 'pending'),
('Ankuai prototype delivery', 'manufacturing', 'fabian', '2026-05-31', 'pending'),
('AS/NZS 3845.2 compliance testing', 'compliance', 'joel', '2026-06-30', 'pending'),
('TASTrack IoT integration complete', 'design', 'sam', '2026-06-30', 'pending'),
('Subscription billing in Zoho', 'sales', 'joel', '2026-07-31', 'pending'),
('Marketing collateral ready', 'marketing', 'fabian', '2026-08-31', 'pending'),
('Pilot program (5 units)', 'sales', 'fabian', '2026-09-15', 'pending'),
('Full production order placed', 'manufacturing', 'fabian', '2026-09-01', 'pending'),
('TZ30 official launch', 'sales', 'fabian', '2026-10-01', 'pending'),
('First 50 subscriptions target', 'sales', 'fabian', '2026-12-31', 'pending');

-- ═══════════════════════════════════════════════════════
-- Seed Agent Swarm: Morning Intelligence
-- ═══════════════════════════════════════════════════════

INSERT INTO agent_swarm_tasks (swarm_name, task_order, agent_context, task_description, input_from, output_to, timeout_seconds) VALUES
('morning_intelligence', 1, 'company', 'Check overnight Zoho activity: new deals, tickets, invoices', 'database', 'next_task', 120),
('morning_intelligence', 2, 'company', 'Score any new or changed deals using deal_score model', 'previous_task', 'database', 180),
('morning_intelligence', 3, 'company', 'Check Xero cash position and flag if below $50K AUD', 'database', 'next_task', 60),
('morning_intelligence', 4, 'personal', 'Review overnight emails and extract commitments/decisions', 'database', 'database', 180),
('morning_intelligence', 5, 'personal', 'Generate morning brief combining company + personal insights', 'previous_task', 'notification', 120);
