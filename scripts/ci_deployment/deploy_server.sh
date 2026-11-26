#!/bin/bash

print_d1() {
    echo "----------------"
    echo "${1}" | tee -a "${logfilepath}"
    echo "----------------"
}

image_matches() {
    case "$1" in
        "${expected_image}"|"${expected_image}"@*) return 0 ;;
        "docker.io/${expected_image}"|"docker.io/${expected_image}"@*) return 0 ;;
        *) return 1 ;;
    esac
}

docker_health() {
    local remaining=$((health_deadline - SECONDS)) limit=${health_command_timeout}
    [ "${remaining}" -gt 0 ] || return 1
    if [ "${limit}" -gt "${remaining}" ]; then
        limit=${remaining}
    fi
    timeout "${limit}s" sudo docker "$@"
}

wait_for_candidate_health() {
    local attempt=1 service_id service_image container_id container_service_id container_image health remaining delay
    local health_deadline=$((SECONDS + health_timeout))
    while [ "${attempt}" -le "${health_attempts}" ] && [ "${SECONDS}" -lt "${health_deadline}" ]; do
        service_id=$(docker_health service inspect --format '{{.ID}}' "${web_service}" 2>/dev/null) || service_id=""
        service_image=$(docker_health service inspect --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' "${web_service}" 2>/dev/null) || service_image=""
        if [ -n "${service_id}" ] && image_matches "${service_image}"; then
            while IFS= read -r container_id; do
                [ -n "${container_id}" ] || continue
                case $'\n'"${previous_containers}"$'\n' in
                    *$'\n'"${container_id}"$'\n'*) continue ;;
                esac
                container_service_id=$(docker_health inspect --format '{{index .Config.Labels "com.docker.swarm.service.id"}}' "${container_id}" 2>/dev/null) || continue
                [ "${container_service_id}" = "${service_id}" ] || continue
                container_image=$(docker_health inspect --format '{{.Config.Image}}' "${container_id}" 2>/dev/null) || continue
                image_matches "${container_image}" || continue
                [ "${container_image#docker.io/}" = "${service_image#docker.io/}" ] || continue
                health=$(docker_health inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${container_id}" 2>/dev/null) || continue
                if [ "${health}" = "healthy" ]; then
                    return 0
                fi
            done < <(docker_health ps -q --no-trunc --filter "label=com.docker.swarm.service.name=${web_service}" --filter status=running)
        fi
        remaining=$((health_deadline - SECONDS))
        if [ "${attempt}" -lt "${health_attempts}" ] && [ "${remaining}" -gt 0 ]; then
            delay=${health_interval}
            [ "${delay}" -le "${remaining}" ] || delay=${remaining}
            sleep "${delay}"
        fi
        attempt=$((attempt + 1))
    done
    return 1
}

stack_name="swarm_webamcr"
web_service="${stack_name}_web"
raw_deployment_tag=${1:?Missing deployment tag}
current_deployment_tag="${raw_deployment_tag#v}"
git_deployment_tag="v${current_deployment_tag}"
deployment_root=${2:?Missing deployment root}
image_source=$(printf '%s' "${3:?Missing image source}" | tr '[:upper:]' '[:lower:]')

case "${image_source}" in
    github) expected_image="ghcr.io/arup-cas/aiscr-webamcr:${current_deployment_tag}" ;;
    dockerhub) expected_image="aiscr/webamcr:${current_deployment_tag}" ;;
    *) echo "Invalid image source: ${image_source}" >&2; exit 1 ;;
esac

health_attempts=${WEB_HEALTH_ATTEMPTS:-180}
health_interval=${WEB_HEALTH_INTERVAL_SECONDS:-5}
health_timeout=${WEB_HEALTH_TIMEOUT_SECONDS:-900}
health_command_timeout=${WEB_HEALTH_COMMAND_TIMEOUT_SECONDS:-10}
if ! [[ "${health_attempts}" =~ ^[1-9][0-9]*$ && "${health_interval}" =~ ^[0-9]+$ && \
        "${health_timeout}" =~ ^[1-9][0-9]*$ && "${health_command_timeout}" =~ ^[1-9][0-9]*$ ]]; then
    echo "Invalid web health-check interval or attempt count" >&2
    exit 1
fi

d_stamp="$(date +%Y%m%dT%H%M%S)"
logpath="${deployment_root}/logs"
scriptpath="${deployment_root}/scripts"
logfile="deployment_${d_stamp}.log"
logfilepath="${logpath}/${logfile}"
path_last_tag="${logpath}/last_deployment_tag.txt"

mkdir -p "${logpath}" || exit 1
find "${logpath}" -name "${logfile}" -type f -mtime +5 -exec rm -f {} \;

# Repo update. A failed prerequisite must not be recorded as a successful release.
git stash push -m "CI_autostash_${current_deployment_tag}_${d_stamp}" || exit 1
git fetch --all --tags --force --prune --prune-tags || exit 1
git checkout -f "refs/tags/${git_deployment_tag}" || exit 1

print_d1 "START DEPLOYMENT SCRIPT @${d_stamp}"
print_d1 "DOCKER ROLLING OUT FROM ${image_source} - TAG ${current_deployment_tag}"
previous_containers=$(sudo docker ps -aq --no-trunc --filter "label=com.docker.swarm.service.name=${web_service}") || exit 1
chmod +x "${scriptpath}/prod_deploy.sh" || exit 1
"${scriptpath}/prod_deploy.sh" -x || exit 1
"${scriptpath}/prod_deploy.sh" "${image_source}" -t "${current_deployment_tag}" || exit 1

print_d1 "WAITING FOR CANDIDATE WEB HEALTH"
if ! wait_for_candidate_health; then
    print_d1 "CHECK NOK - candidate health unavailable or timed out; previous tag retained"
    exit 1
fi
print_d1 "CHECK OK"

tag_tmp=$(mktemp "${path_last_tag}.XXXXXX") || exit 1
if ! printf '%s\n' "${current_deployment_tag}" > "${tag_tmp}"; then
    rm -f -- "${tag_tmp}"
    exit 1
fi
if ! mv -f -- "${tag_tmp}" "${path_last_tag}"; then
    rm -f -- "${tag_tmp}"
    exit 1
fi
print_d1 "RECORDED TAG ${current_deployment_tag}"
