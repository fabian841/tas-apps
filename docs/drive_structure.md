# Google Drive 12-Folder Structure

The 12-folder TAS structure must be fully implemented before Phase 1 begins.
Folder position determines document state. This is the document state machine.

## State Semantics

| Folder | State | Meaning |
|--------|-------|---------|
| `00_INBOX` | Raw | Unprocessed inputs. Every input starts here. |
| `01_WORKING` | In progress | Documents being worked on. Not yet confirmed. |
| `02_CONFIRMED` | Truth | Promoted by Fabian only. Automation reads from here. |

## Folder Structure

| # | Folder | Code | Subfolders |
|---|--------|------|------------|
| 01 | BUSINESS | BIZ | SHR FIN CMP BRD RES ARC |
| 02 | PRODUCTS | PRD | PB4 PB5 MBM PTL VMS IOT RES ARC |
| 03 | MANUFACTURING | MFG | ANK TRF RES ARC |
| 04 | SALES | SLS | NSP JAY DIR HIR PRP RES ARC |
| 05 | MARKETING | MKT | H26 BRA WEB CIN RES ARC |
| 06 | STRATEGY | STR | BPL MTG INV DDG FND REG RES ARC |
| 07 | PERSONAL | PER | LNG TRV OTH RES ARC |
| 08 | CLAUDE | CLW | TPL REF IDX ARC |
| 09 | IDEAS | IDR | BIZ PRD SFT OTH ARC |
| 10 | INTERNATIONAL | INT | UKM CAN USA NZL RES ARC |
| 12 | PEOPLE | PPL | JAK TYN BRK LAW ARC |

## Rules

- **07-PERSONAL**: No staff access. Personal layer only.
- **08-CLAUDE**: Claude workspace — templates, reference docs, indexes.
- **09-IDEAS**: Not confirmed, not active. Research and ideation only.
- Automation may only read from `02_CONFIRMED`. Never from `00_INBOX` or `01_WORKING`.
- Fabian is the only person who promotes documents to `02_CONFIRMED`.
