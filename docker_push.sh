#!/bin/bash

# Build all images
docker build -t $ACR_SERVER/aqe:$TRAVIS_PULL_REQUEST_SHA -f docker/dockerfiles/update_aqe_database.Dockerfile docker/.
docker build -t $ACR_SERVER/laqn:$TRAVIS_PULL_REQUEST_SHA -f docker/dockerfiles/update_laqn_database.Dockerfile docker/.
docker build -t $ACR_SERVER/static:$TRAVIS_PULL_REQUEST_SHA -f docker/dockerfiles/update_static_database.Dockerfile docker/.

# Login to ACR
echo "$ACR_PASSWORD" | docker login -u "$ACR_USERNAME" --password-stdin "$ACR_SERVER"

# Push all our docker images to the container registry
docker push $ACR_SERVER/aqe:$TRAVIS_PULL_REQUEST_SHA
docker push $ACR_SERVER/laqn:$TRAVIS_PULL_REQUEST_SHA
docker push $ACR_SERVER/static:$TRAVIS_PULL_REQUEST_SHA
