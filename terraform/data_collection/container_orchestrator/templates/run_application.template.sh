#! /bin/bash

# Load latest commit hash (as pushed from GitHub)
latest_commit_hash="$(cat /var/www/latest_commit_hash)"

# Log in to the Azure CLI
echo "Logging in to the Azure CLI..."
az login --identity  # sign in using the managed identity for this machine

# Retrieve the container registry details from the key vault
echo "Retrieving the container registry details from Azure..."
registry_password=$(az keyvault secret show --vault-name ${key_vault_name} --name ${registry_admin_password_keyname} --query "value" -o tsv)
registry_username=$(az keyvault secret show --vault-name ${key_vault_name} --name ${registry_admin_username_keyname} --query "value" -o tsv)
echo "... registry_username: $registry_username"

# Retrieve the database details from the key vault
echo "Retrieving the database details from Azure..."
db_admin_password=$(az keyvault secret show --vault-name ${key_vault_name} --name ${db_admin_password_keyname} --query "value" -o tsv)
db_admin_username=$(az keyvault secret show --vault-name ${key_vault_name} --name ${db_admin_username_keyname} --query "value" -o tsv)
db_server_name=$(az keyvault secret show --vault-name ${key_vault_name} --name ${db_server_name_keyname} --query "value" -o tsv)
echo "... db_admin_username: $db_admin_username"
echo "... db_server_name:    $db_server_name"

# Retrieve the database details from the key vault
echo "Retrieving the database details from Azure..."
scoot_aws_key_id=$(az keyvault secret show --vault-name ${key_vault_name} --name ${scoot_aws_key_id_keyname} --query "value" -o tsv)
scoot_aws_key=$(az keyvault secret show --vault-name ${key_vault_name} --name ${scoot_aws_key_keyname} --query "value" -o tsv)


# Log in to the container repository
echo "Logging in to the Azure Container Repository..."
az acr login --name $registry_username

# Get database secrets
database_secrets="{
    \"host\": \"$db_server_name.postgres.database.azure.com\",
    \"port\": 5432,
    \"db_name\": \"${db_name}\",
    \"username\": \"$db_admin_username@$db_server_name\",
    \"password\": \"$db_admin_password\",
    \"ssl_mode\": \"require\"
}"

# Get AWS secrets
aws_secrets="{
    \"aws_key_id\": \"$scoot_aws_key_id\",
    \"aws_key\": \"$scoot_aws_key\"
}"


# Run the containers
echo "Running the container instances..."
for datasource in "aqe" "laqn" "scoot"; do
    echo ":: working on $datasource"
    az container create --cpu 1 \
                        --environment-variables NO_TEXT_COLOUR=1 \
                        --image ${registry_server}/$datasource:$latest_commit_hash \
                        --memory 8 \
                        --name $datasource-instance \
                        --registry-password "$registry_password" \
                        --registry-username "$registry_username" \
                        --resource-group ${resource_group} \
                        --restart-policy OnFailure \
                        --secrets db_secrets.json="$database_secrets" aws_secrets.json="$aws_secrets" \
                        --secrets-mount-path /secrets
done
