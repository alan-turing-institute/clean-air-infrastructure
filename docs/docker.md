# Docker

This guide walks you through how to build, pull, run and push our docker images.
Before starting this guide:
- [Install docker!](https://docs.docker.com/get-docker/)
- Please make sure you are familiar with the [basic docker principles](https://docs.docker.com/get-started/) before starting this guide.

> You may also be interested in using [docker compose](https://docs.docker.com/compose/gettingstarted/), but that is beyond the scope of this guide.


## Contents

- [Our docker images](#our-docker-images)
- [Pulling a docker image](#pulling) from the [Azure container registry](#azure-container-registry).
- [Building a docker image](#building)
- [Running a docker image](#running)
- [(Optional) Networks of docker containers](#multi-container-networks)

***

## Our docker images


***

## Pulling


### Azure container registry

***

## Building


***

## Running



***

## Pushing


***

## Multi-container networks

> This part of the guide is optional and only recommended for advanced users

A network of docker containers [lets the containers communicate](https://docs.docker.com/get-started/07_multi_container/).
We give the example of inserting static datasets into a PostgreSQL database as described in [the developer guide for setting up a docker PostgreSQL database](developer.md#insert-static-datasets).
Other examples include testing the containerized urbanair API by querying the containerized PostgreSQL database.
 
First, make sure the PostgreSQL `database` container is shut down. Now create a network called `urbanair`:

```bash
export NETWORK=urbanair
docker network create $NETWORK
```

Next, run the docker database [as before](developer.md#insert-static-datasets), but this time add the `--network $NETWORK` argument:

```bash
docker run --network $NETWORK --name database -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 database
```

Check that the database is running using the command: `docker ps`.
You can check the status of the network and **find the `IPv4Address` of the database**:

```bash
docker network inspect $NETWORK
```

Update your secrets file by changing the value of `"host"` to be the IP address above. 
You may like to create a new secret file, in which case you should update the `DB_SECRET_FILE` variable.
Also *check that the port number is correct* and the `SECRET_DIR` variable is set to the `.secrets` directory.

We download the static data and insert into the database using a container called `process_static_datasets`.
Remember you will need to:
1. [Build](#building) or [pull](#pulling) the `process_static_datasets` container 
2. [Mount your secrets file](secretfile.md#mounting-a-secrets-file)
3. [Store a SAS token](sas_token.md) inside a `SAS_TOKEN` variable

Combining it all together, lets insert the static datasets:

```bash
docker run --network $NETWORK -v "${SECRETS_DIR}":/secrets cleanairdocker.azurecr.io/process_static_datasets:latest insert \
    -t $SAS_TOKEN \
    -s /secrets/.db_secrets_docker.json \
    -d street_canyon hexgrid london_boundary oshighway_roadlink scoot_detector
```

> You may also need to add `-e GIT_PYTHON_REFRESH=quiet` if there is an error related to git python!

You can also run a development version of the urbanair API using docker.
It will run on the same docker network and connect to docker database.

```bash
docker run --network $NETWORK -i -p 80:80 -e DB_SECRET_FILE=".db_secrets_docker.json" -e APP_MODULE="urbanair.urbanair:app" -v "${SECRET_DIR}":/secrets urbanairapi:py39
```

You can then query the developer urbanair API, which in turn queries the test docker database!
