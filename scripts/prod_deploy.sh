#!/bin/bash
###########
#### SCRIPT: DEPLOYMENT from DOCKERHUB into SWARM
#### PARAMS: see -h
###########
#USAGE: deployment based on release on GITHUB, i.e. GitHub actions published docker images on Docker Hub

# ------ !!!! ----------
SKIP_ALL_CHECKS=1 #IF CHANGED TO 1 then all MANUAL CHECKS, ie questions during script runtime are disabled!
# ------ !!!! ----------

ask_continue () {
    while true; do
        
        read -p "$1 (y or n): " input        
        case $input in
            [yY]*)
                echo '---Continuing!'
                break
                ;;
            [nN]*)
                echo '***So do THAT, exiting!'
                exit 1
                ;;
             *)
                echo '***Invalid input' >&2
        esac
    done
}

echo_dec ()
{
    echo "---------------------------------------"
    echo "--> $1"
    echo "---------------------------------------"
}

er () {
    echo_dec "${1}"
    eval "${1}"
    ret_val=$?
    echo "....................."
    echo ">> DONE: ${1} with status: ${ret_val}"
    return $ret_val
}

check_create_network () {
    
    docker network inspect ${network_name} > /dev/null 2>&1
    network_status=$?
    if [ ${network_status} -eq 1  ]; then
      er "docker network create -d overlay ${network_name}"
      echo_dec "Network ${network_name} created"
    else
       echo_dec "Network ${network_name} already exists"
    fi
}

check_stack_exists ()
{
    docker stack ps ${stack_name} > /dev/null 2>&1
    stack_status=$?
    return ${stack_status}
}

run_default ()
{
   echo_dec "# DEPLOYMENT in SWARM MODE (i.e. host has to be joined or initiated as SWARM NODE) @${start_time}"

   #CHECK SWARM ACTIVATED
   docker node ls
   status_swarm=$?

   if [ $status_swarm -ne 0 ]; then
        echo_dec "SWARM not initiated or joined at this HOST. Exiting"
        exit 1
   fi
   in_args="${1}"
   
   #DISCLAIMER about DEFAULT CASE triggering
   if [ ${SKIP_ALL_CHECKS} -eq 0 ] && [ "${in_args}" == "" ]; then
    ask_continue "Do you want to continue with DEFAULT CASE? "
   fi
   echo_dec "DEPLOY  all services."
   
   #RAISE questions about conditions for deployemnt
   do_manual_checks

   # Check network exists
   check_create_network

   #Update images
   er "${cmd_pull_images}"
   if [ $? -gt 0 ]; then
	echo_dec "${msg_pull_fail} with TAG: ${IMAGE_TAG} => EXITING"
	exit
   fi

      er "${cmd_deploy_base} ${compose_proxy} ${stack_name} && \
      ${cmd_deploy_base} ${compose_prod} ${stack_name}" && \
      echo_dec "$msg_success" || echo_dec "${msg_fail_build}"
}

Help ()
{
    cat <<EOF
    !!!MUST BE RUN from REPOSIOTRY root like =>
    usage: ./scrips/${script_name} [-x|-u <tag_name>|-t <tag_name>|-i], 
    ---
       PURPOSE: manage deployment/run of production docker images build from GIT repository for AIS CR project in SWARM mode
    ----

    Examples on options:
    1) Remove complete docker stack, i.e all services
    
         $./scripts/${script_name} -x  
    
    2) Update all services with new images
       
       $./scripts/${script_name} -u <tag_name>

    3) Deploy or redeploy all services in swarm mode with image tag (version number or "latest")
       
       $./scripts/${script_name} -t <tag_name>

    4) Get information about available versions.

       $./scripts/${script_name} -i

    -----
    Summnary:
    -h help
    -x remove docker stack (all services)
    -u update all services using rolling approach with tag name <tag_name>
    -t deploy all services in swarm mode with tag name <tag_name>
    -i information about available versions

EOF
}

