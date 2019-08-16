#! /bin/bash

# Load latest commit hash (as pushed from GitHub)
latest_commit_hash="$(cat /var/www/latest_commit_hash)"
latest_commit_hash="1adb4a552945bf16ed3f73facf7e55f9040ae6c4"

# Log in to the Azure CLI
echo "Logging in to the Azure CLI..."
az login --identity  # sign in using the managed identity for this machine

# Retrieve the container registry details from the key vault
echo "Retrieving the container registry details from Azure..."
registry_password=$(az keyvault secret show --vault-name ${key_vault_name} --name ${registry_admin_password_secret} --query "value" -o tsv)
registry_username=$(az keyvault secret show --vault-name ${key_vault_name} --name ${registry_admin_username_secret} --query "value" -o tsv)
# echo "registry_password: $registry_password"
echo "registry_username: $registry_username"

# Retrieve the database details from the key vault
echo "Retrieving the database details from Azure..."
db_admin_password=$(az keyvault secret show --vault-name ${key_vault_name} --name ${db_admin_password_secret} --query "value" -o tsv)
db_admin_username=$(az keyvault secret show --vault-name ${key_vault_name} --name ${db_admin_username_secret} --query "value" -o tsv)
db_server_name=$(az keyvault secret show --vault-name ${key_vault_name} --name ${db_server_name_secret} --query "value" -o tsv)
# echo "db_admin_password: $db_admin_password"
echo "db_admin_username: $db_admin_username"
echo "db_server_name: $db_server_name"

# Log in to the container repository
echo "Logging in to the Azure Container Repository..."
az acr login --name $registry_username

# Get database secrets
database_secrets="{
                        \"host\": \"$db_server_name.postgres.database.azure.com\",
                        \"port\": 5432,
                        \"db_name\": \"inputs_db\",
                        \"username\": \"$db_admin_username@$db_server_name\",
                        \"password\": \"$db_admin_password\",
                        \"ssl_mode\": \"require\"
}"
# echo "database_secrets: $database_secrets"

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
