#! /bin/bash
if [ "$(cat /var/www/update_needed)" == "yes" ]; then
    sudo docker login -u ${username} -p ${password} ${host}
    sudo docker pull ${host}/laqn:latest
    echo "" > /var/www/update_needed
fi