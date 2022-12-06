#!/bin/bash
###########
#### SCRIPT: DEPLOYMENT for LOCAL DEV
#### PARAMS: See -h
###########

#USAGE: local deployement for development purposes
#secrets from files, not managed by docker as in swarm mode

# Helper functions
echo_dec ()
{
    echo "---------------------------------------"
    echo "$1"
    echo "---------------------------------------"
}

er () {
    echo_dec "${1}"
    eval "${1}"
    echo "DONE: ${1}"
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

Help ()
{
    cat <<EOF
    !!!MUST BE RUN from REPOSIOTRY root like =>
    usage: ./scrips/dev_deploy.sh [-r|d|s|e], 
    ---
    build and restore db => $./scripts/dev_deploy.sh -d -r other_files/<db_backup_file.tar>
    ---
    stop containers: $./scripts/dev_deploy.sh -e
    start containers: $./scripts/dev_deploy.sh -e
    -----

    -h help
    -r <file_name> => do DB recovery with backup in <file_name>, 
    -x compose down + image prune + container prune
    -d compose-down only, 
    -e stop compose containers
    -s start compose containers (previously stopped)
    -t restart compose containers
EOF
}

echo_dec "# DEPLOYMENT in fro git repository for LOCAL DEVELOPMENT"

# INPUTS
project_name="local"
compose_dev="docker-compose-dev-local-db.yml"

msg_fail_build="!! Command not successfull"
msg_success="Deployed locally ---> APPLICATION ACCESSIBLE on: port 8000"

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

while getopts "hp:f:dxr:est" option; do
   case ${option} in
      h) # display Help
         Help
         exit;;
      d) down_only="yes"
         echo_dec "Compose goes only down"
         er "${cmd_docker_down}"
         ;;         
      x) down_cmd="yes"
         echo_dec "Compose goes down + image prune + container prune (all!!! stopped containers removed)"
         er "${cmd_docker_down}"
         er "yes | docker image prune"
         er "yes | docker container prune"
         ;;
      r) in_file=${OPTARG}
         restore_db="yes"
         echo_dec "DB Restore: ${in_file}"
         er "${cmd_docker_build}${in_file}" && er "${cmd_docker_up}" && echo_dec "${msg_success} project ${project_name}" || echo_dec ${msg_fail_build}
         ;;
      e) stop_services="yes"
         er "${cmd_docker_stop}" && echo_dec "Compose containers stopped / project prefix ${project_name}" || echo_dec ${msg_fail_build} 
         ;;
      s) start_services="yes"
         er "${cmd_docker_start}" && echo_dec "Compose containers started / project prefix ${project_name}" || echo_dec "${msg_fail_build}"
         ;;
      t) restart_services="yes"
         er "${cmd_docker_restart}" && echo_dec "Compose containers going to be restarted / project prefix ${project_name}" || echo_dec ${msg_fail_build} 
         ;;
      
     \?) # Invalid option
         echo "Error: Invalid option ${option}"
         exit;;
   esac
done

unset REVISION_REPO
exit 0
