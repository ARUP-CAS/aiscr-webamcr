#!/bin/bash
# start-celery-worker.sh

celery -A webclient worker -l INFO -n worker1@amcr
crontab -u user /scripts/crontab-worker.txt
