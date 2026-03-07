# PB4000 Product Doctrine

Codified product knowledge for the PORTABOOM PB4000 portable boom barrier.
This is the Company layer's authoritative reference for all PB4000 decisions.

## Product Family

| Code | Variant | Use Case |
|------|---------|----------|
| PB4000 basic | Standard unit | Urban/arterial road works, general use |
| PB4000 TASTrack | IoT fleet management | Long-term projects, fleet tracking, data reporting |
| PB4000 TMA | High-speed highway | Speeds >=70 km/h, paired with Truck Mounted Attenuator |
| PB4000 event | Crowd management | Events, vehicle exclusion zones, VIP access |
| PB4000 rapid | Emergency response | Pre-rigged for incident response, <3 min deploy |
| MINIBOOM TZ30 | Smart mini barrier | Sub-20kg, integrated traffic light, one-person deploy |

## Core Specs (PB4000 Basic)

- Weight: ~70 kg
- Arm span: up to 6 m
- Speed rating: up to 110 km/h (with TGS)
- Price range: $5,995-$10,495 AUD
- Operation: TC-controlled or remote
- Units deployed: 1,500+ across Australia
- Deploy time: <5 minutes (2 operators)

## NSW TCAWS Compliance

**The rule:** Posted speed >45 km/h requires a **portable boom barrier** (not stop/slow bat) when traffic must be stopped.

- Reference: Traffic Control at Work Sites (NSW) - AS 1742.3
- Certification: AS/NZS 3845.2
- Traffic controller (PWZTMP/ITCP) required at all PB4000 sites

## Deployment Rules

### Use PB4000 when:
- Urban road works <=50 km/h with lane closure
- Arterial works 60-70 km/h
- Any site where posted speed >45 km/h and traffic must be stopped

### Do NOT use PB4000 alone when:
- Highway >=80 km/h (requires TMA variant)
- Shoulder-only works with no lane closure (cones sufficient)

## Warranty

- Standard: 12 months from purchase
- Extended: 24 months (available on request)
- Covers: manufacturing defects, electrical/mechanical failure, normal operational wear
- Excludes: vehicle impact damage, misuse outside deployment rules, unauthorized modifications
- Claims: Lodge via Zoho Desk, category "Warranty". TAS reviews within 5 business days.

## Data Source

Doctrine is seeded in `product_doctrine` table (migration 06) and defined in `schemas/pb4000_doctrine.json`.
The Zoho Desk product field links tickets to the correct product for warranty and support routing.
