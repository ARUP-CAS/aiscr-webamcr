#!/bin/bash

echo "Pulling repository"
git pull https://github.com/ARUP-CAS/aiscr-webamcr.git dev

proxy_container_name = 'nginx-proxy'
CID=$(docker ps -q -f status=running -f name=^/${proxy_container_name}$)
if [ ! "${CID}" ]; then
  echo "Proxy is not running doesn't exist creating and starting"
  docker-compose -f docker-compose-production-proxy.yml up -d --build
else
  echo "Proxy is already running"
fi

echo "Building new image"
docker-compose -f docker-compose-production.yml up -d --build


