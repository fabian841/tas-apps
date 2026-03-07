# Disaster Recovery — Restore Procedure

Test quarterly. Log each drill.

## Steps

1. Stop all services:
   ```bash
   cd /opt/fabian-os && docker-compose down
   ```

2. Restore database from latest backup:
   ```bash
   LATEST=$(ls -td /backups/*/ | head -1)
   pg_restore --clean --if-exists --no-owner --dbname=fabian_os "$LATEST/fabian_os.dump"
   ```

3. Start services:
   ```bash
   docker-compose up -d
   ```

4. Verify health:
   - `docker ps` — all 3 containers running (postgres, n8n, glance)
   - `curl http://localhost:5678/healthz/readiness` — n8n responding
   - Check Glance dashboard at http://localhost:8080
   - Spot-check: `SELECT COUNT(*) FROM raw_transcripts;`

## Success Criteria

All checks pass and data is present.

## Drill Log

| Date | Conducted By | Result | Notes |
|------|-------------|--------|-------|
| | | | |
