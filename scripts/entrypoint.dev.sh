#!/bin/bash

python3 manage.py migrate
#python3 manage.py runserver 0.0.0.0:8000
python manage.py shell -c "from cron.tasks import load_news_feed; load_news_feed()"
python3 manage.py runserver_plus --cert-file /cert/amcr-test-local.crt 0.0.0.0:8000
python3 manage.py shell < data_management.py