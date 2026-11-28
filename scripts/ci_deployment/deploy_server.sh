#!/bin/bash
set -eo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/../deployment_helpers.sh"

stack_name="swarm_webamcr"

raw_deployment_tag=${1}
current_deployment_tag="${raw_deployment_tag#v}"
git_deployment_tag="v${current_deployment_tag}"
deployment_root=${2}
image_source=${3}

init_deployment_log "$deployment_root"

#Repo update
git stash push -m "CI_autostash_${current_deployment_tag}_${d_stamp}"
git fetch --all --tags --force --prune --prune-tags || exit 1
git checkout -f "refs/tags/${git_deployment_tag}" || exit 1


#Prints
print_d1 "START DEPLOYMENT SCRIPT @${d_stamp}"

#Docker deployement
print_d1 "DOCKER ROLLING OUT FROM ${image_source} - TAG ${current_deployment_tag}"
chmod +x ${scriptpath}/prod_deploy.sh
"${scriptpath}/prod_deploy.sh" -x < /dev/null || exit $?
"${scriptpath}/prod_deploy.sh" "${image_source}" -t "${current_deployment_tag}" < /dev/null || exit $?

#Status check
print_d1 "STATUS CHECK"
python3 "$scriptpath/check_stack_ready.py" "$stack_name" --compose-file docker-compose-proxy.yml --compose-file docker-compose.yml < /dev/null || exit $?

#IN CASE of ERROR reverts
#TBD

#FINAL
record_deployment_success

print_d1 "EXITING"
