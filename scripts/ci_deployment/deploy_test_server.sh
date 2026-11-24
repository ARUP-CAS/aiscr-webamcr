#!/bin/bash
set -eo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/../deployment_helpers.sh"

stack_name="swarm_webamcr"

current_deployment_tag="test"
deployment_root="${1}"
ref="${2}"
ref_type="${3}"

if [ -z "${deployment_root}" ]; then
    echo "Error: 'deployment_root' parameter is required." >&2
    exit 1
fi

if [ -z "${ref}" ]; then
    echo "Error: 'ref' parameter is required." >&2
    exit 1
fi

echo "${deployment_root}"
echo "${ref}"
echo "${ref_type}"

init_deployment_log "$deployment_root"
print_d1 "Start script deploy_test_server.sh"

print_d1 "Update repository..."


git fetch origin --prune --prune-tags --tags --force
git clean -fd
git restore .

# Pokud typ reference není předán, automaticky ho zjisti (tag vs. branch)
if [ -z "${ref_type}" ]; then
    if git show-ref --verify --quiet "refs/tags/${ref}"; then
        ref_type="tag"
    else
        ref_type="branch"
    fi
fi

if [ "${ref_type}" = "tag" ]; then
    print_d1 "Deploying TAG ${ref}"
    git checkout --force "refs/tags/${ref}" || exit 1
    git reset --hard "refs/tags/${ref}" || exit 1
else
    print_d1 "Deploying BRANCH ${ref}"
    git checkout -B "${ref}" "origin/${ref}" || exit 1
    git reset --hard "origin/${ref}" || exit 1
fi


#Prints
print_d1 "START DEPLOYMENT SCRIPT @${d_stamp}"

#Docker deployement
chmod +x ${scriptpath}/test_deploy.sh
"${scriptpath}/test_deploy.sh" -x < /dev/null || exit $?
"${scriptpath}/test_deploy.sh" -q < /dev/null || exit $?

#Status check
print_d1 "STATUS CHECK"
python3 "$scriptpath/check_stack_ready.py" "$stack_name" --compose-file docker-compose-test.yml < /dev/null || exit $?

#IN CASE of ERROR reverts
#TBD

#FINAL
print_d1 "Cloning test database"
web_container="$(docker ps -q -f label=com.docker.swarm.service.name=swarm_webamcr_web)"
[[ -n "$web_container" && "$web_container" != *$'\n'* ]] || exit 1
docker exec "$web_container" script -e -q -c "python3 /scripts/db/clone_test_db.py" < /dev/null || exit $?

# Kompakce paměti před testy. Build image a start stacku rozdrobí volnou paměť; bez souvislých
# bloků pak kswapd při testech vyhazuje page cache i při několika GB volné RAM a testy se
# zpomalí (Run tests #169: +11 min). Page cache zůstává, jen se přeskládají stránky.
# /proc/buddyinfo = počet volných bloků podle řádu 0-10 (4 kB až 4 MB) v zóně Normal.
print_d1 "Memory compaction"
grep Normal /proc/buddyinfo || true
# Přes sudo jako volání dockeru výše - zápis do /proc/sys vyžaduje root.
if echo 1 | sudo tee /proc/sys/vm/compact_memory > /dev/null; then
    grep Normal /proc/buddyinfo || true
else
    echo "WARNING: memory compaction failed"
fi

record_deployment_success

print_d1 "EXITING"
