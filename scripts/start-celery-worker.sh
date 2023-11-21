#!/bin/bash
# start-celery-worker.sh

sudo crontab -u root /scripts/crontab-worker.txt
celery -A webclient worker -l INFO -n worker1@amcr
