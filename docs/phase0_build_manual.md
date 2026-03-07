# Fabian Operating System – Phase 0 Build Manual

**Version:** 4.1 (Implementation-Ready)
**Objective:** Build the minimum viable core – a reliable foundation that captures data, stores it in a layered database, runs basic automation, and provides a dashboard.
**Time estimate:** 5-7 days (if followed methodically).

---

## 1. Prerequisites & Preparation

### 1.1 Hardware / Environment

- A dedicated machine (or VM) running Ubuntu 22.04 LTS (or similar Linux). Mac users: adapt paths accordingly; Windows users: use WSL2 with Ubuntu.
- Minimum specs: 4 CPU cores, 8 GB RAM, 50 GB free disk (grows over time).
- Docker and Docker Compose installed.
- Git installed.
- Python 3.10+ and pip.
- Node.js 18+ and npm.

### 1.2 Accounts & API Credentials

| Service | What you need |
|---------|--------------|
| Gmail | Google Cloud Project with Gmail API enabled; OAuth 2.0 credentials (download `credentials.json`) |
| Microsoft 365 | Azure App registration with `Mail.Read` permission; note `client_id`, `client_secret`, `tenant_id` |
| Google Drive | Google Cloud Project with Drive API enabled; OAuth 2.0 credentials (download `credentials.json`) |
| Zoho | Zoho API credentials (client ID, secret) for CRM / Books / Projects |
| Xero | Xero App credentials (client ID, secret) – you can use demo company for testing |
| GitHub | Personal access token with repo scope |
| Perplexity | (Optional for Phase 0) API key |
| Claude | (Optional) API key if you want to use Claude AI nodes in n8n |

**Important:** Keep all credentials safe. Store them in environment variables, never in code.

---

## 2. Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd tas-apps

# 2. Set up environment
cp .env.example .env
# Edit .env with your credentials

# 3. Start all services
docker compose up -d

# 4. Verify services
docker ps
docker logs fabian-postgres
docker logs fabian-n8n

# 5. Run database migrations
./migrations/run_migrations.sh prod
./migrations/run_migrations.sh dev

# 6. Install Python dependencies for capture scripts
pip install -r scripts/requirements.txt

# 7. Set up Gmail OAuth (first run will open browser)
python scripts/gmail_capture.py --full-sync

# 8. Set up Drive OAuth (first run will open browser)
python scripts/drive_capture.py --full-sync

# 9. Access services
#    n8n:    http://localhost:5678
#    Glance: http://localhost:8080
```

---

## 3. Database Schema

All schema is managed via versioned migration files in `migrations/`. See individual files for details:

| Migration | Contents |
|-----------|----------|
| `001_extensions.sql` | pgcrypto, pgvector extensions |
| `002_raw_layer.sql` | `raw_emails`, `raw_drive_files`, `raw_agent_output` |
| `003_canonical_layer.sql` | All 7 canonical tables with auto-update triggers |
| `004_event_log.sql` | `event_log` table with indexes |
| `005_health_checks.sql` | `health_checks` table with seed data |
| `006_build_manual_extras.sql` | `credential_expiry` table, email classification column |

---

## 4. n8n Workflows

Import workflow templates from `n8n/workflows/` into n8n:

1. **Health Summary Webhook** (`health_summary.json`) – GET `/webhook/health-summary` returns component health status
2. **System Health Check** (`system_health_check.json`) – Runs every 15 min, checks for unhealthy components, logs alerts

After import, configure the PostgreSQL credential in each workflow to point to `fabian-postgres`.

---

## 5. Capture Scripts

### Gmail Capture

```bash
# Incremental sync (use after initial setup)
python scripts/gmail_capture.py

# Full resync (last 30 days)
python scripts/gmail_capture.py --full-sync

# Custom date range
python scripts/gmail_capture.py --full-sync --days 7
```

### Google Drive Capture

```bash
# Incremental sync
python scripts/drive_capture.py

# Full resync
python scripts/drive_capture.py --full-sync
```

### Scheduling (cron)

```bash
crontab -e
# Gmail: every 15 minutes
*/15 * * * * cd /path/to/tas-apps && python scripts/gmail_capture.py >> logs/gmail.log 2>&1
# Drive: every 30 minutes
*/30 * * * * cd /path/to/tas-apps && python scripts/drive_capture.py >> logs/drive.log 2>&1
# Backup: daily at 2 AM
0 2 * * * /path/to/tas-apps/scripts/backup.sh >> logs/backup.log 2>&1
```

---

## 6. Glance Dashboard

The dashboard is configured in `config/glance.yml` and shows:
- System health (from n8n `/health-summary` webhook)
- Business snapshot (placeholder until Phase 1 populates metrics)
- Recent events (from event_log)
- Clock (Australia/Sydney timezone)

Access at `http://localhost:8080`.

---

## 7. Health Monitoring

Every component reports status to the `health_checks` table:

| Component | Updated By |
|-----------|-----------|
| `gmail_capture` | Gmail capture script |
| `drive_capture` | Drive capture script |
| `n8n_service` | System health check workflow |
| `postgres_service` | Seeded on init |

The system health check workflow runs every 15 minutes and alerts on any non-OK status.

---

## 8. Backup & Restore

Run `scripts/backup.sh` daily. It creates:
- PostgreSQL dump (production and staging)
- Configuration archive
- n8n workflow export (if container is running)

See `docs/restore_procedure.md` for full disaster recovery steps.

---

## 9. Phase 0 Success Criteria Checklist

Before moving to Phase 1, ensure all are true for at least 7 consecutive days:

- [ ] Email capture runs with zero silent failures (check logs and health_checks)
- [ ] Two n8n workflows run successfully with >=95% success rate
- [ ] NotebookLM is used at least once weekly on real documents
- [ ] Glance shows live system health and business metrics
- [ ] Raw, canonical, and event log tables exist and are populated
- [ ] Backup and restore test has been completed successfully
- [ ] All secrets stored in environment variables (never in code)
- [ ] GitHub repo contains all configs and schemas
- [ ] Staging environment exists and is used for testing
- [ ] Health monitoring alerts work (test by causing a temporary failure)
- [ ] You can explain the entire Phase 0 system in 2 minutes
