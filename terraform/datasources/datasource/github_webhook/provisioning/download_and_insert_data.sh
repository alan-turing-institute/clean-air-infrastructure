#! /bin/bash
docker login -u ${username} -p ${password} ${host}
docker run -v /.secrets:/.secrets/ ${host}/${datasource}:latest