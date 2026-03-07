# Confidence Gating Engine

The confidence gate is the enforcement mechanism for LIFE OS Principle #2:
**AI outputs are proposals — never authoritative.**

## How It Works

1. PLAUD transcript arrives via pipeline (Phase 0)
2. Claude API extracts structured items into register format
3. Every extracted item enters `confidence_gate_log` with status = **PROPOSED**
4. Fabian reviews during **Evening Review** touchpoint
5. Fabian confirms (PROPOSED -> CONFIRMED) or rejects (PROPOSED -> REJECTED)
6. Only CONFIRMED items are written to the Google Sheet register

## Confidence Labels

| Label | Meaning | Example |
|-------|---------|---------|
| **HIGH** | Direct quote or explicit statement. No ambiguity. | "I committed to delivering the proposal by Friday" |
| **MEDIUM** | Reasonable inference from context. Supporting evidence exists. | Discussion about timelines implies a soft deadline |
| **LOW** | Weak signal. Requires interpretation. May be noise. | Tone suggests concern about a relationship |

## State Machine

```
PROPOSED ──[Fabian confirms]──> CONFIRMED ──> Written to Google Sheet
    │
    └──[Fabian rejects]──> REJECTED (logged with reason, not written)
```

## Rules

- **No automation may promote PROPOSED to CONFIRMED.** Only Fabian.
- **No auto-write to registers.** The gate is the only path to truth.
- **Rejected items stay in the log.** They are never deleted — audit trail.
- **Patterns require 3+ occurrences.** Never propose a pattern from a single event.
- **LOW confidence items are shown last.** HIGH first to speed up review.

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook/gate-review` | GET | Fetch pending PROPOSED items for review |
| `/webhook/gate-action` | POST | Confirm or reject an item `{id, action, reason?}` |
| `/webhook/evening-review` | GET | Full evening review data (stats + items) |
| `/webhook/register-stats` | GET | Per-register counts for Morning Pulse |

## Monitoring

Sam checks weekly:
- Are PROPOSED items being reviewed? (backlog should not grow unbounded)
- Is the confirmation rate reasonable? (if <20%, extraction prompt needs tuning)
- Are any items being silently dropped? (check for errors in extraction_run)
