-- Phase 5: Compliance & Regulatory Monitoring
-- NSW TCAWS compliance tracking, regulatory change detection, audit trail.

-- ═══════════════════════════════════════════════════════
-- Regulatory Monitor
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS regulatory_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country TEXT NOT NULL DEFAULT 'AU',
    state_province TEXT,                    -- 'NSW', 'VIC', 'QLD', etc.
    regulation_name TEXT NOT NULL,          -- e.g. 'NSW TCAWS', 'AS/NZS 3845.2'
    change_type TEXT NOT NULL,              -- 'new', 'amendment', 'repeal', 'guidance_update'
    summary TEXT NOT NULL,
    impact_assessment TEXT,                 -- how it affects TAS operations
    impact_severity TEXT DEFAULT 'low',     -- 'low', 'medium', 'high', 'critical'
    affected_products TEXT[],              -- ['PB4000', 'MINIBOOM-TZ30']
    source_url TEXT,
    source_date DATE,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    detected_by TEXT DEFAULT 'agent',       -- 'agent', 'manual', 'joel'
    status TEXT DEFAULT 'PROPOSED',         -- PROPOSED -> CONFIRMED -> ACTIONED
    action_required TEXT,
    actioned_at TIMESTAMPTZ,
    agent_session_id UUID REFERENCES agent_sessions(id),
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Compliance Checklist per Product/Site
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS compliance_checklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checklist_name TEXT NOT NULL,           -- e.g. 'PB4000 NSW Deployment', 'TZ30 Pre-Launch'
    product_code TEXT,
    jurisdiction TEXT NOT NULL,             -- 'NSW', 'VIC', 'AU-National', etc.
    items JSONB NOT NULL,                  -- [{ "requirement": "...", "status": "pass|fail|na", "evidence": "..." }]
    overall_status TEXT DEFAULT 'pending',  -- 'pending', 'compliant', 'non_compliant', 'expired'
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    expires_at DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════
-- Certification Tracker
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,              -- 'product', 'person', 'company'
    entity_id TEXT NOT NULL,                -- product_code, employee name, ABN
    certification_name TEXT NOT NULL,       -- 'AS/NZS 3845.2', 'Traffic Controller Licence', etc.
    issuing_body TEXT NOT NULL,
    certificate_number TEXT,
    issued_date DATE NOT NULL,
    expiry_date DATE,
    status TEXT DEFAULT 'active',           -- 'active', 'expiring_30d', 'expired', 'revoked'
    renewal_reminder_sent BOOLEAN DEFAULT FALSE,
    document_path TEXT,                     -- path to scanned cert in Drive
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════
-- Indexes
-- ═══════════════════════════════════════════════════════

CREATE INDEX idx_reg_changes_country ON regulatory_changes(country, state_province);
CREATE INDEX idx_reg_changes_status ON regulatory_changes(status);
CREATE INDEX idx_reg_changes_severity ON regulatory_changes(impact_severity);
CREATE INDEX idx_compliance_product ON compliance_checklist(product_code);
CREATE INDEX idx_compliance_status ON compliance_checklist(overall_status);
CREATE INDEX idx_certs_entity ON certifications(entity_type, entity_id);
CREATE INDEX idx_certs_expiry ON certifications(expiry_date);
CREATE INDEX idx_certs_status ON certifications(status);

-- ═══════════════════════════════════════════════════════
-- Permissions
-- ═══════════════════════════════════════════════════════

GRANT SELECT, INSERT, UPDATE ON regulatory_changes TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON compliance_checklist TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON certifications TO fabian_app;
