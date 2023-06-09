#!/bin/bash

set -e

export DJANGO_SETTINGS_MODULE=webclient.settings.production

sudo cron

python3 manage.py collectstatic --noinput
python3 manage.py migrate
python3 manage.py shell < data_management.py

#Copy locale from volume, create new one/update old, copy locale to volume and remove from app. Move has permission denied.

languages=( "cs" "en" )

#Source of locale on persistent volume
volume_locale='/vol/web/locale/${lang_item}/LC_MESSAGES'
code_locale='/code/locale/${lang_item}/LC_MESSAGES'

for lang_item in ${languages[@]}; do
   
  echo "#make dirs $(eval echo ${code_locale})"
  mkdir -p $(eval "echo ${code_locale}")
  
  test -e $(eval "echo ${volume_locale}/django.po") && eval "cp  ${volume_locale}/*.* ${code_locale}/" || echo "${lang_item} locale file does not exist will create new one"
  
  echo "#makemessages ${lang_item}"
  python3 manage.py makemessages -l ${lang_item}
  
  echo "#copy ${lang_item} from tmp path back to persitent volume location"
  eval "cp ${code_locale}/* ${volume_locale}/"

  echo "#remove tmp locale ${lang_item}"
  eval "rm ${code_locale}/*"

done

uwsgi /scripts/uwsgi_site.ini
