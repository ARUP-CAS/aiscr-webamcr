#!/bin/bash
# Healthcheck kontejneru celery_worker.
# Jedno volání `inspect scheduled` na konkrétní worker ověří, že worker odpovídá přes broker
# (bez odpovědi celery vrací nenulový kód), a zároveň vrátí úlohy s ETA. Pokud je některá
# úloha po ETA déle než 120 s, worker úlohy nezpracovává.
CELERY_APP_PATH="webclient"
WORKER_NAME="worker1@amcr"

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

if [ "$greatest_diff" -lt 120 ]; then
    exit 0
else
    echo "Úloha je $greatest_diff s po ETA."
    exit 1
fi
