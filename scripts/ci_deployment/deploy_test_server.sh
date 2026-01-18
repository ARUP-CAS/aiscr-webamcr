#!/bin/bash

print_d1 () {
    echo "----------------"
    echo "${1}" | tee -a ${logfilepath}
    echo "----------------"

}
print_d1 "Start script deploy_test_server.sh"
stack_name="swarm_webamcr"

current_deployment_tag="test"
deployment_root=${1}
branch=${2}
echo ${deployment_root}
echo ${branch}

d_stamp="$(date +%Y%m%dT%H%M%S)"
logpath="${deployment_root}/logs"
scriptpath="${deployment_root}/scripts"
logfile="deployment_${d_stamp}.log"
logfilepath="${logpath}/${logfile}"
path_last_tag="${logpath}/last_deployment_tag.txt"
last_deployment_tag=$(cat ${path_last_tag})

find "$logpath" -name "$logfile" -type f -mtime +5 -exec rm -f {} \;

mkdir -p ${logpath}

print_d1 "Update repository..."


git fetch origin
git clean -fd
git restore .
git checkout -B ${branch} origin/${branch}
git reset --hard origin/${branch}


#Prints
print_d1 "START DEPLOYMENT SCRIPT @${d_stamp}"

#Docker deployement
chmod +x ${scriptpath}/test_deploy.sh
${scriptpath}/test_deploy.sh -x
${scriptpath}/test_deploy.sh -q

#Status check
print_d1 "STATUS CHECK"
timeout=400         # max čas čekání v sekundách (5 minut)
interval=20          # čas mezi kontrolami
elapsed=0
while true; do
    # Získat seznam kontejnerů se stavem "health: starting"
    unhealthy=$(sudo docker ps --filter "health=starting" --format '{{.ID}}')

    if [ -z "$unhealthy" ]; then
        print_d1 "ALL CONTAINERS ARE HEALTHY"
        break
    fi

    if [ "$elapsed" -ge "$timeout" ]; then
        print_d1 "TIMEOUT Some containers are still not healthy!"
        docker ps --filter "health=starting"
        exit 1
    fi

    print_d1 "Waiting... still unhealthy containers:"
    docker ps --filter "health=starting" --format '→ {{.Names}} ({{.Status}})'

    sleep "$interval"
    elapsed=$((elapsed + interval))
done

#IN CASE of ERROR reverts
#TBD

#FINAL
print_d1 "Cloning test database"
docker exec -i $(docker ps -q -f name=swarm_webamcr_web) script -q -c "python3 /scripts/db/clone_test_db.py"

print_d1 "PUTTING TAG ${current_deployment_tag} as LAST into ${path_last_tag}"
echo "${current_deployment_tag}" > ${path_last_tag}

print_d1 "EXITING"
