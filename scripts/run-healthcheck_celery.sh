#!/bin/bash
# Healthcheck kontejneru celery_worker.
# 1) Řídící rovina: jedno volání `inspect scheduled` na konkrétní worker ověří, že worker odpovídá
#    přes broker (bez odpovědi celery vrací nenulový kód), a zároveň vrátí úlohy s ETA. Pokud je
#    některá úloha po ETA déle než 120 s, worker úlohy nezpracovává.
# 2) Výkonná rovina: potomci prefork poolu po každé dokončené úloze zapisují do Redisu čas
#    (klíč celery_worker_last_task_done:<worker>, handler cron.tasks.record_celery_worker_task_done)
#    a beat každé 2 minuty posílá prázdnou úlohu celery_worker_liveness_ping. Je-li klíč starší
#    než LIVENESS_MAX_AGE, worker je nezdravý jen tehdy, když na něj čeká práce (fronta nebo
#    rezervované úlohy) a zároveň má volné potomky. Zaneprázdněný worker (všichni potomci
#    vykonávají úlohu) ani prázdná fronta (např. neběží beat) poplach nevyvolají.
CELERY_APP_PATH="webclient"
WORKER_NAME="worker1@amcr"
QUEUE_NAME="celery"
LIVENESS_KEY="celery_worker_last_task_done:${WORKER_NAME}"
LIVENESS_MAX_AGE=600

DB_CONF="/run/secrets/db_conf"
REDIS_PASSWORD=$(cat /run/secrets/redis_pass)
REDIS_HOST=$(jq -r '.REDIS_HOST // "redis"' "$DB_CONF")
REDIS_PORT=$(jq -r '.REDIS_PORT // 6379' "$DB_CONF")

redis_cmd() {
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --no-auth-warning -a "$REDIS_PASSWORD" "$@"
}

if ! output=$(celery -A $CELERY_APP_PATH inspect scheduled -d "$WORKER_NAME" --timeout 10); then
    echo "Worker $WORKER_NAME neodpověděl."
    exit 1
fi

dates=$(echo "$output" | grep 'eta' | awk '{print $3}' | tr -d "',")
current_seconds=$(date +%s)
greatest_diff=0
while IFS= read -r line; do
    # Skip empty lines
    if [ -z "$line" ]; then continue; fi
    date_seconds=$(date -d"$line" +%s)
    seconds_diff=$((current_seconds - date_seconds))
    if [ $seconds_diff -gt $greatest_diff ]; then
        greatest_diff=$seconds_diff
    fi
done <<< "$dates"

if [ "$greatest_diff" -ge 120 ]; then
    echo "Úloha je $greatest_diff s po ETA."
    exit 1
fi

if ! last_done=$(redis_cmd GET "$LIVENESS_KEY"); then
    echo "Redis $REDIS_HOST:$REDIS_PORT neodpovídá."
    exit 1
fi
# Chybějící klíč (worker od startu Redisu nic nedokončil) se bere jako libovolně starý.
if [[ "$last_done" =~ ^[0-9]+$ ]]; then
    age=$((current_seconds - last_done))
else
    age=$((LIVENESS_MAX_AGE + 1))
fi
if [ "$age" -le "$LIVENESS_MAX_AGE" ]; then
    exit 0
fi

queued=$(redis_cmd LLEN "$QUEUE_NAME")
if ! [[ "$queued" =~ ^[0-9]+$ ]]; then
    echo "Nelze zjistit délku fronty $QUEUE_NAME: $queued"
    exit 1
fi
# Jeden proces Pythonu místo tří volání `celery inspect`; limit=1 vrací hned po odpovědi workeru.
# Po každém volání se hned končí, aby neodpovídající worker stál nejvýš jeden timeout (5 s)
# a skript skončil vlastní hláškou dřív, než vyprší timeout healthchecku v docker-compose.yml.
if ! load=$(python - "$WORKER_NAME" <<'PY'
import sys

from webclient.celery import app

worker = sys.argv[1]
inspect = app.control.inspect(destination=[worker], timeout=5, limit=1)
replies = []
for method in (inspect.active, inspect.reserved, inspect.stats):
    reply = (method() or {}).get(worker)
    if reply is None:
        sys.exit(1)
    replies.append(reply)
active, reserved, stats = replies
print(len(active), len(reserved), stats["pool"]["max-concurrency"])
PY
); then
    echo "Worker $WORKER_NAME neodpověděl na inspect active/reserved/stats."
    exit 1
fi
# Výsledek je poslední řádek výstupu (import aplikace může něco vypsat před ním).
read -r active reserved concurrency <<< "$(echo "$load" | tail -n 1)"

waiting=$((queued + reserved))
if [ "$waiting" -eq 0 ]; then
    exit 0
fi
if [ "$active" -ge "$concurrency" ]; then
    echo "Worker $WORKER_NAME je zaneprázdněný ($active/$concurrency), poslední úloha dokončena před $age s."
    exit 0
fi
echo "Worker $WORKER_NAME nezpracovává úlohy: poslední dokončena před $age s, čeká $waiting úloh, aktivní $active/$concurrency."
exit 1
