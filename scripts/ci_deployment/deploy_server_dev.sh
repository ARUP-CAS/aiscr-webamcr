#!/bin/bash

print_d1 () {
    echo "----------------"
    echo "${1}" | tee -a ${logfilepath}
    echo "----------------"

}

stack_name="swarm_webamcr"

current_deployment_tag=${1}
deployment_root=${2}
branch=${3}


d_stamp="$(date +%Y%m%dT%H%M%S)"
logpath="${deployment_root}/logs"
scriptpath="${deployment_root}/scripts"
logfile="deployment_${d_stamp}.log"
logfilepath="${logpath}/${logfile}"
path_last_tag="${logpath}/last_deployment_tag.txt"
last_deployment_tag=$(cat ${path_last_tag})

find "$logpath" -name "$logfile" -type f -mtime +5 -exec rm -f {} \;

mkdir -p ${logpath}

#Repo update
git stash push -m "CI_autostash_${current_deployment_tag}_${d_stamp}"
git checkout ${branch}
git pull


#Prints
print_d1 "START DEPLOYMENT SCRIPT @${d_stamp}"

#Docker deployement
print_d1 "DOCKER ROLLING OUT"
chmod +x ${scriptpath}/prod_deploy.sh
${scriptpath}/prod_deploy.sh -x
if [ ${current_deployment_tag} ]; then
    ${scriptpath}/prod_deploy.sh -t ${current_deployment_tag}
else
    ${scriptpath}/prod_deploy.sh
fi

#Status check
print_d1 "STATUS CHECK"
test $(sudo docker stack ps --filter "desired-state=running" ${stack_name} | wc -l) -eq 5 && true || false
check_state="$?"

if [ ${check_state} -eq 0 ]; then
    print_d1 "CHECK OK"
else
    print_d1 "CHECK NOK - ERROR"
fi

#IN CASE of ERROR reverts
#TBD

#FINAL
print_d1 "PUTTING TAG ${current_deployment_tag} as LAST into ${path_last_tag}"
echo "${current_deployment_tag}" > ${path_last_tag}

print_d1 "EXITING"









