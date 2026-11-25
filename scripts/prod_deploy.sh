#!/bin/bash
set -eo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/deployment_helpers.sh"
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

run_default ()
{
   echo_dec "# DEPLOYMENT in SWARM MODE (i.e. host has to be joined or initiated as SWARM NODE) @${start_time}"

   #CHECK SWARM ACTIVATED
   require_swarm || return $?
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
   if ! er "${cmd_pull_images}"; then
	echo_dec "${msg_pull_fail} with TAG: ${IMAGE_TAG} => EXITING"
	return 1
   fi

      if er "${cmd_deploy_base} ${compose_proxy} ${stack_name} && \
      ${cmd_deploy_base} ${compose_prod} ${stack_name}"; then
        echo_dec "$msg_success"
      else
        echo_dec "$msg_fail_build"
        return 1
      fi
}

Help ()
{
    cat <<EOF
    Run from the repository root.
    usage: ./scripts/${script_name} [github|dockerhub] [-h|-x|-u <tag_name>|-t <tag_name>|-i]
    ---
       PURPOSE: manage deployment/run of production docker images build from GIT repository for AIS CR project in SWARM mode
    ----

    Examples on options:
    1) Remove complete docker stack, i.e all services
    
         $./scripts/${script_name} -x  
    
    2) Update all services with new images
       
       $./scripts/${script_name} -u <tag_name>

    3) Deploy or redeploy all services in swarm mode with a specific image tag
       
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

# Read the optional registry before parsing the operation flags.
if [[ -n "$1" && "$1" != -* ]]; then
    IMAGE_SOURCE="${1,,}"
    shift
fi
IMAGE_SOURCE="${IMAGE_SOURCE:-github}" # Default to github if not specified
if [[ "$IMAGE_SOURCE" != dockerhub && "$IMAGE_SOURCE" != github ]]; then
    echo "Error: Invalid source type. Use 'dockerhub' or 'github'." >&2
    exit 1
fi

# Validate the entire request before setup or operating on the stack.
options=()
show_help=false
OPTIND=1
while getopts ":hxu:t:i" option; do
    case "$option" in
        \?) printf 'Error: Invalid option -%s\n' "$OPTARG" >&2; exit 1 ;;
        :) printf 'Error: Option -%s requires an image tag\n' "$OPTARG" >&2; exit 1 ;;
        h) show_help=true ;;
        t|u)
            # Distribution reference tag grammar, with the existing latest restriction.
            if [[ ! "$OPTARG" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$ || "$OPTARG" == latest ]]; then
                printf 'Error: Option -%s requires a valid image tag other than latest\n' "$option" >&2
                exit 1
            fi
            # The last supplied tag applies to all selected modes.
            export IMAGE_TAG="$OPTARG"
            options+=("$option")
            ;;
        *) options+=("$option") ;;
    esac
done
if (( OPTIND <= $# )); then
    echo "Error: Unexpected positional argument" >&2
    exit 1
fi
if [[ "$show_help" == true ]]; then
    Help
    exit 0
fi
echo ">>> IMAGE SOURCE: ${IMAGE_SOURCE}"

#INPUTS

# Override image source path based on the chosen source
# Compose image tags (must match how GitHub Actions publish images)
case $IMAGE_SOURCE in
  dockerhub)
    export amcr_image="aiscr/webamcr:${IMAGE_TAG}"
    export proxy_image="aiscr/webamcr-proxy:${IMAGE_TAG}"
    export redis_image="aiscr/webamcr-redis:${IMAGE_TAG}"
    ;;
  github)
    export amcr_image="ghcr.io/arup-cas/aiscr-webamcr:${IMAGE_TAG}"
    export proxy_image="ghcr.io/arup-cas/aiscr-webamcr-proxy:${IMAGE_TAG}"
    export redis_image="ghcr.io/arup-cas/aiscr-webamcr-redis:${IMAGE_TAG}"
    ;;
esac

stack_name="swarm_webamcr"
network_name="prod-net" #MUST MATCH WITH COMPOSE FILES!!!

compose_proxy="docker-compose-proxy.yml"
compose_prod="docker-compose.yml"

msg_fail_build="!! DEPLOYMENT not successfull"
msg_pull_fail="!! PULL not successfull"
msg_success="DEPLOYED in SWARM MODE ---> APPLICATION ACCESSIBLE on: port 8080"

#TRANSLATION backups path
tr_path="$HOME/translations_backup"
mkdir -p ${tr_path}

#LOGGING
log_dir="logs/prod_deploy"
start_time=$(date +%Y%m%dT%H%M%S)
log_file="${start_time}_prod-deployment_${passed_args}.log"
mkdir -p ${log_dir}

#REDIRECT to log
exec > >(tee "${log_dir}/${log_file}" )
exec 2>&1

#Build commands
cmd_pull_images="docker pull ${proxy_image} && docker pull ${amcr_image}"
cmd_deploy_base="docker stack deploy --compose-file"

prune_images (){
#Cleaning old images
echo "Pruning unused Docker images..."
docker image prune -f
}

for option in "${options[@]}"; do
   case ${option} in
      x) echo "OPTION: -x" 
         prune_images
         remove_old_stack || exit $?
        echo sleep 20 second to wait before network is really removed.
        sleep 20 # Need to wait before network is really removed.
         ;;
      u) #update services
        echo "OPTION: -u with ${IMAGE_TAG}"
        prune_images
        echo_dec "Update services with new images!"
        if check_stack_exists ; then
            do_manual_checks
            docker service update --force --image ${amcr_image} ${stack_name}_web && \
            docker service update --force --image ${proxy_image} ${stack_name}_proxy && \
            echo_dec "$msg_success" || { echo_dec "$msg_fail_build"; exit 1; }
        else
            echo_dec "SERVICE CANNOT BE UPDATED because stack doesn't exist !!!"
            exit 1
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
   esac
done

if (( ${#options[@]} == 0 )); then
   echo_dec "No option is passed as ARG, you have to specify a parameter, for help use -h."
fi

exit 0
