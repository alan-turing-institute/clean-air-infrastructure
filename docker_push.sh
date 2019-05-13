#!/bin/bash
echo "$ACR_PASSWORD" | docker login -u "$ACR_USERNAME" --password-stdin cleanaircontainerregistry.azurecr.io

docker push cleanaircontainerregistry.azurecr.io/laqn:latest