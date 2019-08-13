#! /bin/bash
LATEST_COMMIT_HASH="$(cat /var/www/update_needed)"
if [ "$LATEST_COMMIT_HASH" != "" ]; then
    echo ${password} | docker login -u ${username} --password-stdin  ${host}
    docker pull ${host}/${datasource}:$LATEST_COMMIT_HASH
    echo "" > /var/www/update_needed
fi