#!/bin/bash

db_version_tag="${1}"
backup_destination="/home/amcr/db_backups"
backup_main_name="_export_prod_zaloha_"
backup_complete_name="$(date +%Y%m%d%H%M%S)${backup_main_name}${db_version_tag}.tar"
user="cz_archeologickamapa_api"

echo "_________STARTING PG DUMP__________"
pg_dump --dbname=prod_zaloha --host=localhost --port=5432 --format=t --file=/var/lib/pgsql/${backup_complete_name} --username=${user}
mv /var/lib/pgsql/${backup_complete_name} ${backup_destination}/

echo "_________COMPRESSING__________"
gzip --rsyncable ${backup_destination}/*.tar 

echo '______DB DUMP DONE______'