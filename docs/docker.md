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

### Mounting a secrets file

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
docker network create urbanair
```

Next, run the database [as before](developer.md#insert-static-datasets), but this time add the `--network urbanair` argument:

```bash
docker run --network urbanair --name database -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 database
```

Check that the database is running using the command: `docker ps`.
You can check the status of the `urbanair` network and **find the `IPv4Address` of the database**:

```bash
docker network inspect urbanair
```

Update your secrets file by changing the value of `"host"` to be the IP address above. Also *check that the port number is correct*.

We download the static data and insert into the database using a container called `process_static_datasets`.
Remember you will need to:
1. [Build](#building) or [pull](#pulling) the `process_static_datasets` container 
2. [Mount your secrets file](#mounting-a-secrets-file)
3. [Store a SAS token](sas_token.md) inside a `SAS_TOKEN` variable

Finally, combining it all together, lets insert the static datasets:

```bash
docker run --network urbanair -v "$(pwd)/.secrets":/app/.secrets cleanairdocker.azurecr.io/process_static_datasets:latest insert \
    -t $SAS_TOKEN \
    -s /app/.secrets/.db_secrets_docker.json \
    -d rectgrid_100 street_canyon hexgrid london_boundary oshighway_roadlink scoot_detector urban_village
```

> You may also need to add `-e GIT_PYTHON_REFRESH=quiet` if there is an error related to git python!