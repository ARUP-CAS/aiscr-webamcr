#!/bin/bash


#Wrapper for building production image locally
docker build -t test_prod -f Dockerfile-production --build-arg VERSION_APP="$(git rev-parse --short HEAD | head -c 8)" --build-arg TAG_APP=local_build  .
docker build -t test_proxy -f proxy/Dockerfile --build-arg VERSION_APP="$(git rev-parse --short HEAD | head -c 8)" --build-arg TAG_APP=local_build  ./proxy