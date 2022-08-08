# Secret file for database connection

The connection information for a PostgreSQL database is stored in a JSON "secret" file.
It contains entries for the username, password, host, port, database name and SSL mode.

**Before starting this guide**, please make sure you have [installed the packages](installation.md), [logged into the Azure CLI](azure.md) and read the [developer guide](developer.md).
You may also find it useful to look at our [guide for docker](docker.md) and [mounting a secret file](docker.md#mounting-a-secrets-file).

**The contents of this guide** include:

- Connecting to the [production database](#production-database)
- Secret file for a local [docker database](#docker-database)

***

## Production database

The connection to the production database in Azure is managed through the urbanair CLI.
The username and password are generated using the [Azure CLI](azure.md).
*You do not need to create the secret file for the production database, it is created for you!*

You can store the connection credentials for the production database by running:

```bash
urbanair init production
```

You *should* now be able to connect to the production database using the urbanair CLI.
If you would like to get the location of the JSON secret file for the production database,
you can run:

```bash
urbanair config path
```

If you would like to get the username and password stored in the production JSON secret file, use the `urbanair echo` CLI:

```bash
urbanair echo dbuser
urbanair echo dbtoken
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
