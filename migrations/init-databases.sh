#!/bin/bash
# Creates the staging/dev database alongside the production database.
# This script runs automatically on first PostgreSQL container startup
# via docker-entrypoint-initdb.d.

set -e

POSTGRES_DEV_DB="${POSTGRES_DEV_DB:-fabian_os_dev}"

echo "Creating staging database: $POSTGRES_DEV_DB"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE "$POSTGRES_DEV_DB" OWNER "$POSTGRES_USER";
EOSQL
echo "Staging database '$POSTGRES_DEV_DB' created successfully."
