#! /bin/bash
if [ "$(cat /var/www/update_needed)" == "yes" ]; then
    docker login -u ${username} -p ${password} ${host}
    docker pull ${host}/${datasource}:latest
    echo "" > /var/www/update_needed
fi