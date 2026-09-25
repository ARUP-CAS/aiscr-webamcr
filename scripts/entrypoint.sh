#!/bin/bash

set -e

export DJANGO_SETTINGS_MODULE=webclient.settings.production

sudo cron

pgq() {
  output=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();")
  text=$(echo "$output" | tail -n 1)
  cislo=$(grep -o '[0-9]\+' <<< "$text")
  echo $cislo
}

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
NEW_DB_NAME="${DB_NAME}_backup_${VERSION}"

DB_EXISTS=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER  -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$NEW_DB_NAME'")

if [ "$DB_EXISTS" = "1" ]; then
    echo "Database already exists: $NEW_DB_NAME"
else
  echo "Creating new database: $NEW_DB_NAME"
  #psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c  "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();" > /dev/null
  counter=0
  cislo=$(pgq)
  echo "Number of using database: $cislo"
  while [[ $cislo -ne 0 && "$counter" -lt 10 ]]; do
    cislo=$(pgq)
    echo "Number of using database: $cislo"
    counter=$((counter+1))
    echo "Counter: $counter"
  done
  echo "Number of iterations: $counter"
  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE \"$NEW_DB_NAME\" WITH TEMPLATE $DB_NAME strategy FILE_COPY;"
  if [ $? -eq 0 ]; then
      echo "New database created successfully: $NEW_DB_NAME"
  else
      echo "Failed to create new database: $NEW_DB_NAME"
      exit 1
  fi

fi

unset PGPASSWORD

python3 manage.py migrate
python3 manage.py collectstatic --noinput --clear
python3 manage.py compress --force
python3 manage.py migrate
python3 manage.py shell < data_management.py
python3 manage.py import_permissions

# copy custom_html to volume nginx_data, preserving existing h1 content
python3 /scripts/copy_custom_html.py

# Seed the runtime catalogs from the image, update them with source message IDs,
# and compile them before the application starts.  The image copy lives outside
# /code so Rosetta discovers only the runtime volume through LOCALE_PATHS.
languages=( "cs" "en" )
default_locale="/default_locale"
volume_locale_root="/vol/web/locale"
code_locale_root="/code/locale"
backup_locale_root="/backup"

for lang_item in "${languages[@]}"; do
  volume_locale="${volume_locale_root}/${lang_item}/LC_MESSAGES"
  code_locale="${code_locale_root}/${lang_item}/LC_MESSAGES"
  default_locale_path="${default_locale}/${lang_item}/LC_MESSAGES/django.po"
  volume_po="${volume_locale}/django.po"

  test -f "${default_locale_path}"
  mkdir -p "${volume_locale}" "${code_locale}"

  if test -f "${volume_po}"; then
    backup_locale="${backup_locale_root}/${lang_item}/LC_MESSAGES"
    test -d "${backup_locale_root}" && test -w "${backup_locale_root}"
    mkdir -p "${backup_locale}"
    backup_timestamp=$(date -u +%Y%m%d%H%M%S)
    cp "${volume_po}" "${backup_locale}/django_backup_${backup_timestamp}.po"
  fi

  find "${code_locale}" -mindepth 1 -maxdepth 1 -type f -delete
  cp "${default_locale_path}" "${code_locale}/django.po"

  echo "#makemessages ${lang_item}"
  python3 manage.py makemessages -l "${lang_item}"
  python3 manage.py compilemessages -l "${lang_item}"

  cp "${code_locale}/django.po" "${volume_locale}/django.po.tmp"
  mv "${volume_locale}/django.po.tmp" "${volume_locale}/django.po"
  cp "${code_locale}/django.mo" "${volume_locale}/django.mo.tmp"
  mv "${volume_locale}/django.mo.tmp" "${volume_locale}/django.mo"
  find "${code_locale}" -mindepth 1 -maxdepth 1 -type f -delete
done

python3 manage.py send_test_emails

sudo uwsgi /scripts/uwsgi_site.ini
