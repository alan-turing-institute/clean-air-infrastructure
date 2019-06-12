#!/bin/bash
echo "$ACR_PASSWORD" | docker login -u "$ACR_USERNAME" --password-stdin "$ACR_SERVER"


# Ensure we push for every docker image
docker push "$ACR_SERVER"/laqn:$TRAVIS_PULL_REQUEST_SHA