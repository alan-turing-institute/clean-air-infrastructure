#! /bin/bash
latest_commit_hash="$(cat /var/www/latest_commit_hash)"
az login --identity  # sign in using the managed identity for this machine


# az keyvault secret show --id ${key_vault_id} --name inputs-db-admin-name --query "value"

registry_username=$(az keyvault secret show --id ${key_vault_id} --name inputs-db-admin-name --query "value" -o tsv)
registry_password=$(az keyvault secret show --id ${key_vault_id} --name inputs-db-admin-password --query "value" -o tsv)


for datasource in "aqe" "laqn"; do
    az container create --resource-group ${resource_group} \
                        --name $datasource-app \
                        --image ${registry_server}/$datasource:$latest_commit_hash \
                        --registry-login-server ${registry_server} \
                        --registry-username $registry_username \
                        --registry-password $registry_password \
                        --cpu 1 --memory 1
done
