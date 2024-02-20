#!/bin/bash
CELERY_APP_PATH="webclient"

dates=$(celery -A $CELERY_APP_PATH inspect scheduled | grep 'eta' | awk '{print $3}' | tr -d "',")
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

dates=$(celery -A $CELERY_APP_PATH inspect scheduled | grep 'eta' | awk '{print $3}' | tr -d "',")
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
    exit 1
fi
