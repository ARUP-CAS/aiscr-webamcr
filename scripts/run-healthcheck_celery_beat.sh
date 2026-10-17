#!/bin/bash
# Healthcheck kontejneru celery_beat.
# Beat nezávisí na workeru, potřebuje jen databázi (DatabaseScheduler v django_celery_beat)
# a broker (Redis), kam odesílá naplánované úlohy. Kontroluje se dostupnost obou bez startu Djanga.
DB_CONF="/run/secrets/db_conf"
REDIS_PASSWORD=$(cat /run/secrets/redis_pass)
REDIS_HOST=$(jq -r '.REDIS_HOST // "redis"' "$DB_CONF")
REDIS_PORT=$(jq -r '.REDIS_PORT // 6379' "$DB_CONF")
DB_HOST=$(jq -r '.DB_HOST' "$DB_CONF")
DB_PORT=$(jq -r '.DB_PORT' "$DB_CONF")

# Image nemá ENTRYPOINT, takže `command` z compose běží jako PID 1 (procps v image není).
if ! tr '\0' ' ' < /proc/1/cmdline | grep -q "celery .* beat"; then
    echo "Proces celery beat neběží."
    exit 1
fi

if [ "$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --no-auth-warning -a "$REDIS_PASSWORD" PING)" != "PONG" ]; then
    echo "Redis $REDIS_HOST:$REDIS_PORT neodpovídá."
    exit 1
fi

if ! pg_isready -q -h "$DB_HOST" -p "$DB_PORT" -t 10; then
    echo "Databáze $DB_HOST:$DB_PORT není dostupná."
    exit 1
fi

exit 0
