#! /bin/bash

# Load latest commit hash (as pushed from GitHub)
latest_commit_hash="$(cat /var/www/latest_commit_hash)"

# Log in to the Azure CLI
az login --identity  # sign in using the managed identity for this machine

# Retrieve the container registry details from the key vault
registry_username=$(az keyvault secret show --vault-name ${key_vault_name} --name ${registry_admin_username_secret} --query "value" -o tsv)
registry_password=$(az keyvault secret show --vault-name ${key_vault_name} --name ${registry_admin_password_secret} --query "value" -o tsv)

# Log in to the container repository
az acr login --name $registry_username

# Run the containers
for datasource in "aqe" "laqn"; do
    az container create --resource-group ${resource_group} \
                        --name $datasource-app \
                        --image ${registry_server}/$datasource:$latest_commit_hash \
                        --registry-username "$registry_username" \
                        --registry-password "$registry_password" \
                        --cpu 1 --memory 1
done
