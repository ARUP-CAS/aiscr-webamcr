#!/bin/bash
###########
#### SCRIPT: DEPLOYMENT from DOCKERHUB into SWARM
#### PARAMS: if some command line argument is provided then control checks are skipped and default option for deployment selected!
###########
#USAGE: deployment based on release on GITHUB, i.e. GitHub actions published docker images

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
    echo "-----------------------------"
    echo "$1"
    echo "-----------------------------"
}



echo_dec "# DEPLOYMENT in SWARM MODE (i.e. host has to be joined or initiated as SWARM NODE)"

#INPUTS
dockerhub_account="huldcz"
prod_image_name="${dockerhub_account}/aiscr_prod"
proxy_image_name="${dockerhub_account}/aiscr_proxy"
stack_name="swarm_aiscr"

compose_proxy="docker-compose-production-proxy.yml"
compose_prod="docker-compose-production.yml"

msg_fail_build="!! DEPLOYMENT not successfull"
msg_pull_fail="!! PULL not successfull"
msg_pull_success="PULL success"
msg_success="DEPLOYED in SWARM MODE ---> APPLICATION ACCESSIBLE on: port 8080"

#CHECK SWARM ACTIVATED
docker node ls
status_swarm=$?

if [ $status_swarm -ne 0 ]; then
    echo_dec "SWARM not initiated or joined at this HOST. Exiting"
    exit 1
fi

# DO SOME MANUAL CHECKS of deployment steps by ASKING questions (can be skipped by providing arbitrary command-line argument to the script)
if [ -z "$1" ]; then
    # DO SOME MANUAL CHECKS of deployment steps by ASKING questions (can be skipped)
    ask_continue "1.Did you APPLY MANUAL migrations to DB (if relevant)?"
    ask_continue "2.Did you MAKE release on GitHUB and waited to for end Github Action for publishing Docker images ?"
    ask_continue "3.Did you CONFIGURE secrets to point to desired DB location (using docker secrets db_conf) ?"

    # SELECT OPTION for deployment
    while true; do
        
        read -p "CHOOSE OPTION OF DEPLOYMENT: (r) RE-DEPLOYMENT or (u) UPDATE ==> (r/u): " option_depl  
        case $option_depl in
            [rR]*)
                echo "--Using RE-DEPLOYMENT"
                option_no=0
                break
                ;;
            [uU]*)
                echo "--Using ROLLING UPDATE"
                option_no=1
                break
                ;;
                *)
                echo '***Invalid input' >&2
        esac
    done
else
    #SKIPPED MANUAL CHECKS and deployment option_no ==> DEFAULT option_no==0
    echo_dec "GOING with DEFAULT OPTION ==> RE-DEPLOYMENT"
    option_no=0

fi

case ${option_no} in
    0)
    #REMOVE stack and REDEPLOY
    docker stack rm ${stack_name}
    docker pull ${proxy_image_name} && docker pull ${prod_image_name} && echo_dec "$msg_pull_success" || echo_dec "$msg_pull_fail"
    docker stack deploy --compose-file ${compose_proxy} ${stack_name} && sleep 30 && echo "...continue..." &&  docker stack deploy --compose-file ${compose_prod} ${stack_name} && echo_dec "$msg_success"
    ;;

    1)
    #UPDATE with new image
    docker service update --force --image ${prod_image_name} ${stack_name}_web && docker service update --image memcached:latest  ${stack_name}_memcached && docker service update --force --image ${proxy_image_name} ${stack_name}_proxy && echo_dec "$msg_success" || echo_dec "$msg_fail_build"
    ;;

    *) echo_dec "INVALID OPTION" >&2
esac

exit 0