# Fabian OS – Restore Procedure

This document covers backup and disaster recovery for all Fabian OS components.

---

## 1. PostgreSQL Database

### Backup (Production)

```bash
# Full database dump (compressed)
docker exec fabian-postgres pg_dump -U fabian -Fc fabian_os > backup_fabian_os_$(date +%Y%m%d_%H%M%S).dump

# Schema-only backup
docker exec fabian-postgres pg_dump -U fabian --schema-only fabian_os > schema_fabian_os_$(date +%Y%m%d).sql

# Specific tables
docker exec fabian-postgres pg_dump -U fabian -t canonical_deal -t canonical_contact fabian_os > partial_backup.dump
```

### Backup (Staging)

```bash
docker exec fabian-postgres pg_dump -U fabian -Fc fabian_os_dev > backup_fabian_os_dev_$(date +%Y%m%d_%H%M%S).dump
```

### Restore

```bash
# Restore to a clean database
docker exec -i fabian-postgres pg_restore -U fabian -d fabian_os --clean --if-exists < backup_fabian_os_YYYYMMDD_HHMMSS.dump

# Restore to staging for testing
docker exec -i fabian-postgres pg_restore -U fabian -d fabian_os_dev --clean --if-exists < backup_fabian_os_YYYYMMDD_HHMMSS.dump
```

### Verify Backup

```bash
# Check table row counts after restore
docker exec fabian-postgres psql -U fabian -d fabian_os -c "
SELECT 'raw_emails' AS table_name, COUNT(*) FROM raw_emails
UNION ALL SELECT 'raw_drive_files', COUNT(*) FROM raw_drive_files
UNION ALL SELECT 'canonical_deal', COUNT(*) FROM canonical_deal
UNION ALL SELECT 'canonical_contact', COUNT(*) FROM canonical_contact
UNION ALL SELECT 'event_log', COUNT(*) FROM event_log
UNION ALL SELECT 'health_checks', COUNT(*) FROM health_checks;
"
```

---

## 2. n8n Workflows

### Export All Workflows

```bash
# Via n8n CLI inside the container
docker exec fabian-n8n n8n export:workflow --all --output=/home/node/.n8n/backups/workflows.json

# Copy to host
docker cp fabian-n8n:/home/node/.n8n/backups/workflows.json ./n8n/backups/workflows_$(date +%Y%m%d).json
```

### Export Credentials (encrypted)

```bash
docker exec fabian-n8n n8n export:credentials --all --output=/home/node/.n8n/backups/credentials.json
docker cp fabian-n8n:/home/node/.n8n/backups/credentials.json ./n8n/backups/credentials_$(date +%Y%m%d).json
```

### Import Workflows

```bash
docker cp ./n8n/backups/workflows_YYYYMMDD.json fabian-n8n:/home/node/.n8n/backups/
docker exec fabian-n8n n8n import:workflow --input=/home/node/.n8n/backups/workflows_YYYYMMDD.json
```

---

## 3. Docker Volumes

### Backup Volumes

```bash
# PostgreSQL data volume
docker run --rm -v tas-apps_pgdata:/data -v $(pwd)/backups:/backup alpine tar czf /backup/pgdata_$(date +%Y%m%d).tar.gz -C /data .

# n8n data volume
docker run --rm -v tas-apps_n8n_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/n8n_data_$(date +%Y%m%d).tar.gz -C /data .
```

### Restore Volumes

```bash
# Stop services first
docker compose down

# Restore PostgreSQL volume
docker run --rm -v tas-apps_pgdata:/data -v $(pwd)/backups:/backup alpine sh -c "cd /data && tar xzf /backup/pgdata_YYYYMMDD.tar.gz"

# Restore n8n volume
docker run --rm -v tas-apps_n8n_data:/data -v $(pwd)/backups:/backup alpine sh -c "cd /data && tar xzf /backup/n8n_data_YYYYMMDD.tar.gz"

# Restart services
docker compose up -d
```

---

## 4. Configuration Files

All configuration is version-controlled in the GitHub repository:

- `docker-compose.yml` – Service definitions
- `config/glance.yml` – Dashboard configuration
- `migrations/*.sql` – Database schema
- `schemas/*.json` – Canonical object schemas
- `n8n/workflows/*.json` – Workflow templates

To restore: `git clone` the repository and run `docker compose up -d`.

---

## 5. Full Disaster Recovery Checklist

1. Clone the repository from GitHub
2. Copy `.env` from secure backup (not in git)
3. `docker compose up -d` to start services
4. Restore PostgreSQL from latest backup
5. Run `./migrations/run_migrations.sh prod` (idempotent – safe to re-run)
6. Import n8n workflows from backup
7. Import n8n credentials (requires same `N8N_ENCRYPTION_KEY`)
8. Verify health endpoint: `curl http://localhost:5678/webhook/health-summary`
9. Verify Glance dashboard: `http://localhost:8080`
10. Run capture scripts to verify connectivity

---

## 6. Backup Schedule (Recommended)

| What | Frequency | Retention |
|------|-----------|-----------|
| PostgreSQL full dump | Daily | 30 days |
| n8n workflow export | Weekly | 12 weeks |
| Docker volume snapshots | Weekly | 4 weeks |
| Git repository | Every commit (automatic) | Permanent |
