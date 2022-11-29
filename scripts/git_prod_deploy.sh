#!/bin/bash
###########
#### SCRIPT: DEPLOYMENT GIT REPO
#### PARAMS: if some command line argument is provided then control checks are skipped!
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

echo_dec ()
{
    echo "---------------------------------------"
    echo "$1"
    echo "---------------------------------------"
}

echo_dec "# DEPLOYMENT in from GIT Repository, i.e. building docker images from source code"

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

# INPUTS
project_name="git_aiscr"
compose_prod="git_docker-compose-production.yml"
compose_proxy="git_docker-compose-production-proxy.yml"
compose_override="git_docker-compose-production.override.yml"

secrets_1="secrets.json"
secrets_2="secrets.local.json"

msg_fail_build="!! Build not successfull"
msg_success="DEPLOYED from GIT REPO ---> APPLICATION ACCESSIBLE on: port 8081"



# DO SOME MANUAL CHECKS of deployment steps by ASKING questions (can be skipped by providing arbitrary command-line argument to the script)
if [ -z "$1" ]; then

    ask_continue "1.Did you APPLY MANUAL migrations to target DB (if relevant)?"
    ask_continue "2.Did you CONFIGURE secrets to point to desired DB location (using ${secrets_1} or ${secrets_2} file in repo root) ?"

    # SELECT OPTION for deployment
    while true; do
        
        read -p "DB secrets PROD (using ${secrets_1}) / LOCAL (using overriding compose with ${secrets_2}) ==> (p/l): " db_secret  
        case $db_secret in
            [pP]*)
                echo "--Using PRODUCTION ${secrets_1}"
                check_file_exist ${secrets_1}
                break
                ;;
            [lL]*)
                echo "--Using LOCAL ${secrets_2}"
                do_override="yes"
                check_file_exist ${secrets_2}
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
cmd_docker_base_ext="${cmd_docker_base} -f ${compose_override}"
cmd_docker_build_args="--pull --build-arg VERSION_APP=${git_revision} --build-arg TAG_APP=$(git symbolic-ref HEAD)"

cmd_docker_build="${cmd_docker_base} build ${cmd_docker_build_args}"
cmd_docker_build_ext="${cmd_docker_base_ext} build ${cmd_docker_build_args}"

cmd_docker_up="${cmd_docker_base} up -d"
cmd_docker_up_ext="${cmd_docker_base_ext} up -d"

cmd_docker_down="${cmd_docker_base} down --remove-orphans"
cmd_docker_down_ext="${cmd_docker_base_ext} down --remove-orphans" 

# BUILD docker commands syntax
 if [ -z "${do_override}" ]; then 


     er "${cmd_docker_down}"
     er "${cmd_docker_build}" && er "${cmd_docker_up}" && echo_dec "$msg_success" || echo "${msg_fail_build}"

 else
     
     er "${cmd_docker_down_ext}"
     er "${cmd_docker_build_ext}" && er "${cmd_docker_up_ext}" && echo_dec "$msg_success" || echo "${msg_fail_build}"

fi

unset REVISION_REPO
exit 0

