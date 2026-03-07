# Warranty Engine

Automated warranty lifecycle management for TAS products.

## How It Works

1. **Registration** — POST `/webhook/warranty-register` with serial number, product, purchase date
2. **Daily Check** — Cron at 7 AM marks warranties as `expiring_soon` (30-day window) or `expired`
3. **Alerts** — Email sent to Fabian when units are expiring within 30 days
4. **Claims** — POST `/webhook/warranty-claim` with serial number and issue description
5. **Resolution** — Claim investigated, approved/denied, parts/labour tracked

## Warranty Lifecycle

```
(new) ──[registered]──> active ──[30 days before end]──> expiring_soon ──[past end]──> expired
                          │
                          └──[claim lodged]──> claimed ──[resolved]──> active (or expired)
```

## Status Definitions

| Status | Meaning |
|--------|---------|
| `active` | Warranty in effect. Claims accepted. |
| `expiring_soon` | Within 30 days of expiry. Alert sent. |
| `expired` | Past warranty end date. New claims rejected. |
| `claimed` | Active claim in progress. |
| `void` | Warranty voided (misuse, unauthorized modification). |

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook/warranty-register` | POST | Register a new unit warranty |
| `/webhook/warranty-claim` | POST | Lodge a warranty claim |
| `/webhook/daily-flash` | GET | Includes warranty summary in company dashboard |

## Registration Payload

```json
{
  "serial_number": "PB4000-AU-00123",
  "product_code": "PB4000",
  "variant": "basic",
  "account_zoho_id": "12345",
  "contact_zoho_id": "67890",
  "purchase_date": "2026-03-01",
  "warranty_type": "standard"
}
```

## Claim Payload

```json
{
  "serial_number": "PB4000-AU-00123",
  "issue_description": "Boom arm mechanism stuck at 45 degrees",
  "ticket_zoho_id": "TICKET-456"
}
```

## Monitoring

Sam checks weekly:
- Are warranty alerts being sent? (check `health_checks` for `warranty_engine`)
- Are there unresolved claims older than 10 business days?
- Is the `expiring_soon` count growing? (may indicate sales should push extended warranties)

## Database Tables

- `warranty_registrations` — one row per unit serial number
- `warranty_claims` — one row per claim (no DELETE, audit trail)
- `product_doctrine` — product specs and warranty terms

## Integration with Zoho

- `account_zoho_id` links to `zoho_accounts` for customer lookup
- `contact_zoho_id` links to `zoho_contacts` for notification
- `ticket_zoho_id` in claims links to `zoho_tickets` for support tracking
- `invoice_zoho_id` in registrations links to `zoho_invoices` for purchase verification
