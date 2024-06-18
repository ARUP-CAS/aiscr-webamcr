#!/bin/bash
###########
#### SCRIPT: DEPLOYMENT and BUILD from GIT REPO with existing DB, production setup (i.e. proxy)
#### PARAMS: See -h
###########

#USAGE: ad-hoc deployment from source code on current branch, 
# secrets from file, not managed by docker as in swarm mode
# deploy git compose for production (compose mode only!)

# Helper functions
ask_continue () {
    while true; do
        
        read -p "$1 ==> (y or n): " input        
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

Help ()
{
    cat <<EOF
    !!!MUST BE RUN from REPOSIOTRY root like =>
    usage: ./scrips/${script_name} [-b <service_name | "">|s <service_name | "">|e <service_name | "">|t <service_name | "">|d], 
    ---
       PURPOSE: manage deployment/run of production docker images build from GIT repository for AIS CR project using docker compose.
    ----
    DEFAULT CASE: 
      #just call the script without any args => build and run all services.
      $./scripts/${script_name}

    Examples on options:
    1) build and run selected or all services only => 
         #build and run all services
         $./scripts/${script_name} -b ""  
         or 
         #build and run only web service
         $./scripts/${script_name} -b web 
    
    ---
    2) start all or selected service (previously stopped)=>
       #start all services
       $./scripts/${script_name} -s ""
       or
       #start only service web
       $./scripts/${script_name} -s web
    3) stop all or selected service: $./scripts/${script_name} -e <service_name | "">
    4) restart  all or selected service: $./scripts/${script_name} -t <service_name | "">   
    -----
    5) down all services: $./scripts/${script_name} -d
    -----
    Summnary:
    -h help
    -b build and run selected or all services
    -s start all or selected service (previously stopped)
    -e stop all or selected service
    -t restart all or selected service
    -d down all service

EOF
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

check_file_exist ()
{   
    FILE="$1"
    if [ -f $FILE ]; then
         echo_dec "File $FILE exists."
    else
        echo_dec "!!! File $FILE does not exist. Exiting!"
        exit 1
fi
}

run_default ()
{  
   service_name="${1}"
   echo_dec "${msg_default_case}"
   ask_continue "Do you want to continue with DEFAULT CASE? "
   echo_dec "Build and run without DB restore, selected or all services."
   er "${cmd_docker_build} ${service_name}" && er "${cmd_docker_up} ${service_name}" && echo_dec "${msg_success} project ${project_name} ${service_name}" || echo_dec "${msg_fail_build} ${service_name}"
}


#LOGGING
log_dir="logs/git_prod_deploy"
start_time=$(date +%Y%m%dT%H%M%S)
log_file="${start_time}_git_prod-deployment.log"
mkdir -p ${log_dir}

#REDIRECT to log
exec > >(tee "${log_dir}/${log_file}" )
exec 2>&1

echo_dec "# DEPLOYMENT in from GIT Repository, i.e. building docker images from source code"
script_name=$(basename ${0})

# INPUTS
project_name="git_aiscr"
compose_prod="git_docker-compose-production.yml"
compose_proxy="git_docker-compose-production-proxy.yml"
compose_override="git_docker-compose-production.override.yml"

# !!! Need to be CHECKED UPDATED ACCORDINGLY to point to the same secrets as in docker-compose-dev-local-db.yml
secret_db_conf_1="./secrets.json"
secret_db_conf_2="./secrets.alternative.json"
secret_mail_conf="./secrets_mail_client.json"

check_file_exist ${secret_mail_conf}

msg_fail_build="!! Build not successfull"
msg_success="DEPLOYED from GIT REPO ---> APPLICATION ACCESSIBLE on: port 8081"
msg_default_case="DISCLAIMER: DEFAULT CASE will ONLY build and RUN ALL services again."


# DO SOME MANUAL CHECKS of deployment steps by ASKING questions (can be skipped by providing arbitrary command-line argument to the script)
if [ -z "$1" ]; then

    ask_continue "1.Did you APPLY MANUAL migrations to target DB (if relevant)?"
    ask_continue "2.Did you CONFIGURE secrets to point to desired DB location (using ${secret_db_conf_1} or ${secret_db_conf_2} file in repo root) ?"

    # SELECT OPTION for deployment
    while true; do
        
        read -p "DB secrets PROD (using ${secret_db_conf_1}) / ALTERNATIVE (using overriding compose with ${secret_db_conf_2}) ==> (p/a): " db_secret  
        case $db_secret in
            [pP]*)
                echo "--Using PRODUCTION ${secret_db_conf_1}"
                check_file_exist ${secret_db_conf_1}
                break
                ;;
            [aA]*)
                echo "--Using ALTERNATIVE ${secret_db_conf_2}"
                do_override="yes"
                check_file_exist ${secret_db_conf_2}
                break
                ;;
                *)
                echo '***Invalid input' >&2
        esac
    done

fi 

# GET git revision
git_changes=$(git diff-index $(git write-tree) | wc -l)

if [ ${git_changes} -gt 0 ]; then
    version_suffix="_with_uncommitted"
fi

git_last_tag=$(git describe --tags)
git_revision="${git_last_tag}_$(git rev-parse --short HEAD | head -c 8)${version_suffix}"

echo_dec "REVISION: ${git_revision}"
export REVISION_REPO=${git_revision}

# BUILD docker commands syntax
cmd_docker_base="docker-compose -p ${project_name} -f ${compose_prod} -f ${compose_proxy}"
cmd_docker_base_alt="${cmd_docker_base} -f ${compose_override}"
cmd_docker_build_args="--pull --build-arg VERSION_APP=${git_revision} --build-arg TAG_APP=$(git symbolic-ref HEAD)"


 if [ -z "${do_override}" ]; then 
    cmd_docker_base_used=${cmd_docker_base}
 else
     cmd_docker_base_used=${cmd_docker_base_alt}
fi

# BUILD docker commands syntax
    cmd_docker_build="${cmd_docker_base_used} build ${cmd_docker_build_args}"
    cmd_docker_up="${cmd_docker_base_used} up -d"
    cmd_docker_down="${cmd_docker_base_used} down --remove-orphans"

while getopts "hb:s:e:t:d" option; do
   option_passed="yes"
   case ${option} in
        h) # display Help
         Help
         exit;;
        b) #build and run
           service_name="${OPTARG}"
           run_default ${service_name}
           ;;
        s) # start 
         service_name="${OPTARG}"
         er "${cmd_docker_base_used} start ${service_name}"
         ;;
        e) # stop
         service_name="${OPTARG}"
         er "${cmd_docker_base_used} stop ${service_name}"
         ;;
        t) # restart
         service_name="${OPTARG}"
         er "${cmd_docker_base_used} restart ${service_name}"
         ;;
        d) #compose  down
         er "${cmd_docker_down}" 
         er "docker image prune && docker container prune"
         ;;
       \?) # Invalid option
         echo "Error: Invalid option ${option}"
         exit;;
   esac
done

# RUN docker compose [default option]
if [ -z ${option_passed+x} ]; then
   echo_dec "NO option passed so default case is called,"
   run_default
fi


docker ps
unset REVISION_REPO
exit 0