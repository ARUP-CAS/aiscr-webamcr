#!/bin/sh

set -e

export DJANGO_SETTINGS_MODULE=webclient.settings.production

sudo cron

python3 manage.py collectstatic --noinput

#Copy locale from volume, create new one/update old, copy locale to volume and remove from app. Move has permission denied.
test -e /vol/web/locale/cs/LC_MESSAGES/django.po && cp /vol/web/locale/cs/LC_MESSAGES/django.po /code/locale/cs/LC_MESSAGES/django.po || echo "CS locale file does not exist will create new one"
test -e /vol/web/locale/en/LC_MESSAGES/django.po && cp /vol/web/locale/en/LC_MESSAGES/django.po /code/locale/en/LC_MESSAGES/django.po || echo "EN locale file does not exist will create new one"

mkdir -p locale/cs/LC_MESSAGES
mkdir -p locale/en/LC_MESSAGES

python3 manage.py makemessages -l cs
python3 manage.py makemessages -l en

cp /code/locale/cs/LC_MESSAGES/django.po /vol/web/locale/cs/LC_MESSAGES/django.po
cp /code/locale/en/LC_MESSAGES/django.po /vol/web/locale/en/LC_MESSAGES/django.po

rm /code/locale/cs/LC_MESSAGES/django.po
rm /code/locale/en/LC_MESSAGES/django.po

uwsgi --socket :8000 \
  --master --enable-threads --module webclient.wsgi
