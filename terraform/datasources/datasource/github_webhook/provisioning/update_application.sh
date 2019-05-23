#! /bin/bash
if [ "$(cat /var/www/update_needed)" == "yes" ]; then
    echo ${password} | docker login -u ${username} --password-stdin  ${host}
    docker pull ${host}/${datasource}:latest
    echo "" > /var/www/update_needed
fi