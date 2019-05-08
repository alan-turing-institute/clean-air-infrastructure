#!/bin/bash
echo "$ACR_PASSWORD" | docker login -u "$ACR_USERNAME" --password-stdin cleanairtestcontainerregistry.azurecr.io

docker push cleanairtestcontainerregistry.azurecr.io/laqn:latest