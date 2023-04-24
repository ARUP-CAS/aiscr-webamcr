
#!/bin/sh

status_code="$(curl -s -L -o /dev/null -w '%{http_code}'  127.0.0.1:8080)"

echo "HTTP status code from proxyt is ${status_code}"

test "${status_code}" -eq "200" && true || false

exit_code="$?"

if [ ${exit_code} -eq 0 ] ; then
    echo "Proxy is RUNNING"
    exit 0
else
    echo "Proxy is not running PROPERLY"
    exit 1
fi