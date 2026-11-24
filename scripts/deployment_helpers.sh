#!/bin/bash
# Shared deployment operations; callers keep their own fail-fast policy.

echo_dec () {
    echo "---------------------------------------"
    echo "--> $1"
    echo "---------------------------------------"
}

er () {
    local ret_val
    echo_dec "${1}"
    if eval "${1}"; then ret_val=0; else ret_val=$?; fi
    echo "....................."
    echo ">> DONE: ${1} with status: ${ret_val}"
    return "$ret_val"
}

check_create_network () {
    if docker network inspect "$network_name" > /dev/null 2>&1; then
        echo_dec "Network ${network_name} already exists"
    else
        er "docker network create -d overlay --attachable ${network_name}" || return $?
        echo_dec "Network ${network_name} created"
    fi
}

check_stack_exists () {
    local stacks name
    stacks="$(docker stack ls --format '{{.Name}}')" || return 2
    while IFS= read -r name; do
        if [[ "$name" == "$stack_name" ]]; then return 0; fi
    done <<< "$stacks"
    return 1
}

require_swarm () {
    if ! docker node ls; then
        echo_dec "SWARM not initiated or joined at this HOST. Exiting"
        return 1
    fi
}

print_d1 () {
    echo "----------------"
    echo "${1}" | tee -a "$logfilepath"
    echo "----------------"
}

init_deployment_log () {
    d_stamp="$(date +%Y%m%dT%H%M%S)"
    logpath="${1}/logs"
    scriptpath="${1}/scripts"
    logfile="deployment_${d_stamp}.log"
    logfilepath="${logpath}/${logfile}"
    path_last_tag="${logpath}/last_deployment_tag.txt"
    mkdir -p "$logpath" || return $?
    find "$logpath" -maxdepth 1 -type f -name 'deployment_*.log' ! -name "$logfile" -mtime +5 -exec rm -f -- {} +
}

record_deployment_success () {
    print_d1 "PUTTING TAG ${current_deployment_tag} as LAST into ${path_last_tag}"
    echo "$current_deployment_tag" > "$path_last_tag"
}
