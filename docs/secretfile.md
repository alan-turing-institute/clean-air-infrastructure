# Secret file for database connection

The connection information for a PostgreSQL database is stored in a JSON "secret" file.
It contains entries for the username, password, host, port, database name and SSL mode.

**Before starting this guide**, please make sure you have [installed the packages](installation.md), [logged into the Azure CLI](azure.md) and read the [developer guide](developer.md).
You may also find it useful to look at our [guide for docker](docker.md).

**The contents of this guide** include:

- Connecting to the [Azure database](#Azure-database)
- Secret file for a local [docker database](#docker-database)
- [Mounting a secret file](#mounting-a-secrets-file) when running a docker file

***

## Azure database

The connection to the Azure database in Azure is managed through the urbanair CLI.
The username and password are generated using the [Azure CLI](azure.md).

***With Turing account***

You can store the connection credentials for the Azure database by running:

```bash
urbanair init production
```

You *should* now be able to connect to the Azure database using the urbanair CLI.
If you would like to get the location of the JSON secret file for the Azure database,
you can run:

```bash
urbanair config path
```

If you would like to get the username and password stored in the Azure JSON secret file, use the `urbanair echo` CLI:

```bash
urbanair echo dbuser
urbanair echo dbtoken
```

***Without Turing account***

We are going to store the settings for the azure database in a JSON file.First, create environment variables to store the location of filepaths and create the hidden `.secrets` directory. We recommend doing this inside the repo.

```bash
cd clean-air-infrastructure
export SECRETS_DIR="$(pwd)/.secrets"
export DB_SECRET_FILE="${SECRETS_DIR}/.db_secrets_azure.json"
mkdir "${SECRETS_DIR}"
```

Next create `.db_secrets_azurer.json`:

```bash
echo '{   
    "host": "cleanair-inputs-2021-server.postgres.database.azure.com",
    "port": 5432,
    "db_name": "cleanair_inputs_db",
    "ssl_mode": "require",
    "username": USERNAME,
    "password": PASSWORD,
}' >> $DB_SECRET_FILE
```

Fill the `USERNAME` and `PASSWORD` apporipiated.fThen run the comand to ???.

```
urbanair init local --secretfile $DB_SECRET_FILE
```

***

## Docker database

> Create a [test docker PostgreSQL database](developer.md#setting-up-a-test-database-with-docker) before starting this section.

We are going to store the settings for the test docker database in a JSON file.
First, create environment variables to store the location of filepaths and create the hidden `.secrets` directory. We recommend doing this inside the repo.

```bash
cd clean-air-infrastructure
export SECRETS_DIR="$(pwd)/.secrets"
export DB_SECRET_FILE="${SECRETS_DIR}/.db_secrets_docker.json"
mkdir "${SECRETS_DIR}"
```

> If using conda, you might like to [save these environment variables](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#saving-environment-variables) so you never have to set them again

Next create `.db_secrets_docker.json`:

```bash
echo '{
    "username": "postgres",
    "password": "",
    "host": "localhost",
    "port": 5432,
    "db_name": "cleanair_test_db",
    "ssl_mode": "prefer"
}' >> $DB_SECRET_FILE
```

***

## Mounting a secrets file

If you are running a docker container and you need the container to connect to the database,
you will need to [mount the directory](https://docs.docker.com/storage/bind-mounts/) `SECRETS_DIR` containing the JSON secret file on the host machine onto a target directory `/secrets` on the container file system.

Add the `-v "${SECRET_DIR}":/secrets` option to any `docker run` commands that need a database connection.

You will also need to *append* the location of the JSON secret file by using the `--secretfile` option for most urbanair CLI commands.

In summary, a docker run command might look something like:

```bash
docker run -v "${SECRET_DIR}":/secrets ... --secretfile /secrets/.db_secrets_docker.json
```

If you don't use the `--secretfile` option for running the command, you *might* also need to add an environment variable that tells the *docker container* about the name of the secrets file by adding `-e DB_SECRET_FILE=".db_secrets_docker.json"`.
