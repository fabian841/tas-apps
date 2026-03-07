-- Phase 2: Company OS (GPX) — Zoho canonical tables, warranty engine, PB4000 doctrine
-- Company layer data. Hard isolation boundary: no Personal layer data referenced here.

-- ═══════════════════════════════════════════════════════
-- Zoho CRM Canonical Tables
-- ═══════════════════════════════════════════════════════

CREATE TABLE zoho_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zoho_id TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    company TEXT,
    account_zoho_id TEXT,
    lead_source TEXT,
    owner_name TEXT,
    created_in_zoho TIMESTAMPTZ,
    modified_in_zoho TIMESTAMPTZ,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    raw_data JSONB
);

CREATE TABLE zoho_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zoho_id TEXT UNIQUE NOT NULL,
    account_name TEXT NOT NULL,
    industry TEXT,
    account_type TEXT,               -- 'Customer', 'Prospect', 'Distributor', 'Partner'
    billing_state TEXT,
    billing_country TEXT DEFAULT 'Australia',
    website TEXT,
    owner_name TEXT,
    annual_revenue NUMERIC(15,2),
    created_in_zoho TIMESTAMPTZ,
    modified_in_zoho TIMESTAMPTZ,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    raw_data JSONB
);

CREATE TABLE zoho_deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zoho_id TEXT UNIQUE NOT NULL,
    deal_name TEXT NOT NULL,
    stage TEXT NOT NULL,              -- 'Qualification', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'
    amount NUMERIC(15,2),
    currency TEXT DEFAULT 'AUD',
    closing_date DATE,
    account_zoho_id TEXT,
    contact_zoho_id TEXT,
    owner_name TEXT,
    probability INTEGER,
    pipeline TEXT,
    created_in_zoho TIMESTAMPTZ,
    modified_in_zoho TIMESTAMPTZ,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    raw_data JSONB
);

-- ═══════════════════════════════════════════════════════
-- Zoho Desk Canonical Tables
-- ═══════════════════════════════════════════════════════

CREATE TABLE zoho_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zoho_id TEXT UNIQUE NOT NULL,
    ticket_number TEXT,
    subject TEXT NOT NULL,
    status TEXT NOT NULL,             -- 'Open', 'On Hold', 'Escalated', 'Closed'
    priority TEXT,                    -- 'Low', 'Medium', 'High', 'Urgent'
    channel TEXT,                     -- 'Email', 'Phone', 'Web', 'Chat'
    contact_zoho_id TEXT,
    account_zoho_id TEXT,
    assigned_to TEXT,
    product_name TEXT,                -- e.g. 'PB4000', 'MINIBOOM TZ30', 'TASTrack'
    category TEXT,                    -- 'Warranty', 'Technical Support', 'Sales', 'General'
    resolution TEXT,
    due_date TIMESTAMPTZ,
    created_in_zoho TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    raw_data JSONB
);

-- ═══════════════════════════════════════════════════════
-- Zoho Books Canonical Tables
-- ═══════════════════════════════════════════════════════

CREATE TABLE zoho_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zoho_id TEXT UNIQUE NOT NULL,
    invoice_number TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    account_zoho_id TEXT,
    status TEXT NOT NULL,             -- 'Draft', 'Sent', 'Overdue', 'Paid', 'Void'
    total NUMERIC(15,2) NOT NULL,
    balance_due NUMERIC(15,2),
    currency TEXT DEFAULT 'AUD',
    invoice_date DATE NOT NULL,
    due_date DATE,
    paid_date DATE,
    line_items JSONB,                 -- array of {product, quantity, rate, amount}
    created_in_zoho TIMESTAMPTZ,
    modified_in_zoho TIMESTAMPTZ,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    raw_data JSONB
);

-- ═══════════════════════════════════════════════════════
-- PB4000 Product Doctrine
-- ═══════════════════════════════════════════════════════

CREATE TABLE product_doctrine (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_code TEXT NOT NULL,        -- 'PB4000', 'PB4000-TASTRACK', 'PB4000-TMA', 'MINIBOOM-TZ30'
    variant TEXT,                      -- 'basic', 'tastrack', 'tma', 'event', 'rapid'
    doctrine_version TEXT NOT NULL,    -- e.g. 'v1.0'
    specifications JSONB NOT NULL,     -- weight, arm_span, speed_rating, price_range, etc.
    compliance_requirements JSONB,     -- NSW TCAWS refs, certifications, etc.
    deployment_rules JSONB,            -- when to use, when NOT to use
    warranty_terms JSONB,              -- standard warranty duration, conditions
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(product_code, variant, doctrine_version)
);

