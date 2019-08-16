#! /bin/bash

# Load latest commit hash (as pushed from GitHub)
latest_commit_hash="$(cat /var/www/latest_commit_hash)"
latest_commit_hash="1adb4a552945bf16ed3f73facf7e55f9040ae6c4"

# Log in to the Azure CLI
echo "Logging in to the Azure CLI..."
az login --identity  # sign in using the managed identity for this machine

# Retrieve the container registry details from the key vault
echo "Retrieving the container registry details from Azure..."
registry_username=$(az keyvault secret show --vault-name ${key_vault_name} --name ${registry_admin_username_secret} --query "value" -o tsv)
registry_password=$(az keyvault secret show --vault-name ${key_vault_name} --name ${registry_admin_password_secret} --query "value" -o tsv)
echo "registry_username: $registry_username"
# echo "registry_password: $registry_password"

# Log in to the container repository
echo "Logging in to the Azure Container Repository..."
az acr login --name $registry_username

# Get database secrets
database_secrets="{
                        \"host\": \"inputs-server.postgres.database.azure.com\",
                        \"port\": 5432,
                        \"db_name\": \"inputs_db\",
                        \"username\": \"atiadmin_inputs@inputs-server\",
                        \"password\": \"rjoE6_r13Kq&lQV5\",
                        \"ssl_mode\": \"require\"
}"

# Run the containers
echo "Running the container instances..."
for datasource in "aqe" "laqn"; do
    echo "az container create --resource-group ${resource_group} --name $datasource-app --image ${registry_server}/$datasource:$latest_commit_hash --registry-username \"$registry_username\" --registry-password \"$registry_password\" --cpu 1 --memory 1"
    az container create --resource-group ${resource_group} \
                        --name $datasource-instance \
                        --image ${registry_server}/$datasource:$latest_commit_hash \
                        --registry-username "$registry_username" \
                        --registry-password "$registry_password" \
                        --cpu 1 --memory 1 \
                        --secrets .db_inputs_secret.json="$database_secrets" \
                        --secrets-mount-path /secrets \
                        --restart-policy OnFailure
done
