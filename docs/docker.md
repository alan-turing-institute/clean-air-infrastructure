# Docker

This guide walks you through how to build, pull, run and push our docker images.
Before starting this guide:
- [Install docker!](https://docs.docker.com/get-docker/)
- Please make sure you are familiar with the [basic docker principles](https://docs.docker.com/get-started/) before starting this guide.


## Contents

- [Our docker images](#our-docker-images)
- [Pulling a docker image](#pulling) from the [Azure container registry](#azure-container-registry).
- [Building a docker image](#building)
- [Running a docker image](#running) including [mounting a secret file](#mounting-a-secrets-file)
- [(Optional) Networks of docker containers](#multi-container-networks)

***

## Our docker images

**To generalize this guide**, we use the following environment variables throughout:

```bash
export ACR=cleanairdocker.azurecr.io    # Azure container registry name
export TAG=latest                       # Docker tag
export NAME=cleanair                    # Name of docker file
```

You may also need to get the version of the cleanair/urbanair packages:

```bash
export URBANAIR_VERSION="$(git tag --sort=creatordate | tail -1 | sed 's/^.//')"
```

> Feel free to change the value of `NAME` for different docker files, and change `TAG` to be a specific value. If you are building and running locally on your machine, you may also want to remove the `$ACR` prefix from any commands.

***

## Pulling


Our docker images can be downloaded (pulled) from our Azure container registry.
You will need to be a member of the "UrbanAir" subscription on the Turing Institute's Azure subscription first.

### Azure container registry

To get the username and password for the Azure container registry, first [try this link](https://portal.azure.com/#@turing.ac.uk/resource/subscriptions/ce98e060-eddd-4b54-a33f-b7a6de2ec45c/resourceGroups/RG_CLEANAIR_INFRASTRUCTURE/providers/Microsoft.ContainerRegistry/registries/CleanAirDocker/accessKey).
If the link doesn't work, search for *CleanAirDocker* in the search bar, then navigate to *Access keys* under *Settings*.

Now *on your machine* login to the container registry using docker.
Remember to replace `$DOCKER_USERNAME` and `$DOCKER_PASSWORD` with the relevant fields from the Azure container registry.

```bash
echo $DOCKER_PASSWORD | sudo docker login --password-stdin -u $DOCKER_USERNAME $ACR
```

### Pull from Azure container registry

Now that you have signed into the Azure container registry, you can simply pull the docker container:

```bash
docker pull $ACR/$NAME:$TAG
```

***

## Building

Building a docker file in its simplest form:

```bash
docker build -t $ACR/$NAME:$TAG -f containers/dockerfiles/$NAME.Dockerfile containers
```

If you are building `cleanair`, `urbanair` or `process_static_dataset` you will need to add the additional argument `--build-arg` and remember to [set the environment variables for `URBANAIR_VERSION`](#our-docker-images). For example:

```bash
docker build --build-arg urbanair_version=$URBANAIR_VERSION -t $ACR/$NAME:$TAG -f containers/dockerfiles/$NAME.Dockerfile containers
```



***

## Running

The basic command for running a docker file is:

```bash
docker run $ACR/$NAME:$TAG
```

### Mounting a secrets file

> Look at the [guide to secret files](secretfile.md) before reading this section

If you are running a docker container and you need the container to connect to the database,
you will need to [mount the directory](https://docs.docker.com/storage/bind-mounts/) `SECRETS_DIR` containing the JSON secret file on the host machine onto a target directory `/secrets` on the container file system.

Add the `-v "${SECRET_DIR}":/secrets` option to any `docker run` commands that need a database connection.

You will also need to *append* the location of the JSON secret file by using the `--secretfile` option for most urbanair CLI commands.

In summary, a docker run command might look something like:

```bash
docker run -v "${SECRET_DIR}":/secrets ... --secretfile /secrets/.db_secrets_docker.json
```

If you don't use the `--secretfile` option for running the command, you *might* also need to add an environment variable that tells the *docker container* about the name of the secrets file by adding `-e DB_SECRET_FILE=".db_secrets_docker.json"`.

***

## Pushing

If you are signed into [the Azure container registry](#azure-container-registry),
then simply run:

```bash
docker push $ACR/$NAME:$TAG
```

***

## Multi-container networks

> This part of the guide is optional and only recommended for advanced users. Advances users may also be interested in using [docker compose](https://docs.docker.com/compose/gettingstarted/).

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
docker run --network $NETWORK -v "${SECRETS_DIR}":/secrets $ACR/process_static_datasets:$TAG insert \
    -t $SAS_TOKEN \
    -s /secrets/.db_secrets_docker.json \
    -d street_canyon hexgrid london_boundary oshighway_roadlink scoot_detector
```

> You may also need to add `-e GIT_PYTHON_REFRESH=quiet` if there is an error related to git python!

You can also run a development version of the urbanair API using docker.
It will run on the same docker network and connect to docker database.

```bash
docker run --network $NETWORK -i -p 80:80 \
    -e DB_SECRET_FILE=".db_secrets_docker.json" \
    -e APP_MODULE="urbanair.urbanair:app" \
    -v "${SECRET_DIR}":/secrets \
    $ACR/urbanairapi:$TAG
```

You can then query the developer urbanair API, which in turn queries the test docker database!