-- ═══════════════════════════════════════════════════════
-- Warranty Engine
-- ═══════════════════════════════════════════════════════

CREATE TABLE warranty_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    serial_number TEXT UNIQUE NOT NULL,
    product_code TEXT NOT NULL,        -- 'PB4000', 'MINIBOOM-TZ30'
    variant TEXT,
    account_zoho_id TEXT,              -- links to zoho_accounts
    contact_zoho_id TEXT,              -- links to zoho_contacts
    purchase_date DATE NOT NULL,
    warranty_start DATE NOT NULL,
    warranty_end DATE NOT NULL,
    warranty_type TEXT DEFAULT 'standard',  -- 'standard', 'extended', 'fleet'
    status TEXT DEFAULT 'active',      -- 'active', 'expiring_soon', 'expired', 'claimed', 'void'
    invoice_zoho_id TEXT,              -- links to zoho_invoices
    notes TEXT,
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE warranty_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration_id UUID NOT NULL REFERENCES warranty_registrations(id),
    ticket_zoho_id TEXT,               -- links to zoho_tickets
    claim_date DATE NOT NULL DEFAULT CURRENT_DATE,
    issue_description TEXT NOT NULL,
    resolution TEXT,
    status TEXT DEFAULT 'open',        -- 'open', 'investigating', 'approved', 'denied', 'resolved'
    parts_replaced JSONB,              -- array of {part_code, description, cost}
    labour_cost NUMERIC(10,2),
    total_cost NUMERIC(10,2),
    approved_by TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Zoho Sync Tracking
-- ═══════════════════════════════════════════════════════

