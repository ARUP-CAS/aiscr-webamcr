#!/bin/bash

# Heslo jde přes REDISCLI_AUTH, aby nebylo vidět v /proc/<pid>/cmdline.
REDISCLI_AUTH="$(cat /run/secrets/redis_pass)" redis-cli ping 2>&1 | grep PONG
result="$?"


if [ ${result} -eq 0 ]; then
  echo "Redis PING OK"
  exit 0
else
  echo "Redis PING FAIL"
  exit 1
fi
