# Backup Restore Procedure

**Test quarterly.** Document each test result below.

## Steps

1. Stop services:
   ```bash
   cd /opt/fabian-os
   docker-compose down
   ```

2. Restore database (using latest backup):
   ```bash
   LATEST=$(ls -td /backups/*/ | head -1)
   pg_restore --clean --if-exists --no-owner --dbname=fabian_os "$LATEST/fabian_os.dump"
   ```

3. Start services:
   ```bash
   docker-compose up -d
   ```

4. Verify health:
   ```bash
   docker ps
   curl http://localhost:5678/healthz/readiness
   curl http://localhost:5678/webhook/health-summary
   ```

## Success Criteria

All checks pass and data is present.

## Test Log

| Date | Conducted By | Result | Notes |
|------|-------------|--------|-------|
| _pending_ | _—_ | _—_ | Initial test not yet performed |
