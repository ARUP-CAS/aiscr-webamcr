#!/bin/bash
###########
#### SCRIPT: DEPLOYMENT from local repository into SWARM for testing
#### PARAMS: see -h
###########
#USAGE: deployment based on local repository

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

actualize_repo ()
{

    valid_ans=false

    while [ "$valid_ans" = false ]; do
        
        echo "Do you want to update the local repository to origin/dev first before creating a docker image? (y/n)"   
        read ans

        if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
            echo "Update repository..."
            git fetch origin
            git reset --hard origin/dev
            valid_ans=true
        elif [ "$ans" = "n" ] || [ "$ans" = "N" ]; then
            echo "Continue without update."
            valid_ans=true
        else
            echo "Invalid answer, enter 'y' for yes or 'n' for no."
        fi
    done    
}

run_default ()
{  
    
   in_args="${1}"
   echo_dec "${msg_default_case}"

   actualize_repo
   
   # Check network exists
   check_create_network

   #Update images
   echo_dec "create image"
   er "${cmd_create_images}"
   er "${cmd_create_images_proxy}"

   
    er "${cmd_deploy_base} ${compose_test} ${stack_name}" && \
    echo_dec "$msg_success" || echo_dec "${msg_fail_build}"
    

}

Help ()
{
    cat <<EOF
    !!!MUST BE RUN from REPOSIOTRY root like =>
    usage: ./scrips/${script_name} [-x|b|h], 
    ---
       PURPOSE: manage deployment/run of production docker images build from GIT repository for AIS CR project in SWARM mode
    ----
    DEFAULT CASE: 
      #just call the script without any args => deploy and run all services.
      $./scripts/${script_name}

    Examples on options:
    1) Remove complete docker stack, i.e all services
    
         $./scripts/${script_name} -x  
             
    ---
    2) Deploy or redeploy all services in swarm mode
       
       $./scripts/${script_name} -b   


    -----
    Summnary:
    -h help
    -x remove docker stack (all services)
    -b (re)deploy all services in swarm mode (DEFAULT CASE)
  
EOF
}

script_name=$(basename ${0})
passed_args="$@"


#INPUTS

stack_name="swarm_webamcr"
network_name="prod-net" #MUST MATCH WITH COMPOSE FILES!!!

compose_test="docker-compose-test.yml"

msg_fail_build="!! DEPLOYMENT not successfull"


msg_success="DEPLOYED in SWARM MODE ---> APPLICATION ACCESSIBLE on: port 8080"
msg_default_case="DISCLAIMER: DEFAULT CASE will RE-DEPLOY ALL services again."

#TRANSLATION backups path
tr_path="$HOME/translations_backup"
mkdir -p ${tr_path}

#LOGGING
log_dir="logs/test_deploy"
start_time=$(date +%Y%m%dT%H%M%S)
log_file="${start_time}_test-deployment_${passed_args}.log"
mkdir -p ${log_dir}

OPTIND=1

#REDIRECT to log
exec > >(tee "${log_dir}/${log_file}" )
#exec 2>&1

echo_dec "# DEPLOYMENT in SWARM MODE (i.e. host has to be joined or initiated as SWARM NODE) @${start_time}"

#CHECK SWARM ACTIVATED
docker node ls
status_swarm=$?

if [ $status_swarm -ne 0 ]; then
    echo_dec "SWARM not initiated or joined at this HOST. Exiting"
    exit 1
fi

#Build commands
cmd_stack_rm="docker stack rm ${stack_name}"
cmd_create_images="docker build -t test_prod -f Dockerfile-production --build-arg VERSION_APP=\"$(git rev-parse --short HEAD | head -c 8)\" --build-arg TAG_APP=local_build  ."
cmd_create_images_proxy="docker build -t test_proxy -f proxy/Dockerfile --build-arg VERSION_APP="$(git rev-parse --short HEAD | head -c 8)" --build-arg TAG_APP=local_build  ./proxy"
cmd_deploy_base="docker stack deploy --compose-file"

#Cleaning old images
echo "Pruning unused Docker images..."
docker image prune -f

while getopts "hxbut:d" option; do
   option_passed="yes"
   case ${option} in
      h) # display Help
         echo "OPTION: -h"
         Help
         exit;;
      x) echo "OPTION: -x" 
         echo_dec "Remove docker stack: ${stack_name}"
         if check_stack_exists; then
            er "${cmd_stack_rm}" && \
            er "docker network rm ${network_name}" && \
            echo_dec "Stack ${stack_name} removal successful" || echo_dec "Stack ${stack_name} removal FAILED"
         else
             echo_dec "STACK ${stack_name} doesn't exist so can't be removed!!!"
        fi
        sleep 20 # Need to wait before network is really removed.
         ;;
      b) #deploy stack 
        echo "OPTION: -b"
        run_default b
        ;;
     \?) # Invalid option
         echo_dec "OPTION: INVALID"
         echo "Error: Invalid option ${option}"
         exit;;
   esac
done

# RUN docker compose [default option]
if [ -z ${option_passed+x} ]; then
   echo_dec "NO option passed as ARG so default case is called,"
   run_default
fi

exit 0
