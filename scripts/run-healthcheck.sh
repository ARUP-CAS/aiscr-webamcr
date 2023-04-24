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

disk_utilization=$(df -h | awk '$NF=="/"{printf "%s", $5}' | cut -d'%' -f1)

if [ $disk_utilization -lt ${disk_limit} ]; then
  echo "Disk utilization is lower than ${disk_limit}% ($disk_utilization%)."
  disk_status=0
else
  echo "Disk utilization is higher than or equal to ${disk_limit}% ($disk_utilization%)."
  disk_status=1
fi

status_code="$(curl -s -L -o /dev/null -w '%{http_code}'  127.0.0.1:8001/healthcheck)"

echo "HTTP status code from /healthcheck endpoint is ${status_code}"

test "${status_code}" -eq "200" && python /scripts/db/db_connection_from_docker-web.py && test ${disk_status} -eq 0 && test ${ram_status} -eq 0 && true || false

exit_code="$?"


if [ ${exit_code} -eq 0 ] ; then
    echo "Django application is running with RAM ${rounded_ram_utilization} % and DISK utilization ${disk_utilization}%"
    exit 0
else
    echo "Django application is not running or RAM or DISK limits exceeded"
    exit 1
fi