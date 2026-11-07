#!/bin/sh

# Ověřuje jen běh nginx; zdraví Djanga hlídá healthcheck kontejneru web.
# Bez -L a bez průchodu do Djanga, jinak by proxy padala při odstávce (503) nebo výpadku webu (#4417).
status_code="$(curl -s -o /dev/null -w '%{http_code}' 127.0.0.1:8080/nginx-health)"

echo "HTTP status code from proxy is ${status_code}"

test "${status_code}" -eq "200" && true || false

exit_code="$?"

if [ ${exit_code} -eq 0 ] ; then
    echo "Proxy is RUNNING"
    exit 0
else
    echo "Proxy is not running PROPERLY"
    exit 1
fi