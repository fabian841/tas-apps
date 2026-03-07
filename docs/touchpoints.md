# 4 Daily Touchpoints

Phase 1 introduces structured daily interaction points.
Each touchpoint has a specific purpose — no overlap.

## Touchpoint 1: Morning Pulse (6:30am)

**Purpose:** Orientation. Read-only. No decisions.
**Surface:** Glance dashboard — "Morning Pulse" tab
**Duration:** 2-3 minutes

What you see:
- Time and weather (Sydney)
- Today's calendar
- Email unread counts (TAS + personal)
- PLAUD transcript count (last 24h)
- Register health (confirmed/pending per register)
- n8n service status

**Rule:** Look, don't act. Decisions happen later.

## Touchpoint 2: Midday Check-in (12:30pm)

**Purpose:** Awareness. What has the system extracted today?
**Surface:** Glance dashboard — "Midday Check-in" tab
**Duration:** 3-5 minutes

What you see:
- Today's extraction summary (items per register)
- Upcoming commitments (due within 3 days)
- Email status

**Rule:** Note items to review later. Don't confirm/reject yet.

## Touchpoint 3: Evening Review (6:00pm)

**Purpose:** Gate review. Confirm or reject PROPOSED items.
**Surface:** Glance dashboard — "Evening Review" tab + POST to /gate-action
**Duration:** 10-15 minutes

What you see:
- Gate stats (pending/confirmed/rejected today)
- Items sorted by confidence (HIGH first)
- Register totals

**What you do:**
- Review each PROPOSED item
- Confirm (writes to Google Sheet) or reject (logged with reason)
- HIGH confidence items should be fast — most are correct
- LOW confidence items may need more thought or rejection

**Rule:** This is the only time items become truth.

## Touchpoint 4: Weekly Reflection (Sunday 6pm)

**Purpose:** Step back. How is the system performing?
**Surface:** Email (automated by n8n)
**Duration:** 5-10 minutes

What you receive:
- Gate summary for the week (proposed/confirmed/rejected by register)
- List of confirmed items
- Extraction quality (confirmation rate %)
- Unreviewed backlog count and age

**Rule:** If confirmation rate < 20%, tell Sam to tune the extraction prompt.
