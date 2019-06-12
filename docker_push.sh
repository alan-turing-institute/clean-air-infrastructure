#!/bin/bash

# Login to ACR
echo "$ACR_PASSWORD" | docker login -u "$ACR_USERNAME" --password-stdin "$ACR_SERVER"

## Ensure we push for every docker image
# DataSources
docker push "$ACR_SERVER"/laqn:$TRAVIS_PULL_REQUEST_SHA
# docker push "$ACR_SERVER"/AQE:$TRAVIS_PULL_REQUEST_SHA 
# docker push "$ACR_SERVER"/darksky:$TRAVIS_PULL_REQUEST_SHA 
# docker push "$ACR_SERVER"/ECMWF:$TRAVIS_PULL_REQUEST_SHA 