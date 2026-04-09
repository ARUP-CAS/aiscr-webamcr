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

REDIS_ADDR="$(cat "$redis_host_file")"
REDIS_PASSWORD="$(cat "$redis_pass_file")"

export REDIS_ADDR
export REDIS_PASSWORD

exec /redis_exporter
