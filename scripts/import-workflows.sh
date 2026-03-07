#!/bin/bash
set -euo pipefail

# Fabian OS — n8n Workflow Import Script
# Imports all workflow JSON files from n8n-workflows/ directory via n8n API.
# Usage: ./scripts/import-workflows.sh
#
# Prerequisites:
#   - n8n must be running (docker-compose up -d n8n)
#   - N8N_API_KEY must be set (generate in n8n Settings > API)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WORKFLOWS_DIR="$PROJECT_DIR/n8n-workflows"

N8N_BASE_URL="${N8N_BASE_URL:-http://localhost:5678}"
N8N_API_KEY="${N8N_API_KEY:-}"

# Load .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  source "$PROJECT_DIR/.env"
  set +a
fi

if [ -z "$N8N_API_KEY" ]; then
  echo "ERROR: N8N_API_KEY not set."
  echo "Generate one in n8n UI: Settings > API > Create API Key"
  echo "Then: export N8N_API_KEY=your_key"
  exit 1
fi

echo "=== Fabian OS — n8n Workflow Import ==="
echo "Source: $WORKFLOWS_DIR"
echo "Target: $N8N_BASE_URL"
echo ""

# Wait for n8n to be ready
echo "Checking n8n availability..."
for i in {1..15}; do
  if curl -sf "$N8N_BASE_URL/healthz/readiness" > /dev/null 2>&1; then
    echo "n8n is ready."
    break
  fi
  if [ "$i" -eq 15 ]; then
    echo "ERROR: n8n not ready after 15 attempts."
    exit 1
  fi
  sleep 2
done

IMPORTED=0
FAILED=0

for workflow_file in "$WORKFLOWS_DIR"/*.json; do
  filename=$(basename "$workflow_file")
  name=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['name'])" "$workflow_file" 2>/dev/null || echo "$filename")

  # Import workflow via API
  response=$(curl -sf -X POST "$N8N_BASE_URL/api/v1/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d @"$workflow_file" 2>&1) && status=$? || status=$?

  if [ $status -eq 0 ]; then
    workflow_id=$(echo "$response" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','?'))" 2>/dev/null || echo "?")
    echo "  OK: $name (id: $workflow_id)"
    IMPORTED=$((IMPORTED + 1))
  else
    echo "  FAIL: $name — $response"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
echo "=== Import complete: $IMPORTED imported, $FAILED failed ==="
