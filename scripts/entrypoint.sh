#!/bin/sh

set -e

export DJANGO_SETTINGS_MODULE=webclient.settings.production

python3 manage.py collectstatic --noinput
python3 manage.py makemessages -l cs
python3 manage.py makemessages -l en

uwsgi --socket :8000 \
  --master --enable-threads --module webclient.wsgi
