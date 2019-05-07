#!/bin/bash
echo "$ACR_PASSWORD" | docker login -u "$ACR_USERNAME" --password-stdin cleanairtestcontainerregistry.azurecr.io

docker build -t cleanairtestcontainerregistry.azurecr.io/laqn:latest scripts/datasources/laqn/.
docker push cleanairtestcontainerregistry.azurecr.io/laqn:latest