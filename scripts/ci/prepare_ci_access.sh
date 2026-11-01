#!/usr/bin/env bash
# Volá se přes sudo před spuštěním testů pod odděleným UID.
set -euo pipefail

test_uid=$1
test_gid=$2
checkout=$(realpath "$3")
output=$(realpath "$4")

# Checkout smí testy pouze číst; výsledky patří výhradně testovacímu uživateli.
setfacl -R -m "u:$test_uid:r-X" "$checkout"
chown "$test_uid:$test_gid" "$output"

# GitHub může mít rodiče checkoutu i RUNNER_TEMP v režimu 0700.
# Jmenované ACL povolí pouze průchod, bez výpisu či čtení sourozenců.
for directory in "$checkout" "$output"; do
    parent=$(dirname "$directory")
    while [[ "$parent" != / ]]; do
        setfacl -m "u:$test_uid:--x" "$parent"
        parent=$(dirname "$parent")
    done
done
