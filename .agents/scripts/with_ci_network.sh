#!/usr/bin/env bash
# Izolace testovacího uživatele na jednorázovém Linux runneru; neovlivní Actions agenta.
set -euo pipefail

suite=$1
output=$2
python_bin=$3
case "$suite" in fast|database) ;; *) exit 2 ;; esac

test_user=amcr-ci-tests
chain="AMCR_CI_$$"
sudo -n useradd --system --uid 20000 --user-group --no-create-home "$test_user"
test_uid=$(id -u "$test_user")
test_gid=$(id -g "$test_user")
mkdir -p "$output"
output=$(realpath "$output")
sudo -n chown "$test_uid:$test_gid" "$output"

cleanup() {
    result=$?
    trap - EXIT
    for firewall in iptables ip6tables; do
        sudo -n "$firewall" -w -D OUTPUT -m owner --uid-owner "$test_uid" -j "$chain" 2>/dev/null || true
        sudo -n "$firewall" -w -F "$chain" 2>/dev/null || true
        sudo -n "$firewall" -w -X "$chain" 2>/dev/null || true
    done
    exit "$result"
}
trap cleanup EXIT

for firewall in iptables ip6tables; do
    sudo -n "$firewall" -w -N "$chain"
done

# Docker může provést DNAT před filtrem OUTPUT, proto povolíme i přesné IP služeb.
for address in 127.0.0.1 ${AMCR_CI_SERVICE_IPS:-}; do
    [[ "$address" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 2
    sudo -n iptables -w -A "$chain" -d "$address" -p tcp -m multiport --dports 5432,6379 -j ACCEPT
done
sudo -n ip6tables -w -A "$chain" -d ::1 -p tcp -m multiport --dports 5432,6379 -j ACCEPT
for firewall in iptables ip6tables; do
    sudo -n "$firewall" -w -A "$chain" -j REJECT
    sudo -n "$firewall" -w -I OUTPUT 1 -m owner --uid-owner "$test_uid" -j "$chain"
done

rejected_packets() {
    for firewall in iptables ip6tables; do
        sudo -n "$firewall" -w -L "$chain" -n -v -x
    done | awk '$3 == "REJECT" { total += $1 } END { print total+0 }'
}

# Ověření fail-closed před importem aplikace, bez DNS a bez odeslání ven.
sudo -n setpriv --reuid="$test_uid" --regid="$test_gid" --init-groups --no-new-privs --bounding-set=-all \
    "$python_bin" -c 'import socket; s=socket.socket(); s.settimeout(1); assert s.connect_ex(("127.0.0.1", 9)) != 0'
[[ $(rejected_packets) -gt 0 ]] || { echo 'Firewall verification failed'; exit 1; }
for firewall in iptables ip6tables; do
    sudo -n "$firewall" -w -Z "$chain"
done

result=0
sudo -n env \
    "AMCR_CI_DB_NAME=${AMCR_CI_DB_NAME:-amcr_ci}" \
    "AMCR_CI_DB_USER=${AMCR_CI_DB_USER:-amcr_ci}" \
    "AMCR_CI_DB_PASSWORD=${AMCR_CI_DB_PASSWORD:-ci-only-password}" \
    setpriv --reuid="$test_uid" --regid="$test_gid" --init-groups --no-new-privs --bounding-set=-all \
    "$python_bin" .agents/scripts/run_django_ci.py --suite "$suite" --output-dir "$output" || result=$?

blocked=$(rejected_packets)
if [[ "$blocked" -gt 0 ]]; then
    printf '\n## FAIL: firewall blocked %s forbidden network packets\n' "$blocked" >> "$output/summary.md"
    result=1
fi
exit "$result"
