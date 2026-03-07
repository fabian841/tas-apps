#!/bin/bash
set -euo pipefail

# Fabian OS — Smoke Test Script
# Validates that all core services, database tables, and endpoints are operational.
# Usage: ./scripts/smoke-test.sh
#
# Exit codes: 0 = all pass, 1 = failures detected

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-fabian_os}"
DB_USER="${DB_USER:-fabian_admin}"
N8N_URL="${N8N_BASE_URL:-http://localhost:5678}"
GLANCE_URL="${GLANCE_URL:-http://localhost:8080}"

# Load .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  source "$PROJECT_DIR/.env"
  set +a
fi

PASS=0
FAIL=0

check() {
  local desc="$1"
  shift
  if "$@" > /dev/null 2>&1; then
    echo "  PASS  $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $desc"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Fabian OS — Smoke Tests ==="
echo ""

# --- Docker containers ---
echo "--- Docker Containers ---"
check "PostgreSQL container running" docker ps --format '{{.Names}}' | grep -q fabian-postgres
check "n8n container running" docker ps --format '{{.Names}}' | grep -q fabian-n8n
check "Glance container running" docker ps --format '{{.Names}}' | grep -q fabian-glance

# --- Database connectivity ---
echo ""
echo "--- Database ---"
check "PostgreSQL accepts connections" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"

# Core tables existence
EXPECTED_TABLES=(
  "raw_emails"
  "raw_transcripts"
  "raw_drive_files"
  "canonical_deal"
  "canonical_contact"
  "canonical_metric"
  "canonical_task"
  "canonical_product"
  "pil_decisions"
  "pil_commitments"
  "pil_ideas"
  "pil_learnings"
  "pil_relationships"
  "pil_health"
  "pil_finance"
  "pil_patterns"
  "confidence_gate_log"
  "zoho_contacts"
  "zoho_accounts"
  "zoho_deals"
  "zoho_tickets"
  "zoho_invoices"
  "product_doctrine"
  "warranty_registrations"
  "warranty_claims"
  "mcp_servers"
  "agent_sessions"
  "agent_findings"
  "canonical_quarter"
  "canonical_meeting"
  "canonical_scorecard"
  "health_checks"
  "event_log"
)

for table in "${EXPECTED_TABLES[@]}"; do
  check "Table exists: $table" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT 1 FROM information_schema.tables WHERE table_name='$table' AND table_schema='public';" | grep -q 1
done

# pgvector extension
check "pgvector extension loaded" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc \
  "SELECT 1 FROM pg_extension WHERE extname='vector';" | grep -q 1

# fabian_app role
check "fabian_app role exists" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc \
  "SELECT 1 FROM pg_roles WHERE rolname='fabian_app';" | grep -q 1

# --- Service endpoints ---
echo ""
echo "--- Service Endpoints ---"
check "n8n healthcheck" curl -sf "$N8N_URL/healthz/readiness"
check "Glance dashboard" curl -sf "$GLANCE_URL"

# n8n webhook endpoints
WEBHOOKS=(
  "health-summary"
  "metrics"
  "daily-flash"
  "email-status"
  "plaud-status"
  "register-stats"
  "agent-status"
  "rocks-progress"
  "scorecard"
  "upcoming-meetings"
  "agent-findings"
)

for webhook in "${WEBHOOKS[@]}"; do
  check "Webhook: /webhook/$webhook" curl -sf "$N8N_URL/webhook/$webhook"
done

# --- MCP server files ---
echo ""
echo "--- MCP Servers ---"
MCP_SERVERS=("zoho-crm" "zoho-desk" "zoho-books")
for server in "${MCP_SERVERS[@]}"; do
  check "MCP server file: $server" test -f "$PROJECT_DIR/mcp-servers/$server/index.js"
done

# --- Agent configs ---
echo ""
echo "--- Agent Framework ---"
check "Personal agent CLAUDE.md" test -f "$PROJECT_DIR/agents/personal/CLAUDE.md"
check "Company agent CLAUDE.md" test -f "$PROJECT_DIR/agents/company/CLAUDE.md"
check "Personal .mcp.json" test -f "$PROJECT_DIR/agents/personal/.mcp.json"
check "Company .mcp.json" test -f "$PROJECT_DIR/agents/company/.mcp.json"

# --- Summary ---
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
