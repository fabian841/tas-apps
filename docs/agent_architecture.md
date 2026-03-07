# Agent Architecture — Phase 3

Claude Code remote agents replace the original Clawdbot concept.
Instead of building a custom agent loop, we use Claude Code's native capabilities:
MCP server connections, tool use, multi-step reasoning, and conversation context.

## Why Claude Code Instead of Custom Agent

| Concern | Custom Agent | Claude Code |
|---------|-------------|-------------|
| Agent loop | Build and maintain yourself | Anthropic maintains it |
| Tool access | Manual wiring per tool | Native tool use (Bash, Read, Edit, MCP) |
| MCP support | Build MCP client | Built-in MCP client |
| Context | Limited to what you pass | Full file + conversation context |
| Model upgrades | Manual swaps | Automatic access to latest models |
| Cost | Same API costs | Same API costs |

## Two Agent Contexts

### Personal Agent (PIL Layer)
- **Directory:** `agents/personal/`
- **System prompt:** `agents/personal/CLAUDE.md`
- **MCP config:** `agents/personal/.mcp.json`
- **MCP servers:** postgres (personal tables), google-sheets (PIL registers), filesystem
- **Scheduled:** Morning prep (6 AM), Evening prep (5:30 PM)
- **On demand:** POST `/webhook/agent-personal` with `{task: "..."}`

### Company Agent (GPX Layer)
- **Directory:** `agents/company/`
- **System prompt:** `agents/company/CLAUDE.md`
- **MCP config:** `agents/company/.mcp.json`
- **MCP servers:** postgres (company tables), zoho-crm, zoho-desk, zoho-books, filesystem
- **Scheduled:** Daily Flash prep (7 AM weekdays), Pipeline review (Monday 8 AM)
- **On demand:** POST `/webhook/agent-company` with `{task: "..."}`

## Hard Isolation

The Personal agent **cannot** see Company data. The Company agent **cannot** see Personal data.
This is enforced by:
1. Separate `.mcp.json` files — each agent only has MCP servers for its layer
2. Separate `CLAUDE.md` system prompts — each agent is instructed about its boundary
3. Separate Postgres connection strings (future: schema-level isolation)

## MCP Server Registry

| Server | Layer | Transport | What It Exposes |
|--------|-------|-----------|-----------------|
| postgres-personal | Personal | stdio | PIL tables: gate log, registers, transcripts |
| postgres-company | Company | stdio | Zoho canonical, warranty, doctrine tables |
| google-sheets | Personal | stdio | 8 PIL register spreadsheets |
| zoho-crm | Company | stdio | Contacts, accounts, deals + write ops |
| zoho-desk | Company | stdio | Tickets + create/update/comment |
| zoho-books | Company | stdio | Invoices, overdue, search |
| filesystem | Shared | stdio | `/opt/fabian-os/data` read/write |

## Agent Findings

All agent output follows the same confidence gate as PIL registers:

```
Agent produces finding → agent_findings (PROPOSED)
                              ↓
                     Fabian reviews
                              ↓
                   CONFIRMED or REJECTED
```

Finding types:
- **insight** — observation or pattern detected
- **recommendation** — suggested action (with confidence label)
- **alert** — something needs immediate attention
- **action_taken** — agent performed a write operation (logged)
- **data_update** — agent updated data in a system

## How n8n Triggers Agents

```
n8n cron/webhook → Create session record → Execute claude --print → Parse output → Complete session → Log event
```

The `claude --print` flag runs Claude Code non-interactively.
The agent's CLAUDE.md and .mcp.json in the working directory configure its behaviour and tools.

## Monitoring

Sam checks via the **Agent Monitor** Glance page:
- Are scheduled sessions running? (check `agent_sessions` for today's runs)
- Are any sessions failing? (status = 'failed')
- Are findings being reviewed? (proposed count should not grow unbounded)
- Are MCP servers healthy? (check `mcp_servers.status`)

## Cost Management

- Default model: `claude-sonnet-4-6` for cost efficiency
- `--max-turns` limits agent steps (20 personal, 25 company)
- Token usage tracked in `agent_sessions` (tokens_input, tokens_output, cost_usd)
- If costs exceed budget, reduce scheduled frequency or switch tasks to manual triggers
