#!/bin/bash

redis-cli -a $(cat /run/secrets/redis_pass) ping 2>1 | grep PONG
result="$?"


if [ ${result} -eq 0 ]; then
  echo "Redis PING OK"
  exit 0
else
  echo "Redis PING FAIL"
  exit 1
fi
