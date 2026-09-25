#!/bin/bash
set -e

# Execute SQL command using psql against the default container environment
psql -v ON_ERROR_STOP=1 --username "$PG_USER" --dbname "$PG_DB" <<-EOSQL
    ALTER ROLE app_user WITH ENCRYPTED PASSWORD '${APP_USER_PW}';
EOSQL
