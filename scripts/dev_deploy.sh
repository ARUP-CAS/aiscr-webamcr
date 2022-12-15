#!/bin/bash
###########
#### SCRIPT: DEPLOYMENT for LOCAL DEV
#### PARAMS: See -h
###########

#USAGE: local deployment for development purposes
#secrets from files, NOT managed by docker as in swarm mode

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

create_if_absent() {
  FILE="$1"
  if [ ! -f $FILE ]; then
    mkdir -p $(dirname ${FILE})
    touch $FILE
    echo ${default_pass} > $FILE
  fi
}


# Helper functions
echo_dec ()
{
    echo "---------------------------------------"
    echo "--> ${1}"
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


detect_secrets ()
{
   if [ -f "${1}" ]; then
      echo_dec "Secret detected ${1}"
   else
      echo_dec "Secret ${1} is missing!"
      ask_continue "Do you want ${1} to be automatically created with default password content, i.e ${default_pass}, if not => EXIT ? "
      create_if_absent ${1}
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

Help ()
{
    cat <<EOF
    !!!MUST BE RUN from REPOSIOTRY root like =>
    usage: ./scrips/${script_name} [-r [db_restore_file]|b <service_name | "">|x|d|s <service_name | "">|e <service_name | "">|t <service_name | "">], 
    ---
      PURPOSE: manage deployment/run of local development docker images build from GIT repository using docker compose.
    ---
    DEFAULT CASE: 
      #just call the script without any args => build and run all services without DB restore
      >> $./scripts/${script_name}

    Examples on options:
    1) build and run all services with restore db =>  (db backup files available at 192.168.254.30:/home/amcr/db_backups/*.tar)
         $./scripts/${script_name} -d -r <path_to_db_file>/<db_backup_file.tar>
    
    2) build and run selected or all services only => 
         #build and run all services
         $./scripts/${script_name} -b ""  
         or 
         #build and run only db service
         $./scripts/${script_name} -b db 
    ---
    3) down and prune all services (remove all containers): $./scripts/${script_name} -x
    4) down all services: $./scripts/${script_name} -d
    ---
    5) start all or selected service (previously stopped)=>
       #start all services
       $./scripts/${script_name} -s ""
       or
       #start only service web
       $./scripts/${script_name} -s web
    6) stop all or selected service: $./scripts/${script_name} -e <service_name | "">
    7) restart  all or selected service: $./scripts/${script_name} -t <service_name | "">   
    -----
    Summnary:
    -h help
    -r build and run all service with DB restored from <file_name> 
    -b build and run selected or all services
    -x compose down + image prune + container prune all services
    -d down all services
    -s start all or selected service (previously stopped)
    -e stop all or selected service
    -t restart all or selected service

EOF
}

echo_dec "# DEPLOYMENT in from git repository for LOCAL DEVELOPMENT "
script_name=$(basename ${0})

# INPUTS
project_name="local"
compose_dev="docker-compose-dev-local-db.yml"
default_pass="123456"

# !!! Need to be CHECKED UPDATED ACCORDINGLY to point to the same secrets as in docker-compose-dev-local-db.yml
secret_local_db_pass="secrets/local_db_pass"
secret_pg_admin_pass="secrets/pg_admin_pass"
secret_db_conf="./secrets.alternative.json"
secret_mail_conf="./secrets_mail_client.json"

msg_fail_build="!! Command not successfull"
msg_success="Deployed locally ---> APPLICATION ACCESSIBLE on: port 8000"
msg_default_case="DISCLAIMER: DEFAULT CASE assumes that db data ALREADYY exists in docker named-volume ${project_name}_db_dev_data (see compose file definition for volumes and db service) if NOT then local DB will be blank!"

# Detect missing secrets
detect_secrets ${secret_local_db_pass}
detect_secrets ${secret_pg_admin_pass}
check_file_exist ${secret_db_conf}
check_file_exist ${secret_mail_conf}

# GET git revision
git_changes=$(git diff-index $(git write-tree) | wc -l)

if [ ${git_changes} -gt 0 ]; then
    version_suffix="_with_uncommitted"
fi

git_last_tag=$(git describe --tags)
git_revision="${git_last_tag}_$(git rev-parse --short HEAD | head -c 8)${version_suffix}"
git_ref=$(git symbolic-ref HEAD)
echo_dec "REVISION: ${git_revision}"
export REVISION_REPO=${git_revision}

# BUILD docker commands syntax
cmd_docker_base="docker-compose -p ${project_name} -f ${compose_dev}"
cmd_docker_build_args="--pull --build-arg VERSION_APP=${git_revision} --build-arg TAG_APP=${git_ref} --build-arg DB_BACKUP_FILE="

cmd_docker_build="${cmd_docker_base} build ${cmd_docker_build_args}"
cmd_docker_up="${cmd_docker_base} up -d"
cmd_docker_start="${cmd_docker_base} start"
cmd_docker_stop="${cmd_docker_base} stop"
cmd_docker_restart="${cmd_docker_base} restart"
cmd_docker_down="${cmd_docker_base} down --remove-orphans"

while getopts "hr:b:xds:e:t:" option; do
   option_passed="yes"
   case ${option} in
      h) # display Help
         Help
         exit;;
      r) # build and run with restore DB locally from file
         in_file="${OPTARG}"
         restore_db="yes"
         er "${cmd_docker_base} rm -f --stop db"
         er "docker volume rm ${project_name}_db_dev_data"
         echo_dec "Build and run all services with DB Restore: ${in_file}"
         er "${cmd_docker_build}${in_file}" && er "${cmd_docker_up}" && echo_dec "${msg_success} project ${project_name}" || echo_dec ${msg_fail_build}
         ;;
      b) build_and_run="yes"
         service_name="${OPTARG}"
         run_default $service_name
         ;;
      x) down_prune="yes"
         echo_dec "Compose goes down + image prune + container prune (all!!! stopped containers removed)"
         er "${cmd_docker_down}"
         er "yes | docker image prune"
         er "yes | docker container prune"
         ;;
      d) down_only="yes"
         echo_dec "Compose goes only down."
         er "${cmd_docker_down}" && echo_dec "Compose goes down." || echo_dec "Compose down FAILED!.."
         ;;     
      s) start_services="yes"
         service_name="${OPTARG}"
         er "${cmd_docker_start} ${service_name}" && echo_dec "Compose containers started / project prefix ${project_name} ${service_name}" && echo_dec ${msg_success} || echo_dec "${msg_fail_build}"
         ;;
      e) stop_services="yes"
         service_name="${OPTARG}"
         er "${cmd_docker_stop} ${service_name}" && echo_dec "Compose containers stopped / project prefix ${project_name} ${service_name}" && echo_dec ${msg_success} || echo_dec ${msg_fail_build} 
         ;;
      t) restart_services="yes"
         service_name="${OPTARG}"
         er "${cmd_docker_restart} ${service_name}" && echo_dec "Compose containers going to be restarted / project prefix ${project_name} ${service_name}" && echo_dec ${msg_success} || echo_dec ${msg_fail_build} 
         ;;
     \?) # Invalid option
         echo_dec "Error: Invalid option ${option}"
         exit;;
   esac
done

if [ -z ${option_passed+x} ]; then
   echo_dec "NO option passed so default case is called."
   run_default
fi
docker ps

unset REVISION_REPO
exit 0
