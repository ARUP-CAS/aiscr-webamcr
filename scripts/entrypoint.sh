#!/bin/bash

set -e

export DJANGO_SETTINGS_MODULE=webclient.settings.production

sudo cron

CONFIG_FILE="/run/secrets/db_conf"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

DB_NAME=$(jq -r '.DB_NAME' $CONFIG_FILE)
DB_USER=$(jq -r '.DB_USER' $CONFIG_FILE)
DB_PASS=$(jq -r '.DB_PASS' $CONFIG_FILE)
DB_HOST=$(jq -r '.DB_HOST' $CONFIG_FILE)
DB_PORT=$(jq -r '.DB_PORT' $CONFIG_FILE)

if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASS" ] || [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
    echo "Failed to parse the configuration file or one of the required fields is empty."
    exit 1
fi

export PGPASSWORD=$DB_PASS

IMAGE_TAG=$(curl -s "https://hub.docker.com/v2/repositories/aiscr/webamcr/tags/" | jq -r '.results[1].name')
NEW_DB_NAME="${DB_NAME}_backup_${IMAGE_TAG}"

DB_EXISTS=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER  -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$NEW_DB_NAME'")

if [ "$DB_EXISTS" = "1" ]; then
    echo "Database already exists: $NEW_DB_NAME"
else
  echo "Creating new database: $NEW_DB_NAME"
  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c  "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();" > /dev/null
          
  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE \"$NEW_DB_NAME\" WITH TEMPLATE $DB_NAME;"
  if [ $? -eq 0 ]; then
      echo "New database created successfully: $NEW_DB_NAME"
  else
      echo "Failed to create new database: $NEW_DB_NAME"
      exit 1
  fi

fi

unset PGPASSWORD

python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py compress --force
python3 manage.py migrate
python3 manage.py shell < data_management.py
python3 manage.py set_database_rights
#python3 manage.py update_snapshot_fields

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

sudo uwsgi /scripts/uwsgi_site.ini
