#!/bin/bash

set -e

export DJANGO_SETTINGS_MODULE=webclient.settings.production

python3 manage.py collectstatic --noinput

#Copy locale from volume, create new one/update old, copy locale to volume and remove from app. Move has permission denied.

languages=( "cs" "en" )

#Source of locale on persistent volume
volume_locale="/vol/web/locale/"
locale_file="LC_MESSAGES/django.po"
locale_cp_root="/code/locale"

for lang_item in ${languages[@]}; do
  
  vol_locale="${volume_locale}/${lang_item}/${locale_file}"
  cp_path_locale="${locale_cp_root}/${lang_item}/${locale_file}"
  
  echo "#make dirs $(dirname ${cp_path_locale})"
  mkdir -p $(dirname ${cp_path_locale})
  
  test -e ${vol_locale} && cp ${vol_locale} ${cp_path_locale} || echo "${lang_item} locale file does not exist will create new one"
  
  echo "#makemessages ${lang_item}"
  python3 manage.py makemessages -l ${lang_item}
  
  echo "#copy ${lang_item} from tmp path back to persitent volume location"
  cp ${cp_path_locale} ${vol_locale}

  echo "#remove tmp locale ${lang_item}"
  rm ${cp_path_locale}

done

uwsgi --socket :8000 \
  --master --enable-threads --module webclient.wsgi
