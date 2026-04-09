#!/bin/sh
set -eu

redis_host_file="/run/secrets/redis_host"
redis_pass_file="/run/secrets/redis_pass"

if [ ! -s "$redis_host_file" ]; then
    echo "Missing or empty Redis host secret: $redis_host_file" >&2
    exit 1
fi

if [ ! -s "$redis_pass_file" ]; then
    echo "Missing or empty Redis password secret: $redis_pass_file" >&2
    exit 1
fi

redis_host="$(cat "$redis_host_file")"
redis_pass_encoded=$(python -c 'import sys; from urllib.parse import quote; print(quote(sys.stdin.read().strip()))' < "$redis_pass_file")

CE_BROKER_URL="redis://:${redis_pass_encoded}@${redis_host}"

export CE_BROKER_URL

exec python /app/cli.py
