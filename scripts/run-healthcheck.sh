#!/bin/bash

ram_limit=95
disk_limit=95

ram_utilization=$(free | awk '/Mem/{printf("%.2f"), $3/$2*100}')
rounded_ram_utilization=$(printf "%.0f" "$ram_utilization")

if [ "$rounded_ram_utilization" -lt ${ram_limit} ]; then
  echo "RAM utilization is lower than ${ram_limit}% ($ram_utilization%)."
  ram_status=0
else
  echo "RAM utilization is higher than or equal to ${ram_limit}% ($ram_utilization%)."
  ram_status=1
fi

status_code="$(curl -s -L -o /dev/null -w '%{http_code}'  127.0.0.1:8001/healthcheck)"

echo "HTTP status code from /healthcheck endpoint is ${status_code}"

if [ -f "/run/secrets/db_conf" ]; then
    file_path="/run/secrets/db_conf"
else
    file_path="/code/webclient/settings/sample_secrets_db.json"
fi
fedora_server_hostname=$(jq -r '.FEDORA_SERVER_HOSTNAME' "$file_path")
fedora_server_name=$(jq -r '.FEDORA_SERVER_NAME' "$file_path")
fedora_port_number=$(jq -r '.FEDORA_PORT_NUMBER' "$file_path")
fedora_user=$(jq -r '.FEDORA_ADMIN_USER' "$file_path")
fedora_user_password=$(jq -r '.FEDORA_ADMIN_USER_PASSWORD' "$file_path")
fedora_protocol=$(jq -r '.FEDORA_PROTOCOL' "$file_path")

url="${fedora_protocol}://${fedora_server_hostname}:${fedora_port_number}/rest/${fedora_server_name}"
fedora_status_code=$(curl -o /dev/null -s -w "%{http_code}" -u "${fedora_user}":"${fedora_user_password}" "$url")
echo "HTTP status code from FEDORA is ${fedora_status_code}"


test "${status_code}" -eq "200" && test "${fedora_status_code}" -eq "200" && python /scripts/db/db_connection_from_docker-web.py && test ${ram_status} -eq 0 && true || false

exit_code="$?"


if [ ${exit_code} -eq 0 ] ; then
    echo "Django application is running with RAM ${rounded_ram_utilization} %."
    exit 0
else
    echo "Django application is not running or RAM or DISK limits exceeded"
    exit 1
fi