CREATE TABLE zoho_sync_log (
    id BIGSERIAL PRIMARY KEY,
    entity_type TEXT NOT NULL,         -- 'contacts', 'accounts', 'deals', 'tickets', 'invoices'
    direction TEXT NOT NULL,           -- 'zoho_to_local', 'local_to_zoho'
    records_synced INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running',     -- 'running', 'completed', 'failed'
    error_message TEXT,
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Indexes
-- ═══════════════════════════════════════════════════════

-- Zoho
CREATE INDEX idx_zoho_contacts_email ON zoho_contacts(email);
CREATE INDEX idx_zoho_contacts_company ON zoho_contacts(company);
CREATE INDEX idx_zoho_accounts_type ON zoho_accounts(account_type);
CREATE INDEX idx_zoho_deals_stage ON zoho_deals(stage);
CREATE INDEX idx_zoho_deals_account ON zoho_deals(account_zoho_id);
CREATE INDEX idx_zoho_deals_closing ON zoho_deals(closing_date);
CREATE INDEX idx_zoho_tickets_status ON zoho_tickets(status);
CREATE INDEX idx_zoho_tickets_product ON zoho_tickets(product_name);
CREATE INDEX idx_zoho_tickets_account ON zoho_tickets(account_zoho_id);
CREATE INDEX idx_zoho_invoices_status ON zoho_invoices(status);
CREATE INDEX idx_zoho_invoices_account ON zoho_invoices(account_zoho_id);
CREATE INDEX idx_zoho_invoices_due ON zoho_invoices(due_date);

-- Warranty
CREATE INDEX idx_warranty_reg_product ON warranty_registrations(product_code);
CREATE INDEX idx_warranty_reg_account ON warranty_registrations(account_zoho_id);
CREATE INDEX idx_warranty_reg_end ON warranty_registrations(warranty_end);
CREATE INDEX idx_warranty_reg_status ON warranty_registrations(status);
CREATE INDEX idx_warranty_claims_reg ON warranty_claims(registration_id);
CREATE INDEX idx_warranty_claims_status ON warranty_claims(status);

-- Doctrine
CREATE INDEX idx_doctrine_product ON product_doctrine(product_code);

-- Sync log
CREATE INDEX idx_sync_log_entity ON zoho_sync_log(entity_type);
CREATE INDEX idx_sync_log_status ON zoho_sync_log(status);

-- ═══════════════════════════════════════════════════════
-- Permissions
-- ═══════════════════════════════════════════════════════

GRANT SELECT, INSERT, UPDATE, DELETE ON zoho_contacts TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON zoho_accounts TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON zoho_deals TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON zoho_tickets TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON zoho_invoices TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON product_doctrine TO fabian_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON warranty_registrations TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON warranty_claims TO fabian_app;  -- no DELETE on claims
GRANT SELECT, INSERT, UPDATE ON zoho_sync_log TO fabian_app;
GRANT USAGE, SELECT ON SEQUENCE zoho_sync_log_id_seq TO fabian_app;

-- ═══════════════════════════════════════════════════════
-- Seed PB4000 Doctrine v1.0
-- ═══════════════════════════════════════════════════════

INSERT INTO product_doctrine (product_code, variant, doctrine_version, specifications, compliance_requirements, deployment_rules, warranty_terms) VALUES
('PB4000', 'basic', 'v1.0',
  '{"weight_kg": 70, "arm_span_m": 6, "speed_rating_kmh": 110, "price_range_aud": "5995-10495", "operation": "TC or remote", "units_deployed": 1500}'::jsonb,
  '{"nsw_tcaws": "Required where posted speed >45 km/h and traffic must be stopped. Boom barrier — not stop/slow bat.", "certifications": ["AS/NZS 3845.2"], "requires_tc": true}'::jsonb,
  '{"use_when": ["Urban road works ≤50 km/h with lane closure", "Arterial works 60-70 km/h", "Any site where posted speed >45 km/h"], "do_not_use_when": ["Shoulder-only works with no lane closure", "Highway ≥80 km/h without TMA"], "deploy_time_minutes": 5}'::jsonb,
  '{"standard_months": 12, "extended_available": true, "conditions": ["Normal operational wear", "Manufacturing defects", "Excludes damage from vehicle impact"]}'::jsonb
),
('PB4000', 'tastrack', 'v1.0',
  '{"base": "PB4000", "platform": "TASTrack IoT", "monitoring": "real-time", "pre_start": "digital compliance", "data": "vehicle counting"}'::jsonb,
  '{"nsw_tcaws": "Same as basic PB4000", "iot_data_retention": "12 months minimum"}'::jsonb,
  '{"use_when": ["Long-term projects", "Fleet management requirements", "Client requires data reporting"], "additional": "TASTrack subscription required"}'::jsonb,
  '{"standard_months": 12, "iot_subscription_separate": true}'::jsonb
),
('PB4000', 'tma', 'v1.0',
  '{"base": "PB4000", "speed_zone_kmh": "≥70", "tma_required": true, "pwztmp_required": true}'::jsonb,
  '{"nsw_tcaws": "TMA mandatory at ≥70 km/h", "rol_required": "likely", "pwztmp": "Required on site"}'::jsonb,
  '{"use_when": ["Highway works ≥70 km/h"], "requires": ["Truck Mounted Attenuator", "PWZTMP qualified TC"]}'::jsonb,
  '{"standard_months": 12, "tma_warranty_separate": true}'::jsonb
),
('PB4000', 'event', 'v1.0',
  '{"base": "PB4000", "deploy_time_minutes": 5, "operation": "manual or remote", "power": "battery or 240V", "fleet_discount": true}'::jsonb,
  '{"event_specific": "Vehicle exclusion zones, VIP access, emergency access control"}'::jsonb,
  '{"use_when": ["Major events", "Vehicle exclusion zones", "VIP/emergency access control"]}'::jsonb,
  '{"standard_months": 12}'::jsonb
),
('PB4000', 'rapid', 'v1.0',
  '{"base": "PB4000", "deploy_time_minutes": 3, "weight_kg": 70, "operators": "1-2 persons", "tastrack_optional": true}'::jsonb,
  '{"pre_rigged": true, "operator_briefed": true}'::jsonb,
  '{"use_when": ["Emergency services", "Incident response", "Critical infrastructure protection"], "pre_positioned": true}'::jsonb,
  '{"standard_months": 12}'::jsonb
),
('MINIBOOM-TZ30', 'standard', 'v1.0',
  '{"weight_kg": 20, "hardware_cost_aud": 4000, "subscription_weekly_aud": "65-125", "launch_date": "2026-10-01", "traffic_light_integrated": true, "one_person_deploy": true}'::jsonb,
  '{"nsw_tcaws": "For lower speed environments where single-operator deployment is required"}'::jsonb,
  '{"use_when": ["Facilities requiring one-person deployment", "Lower speed zones", "No machinery available"], "program": "TZ30"}'::jsonb,
  '{"subscription_model": true, "hardware_warranty_months": 12}'::jsonb
);