do_manual_checks ()
{
    # DO SOME MANUAL CHECKS of deployment steps by ASKING questions (can be skipped by providing arbitrary command-line argument to the script)
    if [ ${SKIP_ALL_CHECKS} -eq 1 ]; then
        echo_dec "DEPLOYMENT QUESTIONS SKIPPED due to CONSTANT SKIP_ALL_CHECKS set ${SKIP_ALL_CHECKS}"
    else
        # DO SOME MANUAL CHECKS of deployment steps by ASKING questions (can be skipped)
        ask_continue "1.Did you APPLY MANUAL migrations to DB (if relevant)?"
        ask_continue "2.Did you MAKE release on GitHUB and waited to for end Github Action for publishing Docker images ?"
        ask_continue "3.Did you CONFIGURE secrets to point to desired DB location (using docker secrets db_conf, i.e swarm secrets MUST be already existing) ?"
    fi
}

script_name=$(basename ${0})
passed_args="$@"
#export IMAGE_TAG="latest"

while getopts ":t:u:" option; do
    
   case ${option} in
        t|u|d)  #Overriding of default latest image by providing specific tag
            export IMAGE_TAG="${OPTARG}"
            tag_passed="yes"
            echo "IMAGE TAG FOR DOCKER IMAGES IS >>>> ${IMAGE_TAG}"
            ;;
	 *)
            ;;
    esac
done

#INPUTS
dockerhub_account="aiscr"
prod_image_name="${dockerhub_account}/webamcr:${IMAGE_TAG}"
proxy_image_name="${dockerhub_account}/webamcr-proxy:${IMAGE_TAG}"

stack_name="swarm_webamcr"
network_name="prod-net" #MUST MATCH WITH COMPOSE FILES!!!

compose_proxy="docker-compose-production-proxy.yml"
compose_prod="docker-compose-production.yml"

msg_fail_build="!! DEPLOYMENT not successfull"
msg_pull_fail="!! PULL not successfull"
msg_pull_success="PULL success"
msg_success="DEPLOYED in SWARM MODE ---> APPLICATION ACCESSIBLE on: port 8080"

#TRANSLATION backups path
tr_path="$HOME/translations_backup"
mkdir -p ${tr_path}

#LOGGING
log_dir="logs/prod_deploy"
start_time=$(date +%Y%m%dT%H%M%S)
log_file="${start_time}_prod-deployment_${passed_args}.log"
mkdir -p ${log_dir}

OPTIND=1

#REDIRECT to log
exec > >(tee "${log_dir}/${log_file}" )
exec 2>&1

#Build commands
cmd_stack_rm="docker stack rm ${stack_name}"
cmd_pull_images="docker pull ${proxy_image_name} && docker pull ${prod_image_name}"
cmd_deploy_base="docker stack deploy --compose-file"

prune_images (){
#Cleaning old images
echo "Pruning unused Docker images..."
docker image prune -f
}

while getopts "hxu:t:i" option; do
   case ${option} in
      h) # display Help
         echo "OPTION: -h"
         Help
         exit;;
      x) echo "OPTION: -x" 
         prune_images
         echo_dec "Remove docker stack: ${stack_name}"
         if check_stack_exists; then
            er "${cmd_stack_rm}" && \
            er "docker network rm ${network_name}" && \
            echo_dec "Stack ${stack_name} removal successful" || echo_dec "Stack ${stack_name} removal FAILED"
         else
             echo_dec "STACK ${stack_name} doesn't exist so can't be removed!!!"
        fi
        echo sleep 20 second to wait before network is really removed.
        sleep 20 # Need to wait before network is really removed.
         ;;
      u) #update services
        echo "OPTION: -u with ${IMAGE_TAG}"
        prune_images
        echo_dec "Update services with new images!"
        if check_stack_exists ; then
            do_manual_checks
            docker service update --force --image ${prod_image_name} ${stack_name}_web && \
            docker service update --force --image ${proxy_image_name} ${stack_name}_proxy && \
            echo_dec "$msg_success" || echo_dec "$msg_fail_build"
        else
            echo_dec "SERVICE CANNOT BE UPDATED because stack doesn't exist !!!"
        fi
        ;;
      t)
        echo "OPTION: -t with ${IMAGE_TAG}"
        prune_images
        run_default b
	      ;;
      i)
        echo 10 last available versions
        curl -s https://hub.docker.com/v2/repositories/aiscr/webamcr/tags/ | jq '."results"[0:10] | .[]["name"]'
	      ;;
     \?) # Invalid option
         echo_dec "OPTION: INVALID"
         echo "Error: Invalid option ${option}"
         exit;;
   esac
done

if [ -z ${option_passed+x} ]; then
   echo_dec "No option is passed as ARG, you have to specify a parameter, for help use -h."
fi

exit 0