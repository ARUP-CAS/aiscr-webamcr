#!/bin/bash

celery -A webclient inspect ping &> /dev/null
result="$?"


if [ ${result} -eq 0 ]; then
  echo "Celery PING OK"
  exit 0
else
  echo "Celery PING FAIL"
  exit 1
fi
