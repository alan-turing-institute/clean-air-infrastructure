#! /bin/bash
latest_commit_hash="$(cat /var/www/update_needed)"
if [ "$latest_commit_hash" != "" ]; then
    # echo ${password} | docker login -u ${username} --password-stdin  ${host}
    # docker pull ${host}/${datasource}:$latest_commit_hash
    # echo "#! /bin/bash" >
    # for datasource in "aqe" "laqn"; do
    #     echo "az container create --resource-group ${resource_group} --name ${datasource}-app --image ${registry_name}.azurecr.io/aqe:${latest_commit_hash} --cpu 1 --memory 1 --registry-login-server ${registry_name}.azurecr.io --registry-username ${registry_username} --registry-password ${registry_password}"
    # done
    # echo "" > /var/www/update_needed
fi