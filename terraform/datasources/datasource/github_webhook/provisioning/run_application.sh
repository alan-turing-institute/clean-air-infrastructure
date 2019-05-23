#! /bin/bash
echo ${password} | docker login -u ${username} --password-stdin  ${host}
docker run -v /.secrets:/.secrets/ ${host}/${datasource}:$LATEST_COMMIT_HASH