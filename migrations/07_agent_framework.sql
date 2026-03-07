-- Phase 3: Agent Framework — Claude Code remote agents + MCP server registry
-- Replaces custom "Clawdbot" with Claude Code sessions connected to MCP servers.
-- Two agent contexts: Personal (PIL) and Company (GPX), hard-isolated.

-- ═══════════════════════════════════════════════════════
-- MCP Server Registry
-- ═══════════════════════════════════════════════════════

CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_name TEXT UNIQUE NOT NULL,    -- 'zoho-crm', 'postgres-personal', 'google-sheets'
    layer TEXT NOT NULL,                 -- 'personal', 'company', 'shared'
    transport TEXT NOT NULL,             -- 'stdio', 'sse', 'streamable-http'
    command TEXT,                        -- for stdio: the launch command
    url TEXT,                            -- for sse/http: the endpoint URL
    env_vars JSONB,                      -- required env vars (names only, not values)
    capabilities JSONB,                  -- list of tools/resources exposed
    status TEXT DEFAULT 'registered',    -- 'registered', 'active', 'disabled', 'error'
    last_health_check TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Agent Session Tracking
-- ═══════════════════════════════════════════════════════

CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_context TEXT NOT NULL,          -- 'personal', 'company'
    trigger_type TEXT NOT NULL,           -- 'scheduled', 'webhook', 'manual', 'n8n'
    trigger_source TEXT,                  -- e.g. 'evening_review', 'daily_flash', 'fabian_request'
    model TEXT NOT NULL DEFAULT 'claude-sonnet-4-6',
    mcp_servers_used TEXT[],             -- array of server_name values
    system_prompt_version TEXT,
    status TEXT DEFAULT 'running',        -- 'running', 'completed', 'failed', 'cancelled'
    input_summary TEXT,                   -- brief description of what was requested
    output_summary TEXT,                  -- brief description of what was produced
    tools_called INTEGER DEFAULT 0,
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd NUMERIC(8,4),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Agent Findings (structured output from agent sessions)
-- ═══════════════════════════════════════════════════════

CREATE TABLE agent_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES agent_sessions(id),
    agent_context TEXT NOT NULL,          -- 'personal', 'company'
    finding_type TEXT NOT NULL,           -- 'insight', 'action_taken', 'recommendation', 'alert', 'data_update'
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    confidence TEXT,                      -- 'HIGH', 'MEDIUM', 'LOW' (for recommendations)
    status TEXT DEFAULT 'PROPOSED',       -- same gate as PIL: PROPOSED -> CONFIRMED/REJECTED
    target_register TEXT,                 -- if this maps to a PIL register
    target_entity_type TEXT,              -- 'deal', 'ticket', 'warranty', etc.
    target_entity_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════
-- Indexes
-- ═══════════════════════════════════════════════════════

CREATE INDEX idx_mcp_servers_layer ON mcp_servers(layer);
CREATE INDEX idx_mcp_servers_status ON mcp_servers(status);
CREATE INDEX idx_agent_sessions_context ON agent_sessions(agent_context);
CREATE INDEX idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX idx_agent_sessions_started ON agent_sessions(started_at);
CREATE INDEX idx_agent_findings_session ON agent_findings(session_id);
CREATE INDEX idx_agent_findings_context ON agent_findings(agent_context);
CREATE INDEX idx_agent_findings_status ON agent_findings(status);
CREATE INDEX idx_agent_findings_type ON agent_findings(finding_type);

-- ═══════════════════════════════════════════════════════
-- Permissions
-- ═══════════════════════════════════════════════════════

GRANT SELECT, INSERT, UPDATE ON mcp_servers TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON agent_sessions TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON agent_findings TO fabian_app;

-- ═══════════════════════════════════════════════════════
-- Seed MCP Servers
-- ═══════════════════════════════════════════════════════

INSERT INTO mcp_servers (server_name, layer, transport, command, capabilities, status) VALUES
('postgres-personal', 'personal', 'stdio',
  'npx -y @anthropic/mcp-postgres postgresql://fabian_app:$APP_DB_PASSWORD@localhost:5432/fabian_os?options=-c%20search_path=personal',
  '["query", "execute", "describe_table", "list_tables"]'::jsonb,
  'registered'),
('postgres-company', 'company', 'stdio',
  'npx -y @anthropic/mcp-postgres postgresql://fabian_app:$APP_DB_PASSWORD@localhost:5432/fabian_os?options=-c%20search_path=company',
  '["query", "execute", "describe_table", "list_tables"]'::jsonb,
  'registered'),
('google-sheets', 'personal', 'stdio',
  'npx -y @anthropic/mcp-google-sheets --credentials-path $GOOGLE_SHEETS_CREDENTIALS_PATH',
  '["read_sheet", "write_sheet", "append_row", "list_sheets"]'::jsonb,
  'registered'),
('zoho-crm', 'company', 'stdio',
  'node /opt/fabian-os/mcp-servers/zoho-crm/index.js',
  '["search_contacts", "get_contact", "search_accounts", "get_account", "search_deals", "get_deal", "update_deal_stage", "create_note"]'::jsonb,
  'registered'),
('zoho-desk', 'company', 'stdio',
  'node /opt/fabian-os/mcp-servers/zoho-desk/index.js',
  '["search_tickets", "get_ticket", "create_ticket", "update_ticket", "add_comment"]'::jsonb,
  'registered'),
('zoho-books', 'company', 'stdio',
  'node /opt/fabian-os/mcp-servers/zoho-books/index.js',
  '["list_invoices", "get_invoice", "list_overdue", "search_invoices"]'::jsonb,
  'registered'),
('filesystem', 'shared', 'stdio',
  'npx -y @anthropic/mcp-filesystem /opt/fabian-os/data',
  '["read_file", "write_file", "list_directory"]'::jsonb,
  'registered');
