#!/bin/bash
echo "$ACR_PASSWORD" | docker login -u "$ACR_USERNAME" --password-stdin "$ACR_SERVER"

docker push cleanaircontainerregistry.azurecr.io/laqn:$TRAVIS_PULL_REQUEST_SHA