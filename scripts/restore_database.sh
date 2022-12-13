#!/usr/bin/env bash
echo "Restoring database"
psql -U postgres -c "DROP DATABASE IF EXISTS ${DBNAME};"
psql -U postgres -c "CREATE DATABASE ${DBNAME};"
psql -U postgres -c "CREATE ROLE cz_archeologickamapa_api;"
psql -U postgres -c "CREATE ROLE ${DB_FLAG_ROLE};"
psql -U postgres -c "ALTER ROLE ${DB_FLAG_ROLE} CONNECTION LIMIT 0;"
pg_restore -v -e -d ${DBNAME} -e /tmp/${USED_DB_BACKUP} > /tmp/log
psql -U postgres -c "ALTER ROLE ${DB_FLAG_ROLE} CONNECTION LIMIT -1;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ${DBNAME} TO postgres;"
echo "Database restored successfully"
