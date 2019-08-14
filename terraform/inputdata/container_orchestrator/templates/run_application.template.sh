#! /bin/bash
latest_commit_hash="$(cat /var/www/latest_commit_hash)"
for datasource in "aqe" "laqn"; do
    az container create --resource-group ${resource_group} \
                        --name $datasource-app \
                        --image ${registry_server}/$datasource:$latest_commit_hash \
                        --registry-login-server ${registry_server} \
                        --registry-username ${registry_username} \
                        --registry-password ${registry_password} \
                        --cpu 1 --memory 1
done
