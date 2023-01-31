#!/bin/bash

set -o errexit
set -o nounset

worker_ready() {
    celery -A webclient inspect ping
}

until worker_ready; do
  >&2 echo 'Celery workers not available'
  sleep 2
done
>&2 echo 'Celery workers is available'

celery -A webclient  \
    --broker=${CELERY_BROKER} \
    flower
