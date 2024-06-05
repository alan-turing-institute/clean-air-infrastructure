# Secret File for Database Connection

The connection information for a PostgreSQL database is stored in a JSON "secret" file. This file contains entries for the username, password, host, port, database name, and SSL mode.

**Before starting this guide**, ensure you have [installed the necessary packages](installation.md) and read the [developer guide](developer.md). Additionally, refer to our guides on [Docker](docker.md) and [mounting a secret file](docker.md#mounting-a-secrets-file).

**Contents of this Guide:**

- Secret file for a local [Docker database](#docker-database)
- Secret file for a server [Aquifer database](#server-database)

***

## Local Database

We store database credentials in JSON files. **For production databases, never store database passwords in these files. For more information, see the production database section.**

Create the secrets directory and the local database secrets file:

```bash
mkdir -p .secrets
echo '{
    "username": "postgres",
    "password": "",
    "host": "localhost",
    "port": 5432,
    "db_name": "cleanair_test_db",
    "ssl_mode": "prefer"
}' >> .secrets/.db_secrets_offline.json
```

Initialize the local environment:

```bash
urbanair init local --secretfile $DB_SECRET_FILE
```

***

## Docker Database

> **Note:** Create a [test Docker PostgreSQL database](developer.md#setting-up-a-test-database-with-docker) before starting this section.

Store the settings for the test Docker database in a JSON file. First, create environment variables to store the location of file paths and create the hidden `.secrets` directory. It is recommended to do this inside the repository.

```bash
cd clean-air-infrastructure
export SECRETS_DIR="$(pwd)/.secrets"
export DB_SECRET_FILE="${SECRETS_DIR}/.db_secrets_docker.json"
mkdir "${SECRETS_DIR}"
```

> **Tip:** If using Conda, you might want to [save these environment variables](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#saving-environment-variables) to avoid setting them again.

Next, create the `.db_secrets_docker.json` file:

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

## Server Database

Store the settings for the Aquifer PostgreSQL database in a JSON file. First, ensure you have access to the Aquifer server located in the Department of Computer Science at Warwick. Create environment variables to store the location of file paths and create the hidden `.secrets` directory. It is recommended to do this inside the repository.

```bash
cd clean-air-infrastructure
export SECRETS_DIR="$(pwd)/.secrets"
export DB_SECRET_FILE="${SECRETS_DIR}/.db_secrets_aqifer.json"
mkdir "${SECRETS_DIR}"
```

> **Tip:** If using Conda, you might want to [save these environment variables](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#saving-environment-variables) to avoid setting them again.

Next, create the `.db_secrets_aqifer.json` file:

```bash
echo '{
    "username": "postgres",
    "password": "<PASSWORD>",
    "host": "localhost",
    "port": 5432,
    "db_name": "cleanair_inputs_db",
    "ssl_mode": "prefer"
}' >> $DB_SECRET_FILE
```

If you do not have admin access to the Aquifer server or encounter any issues connecting to the database, please contact [Sueda Ciftci](mailto:sueda.ciftci@warwick.ac.uk).

***

## Mounting a Secrets File

When running a Docker container that needs to connect to the database, you must [mount the directory](https://docs.docker.com/storage/bind-mounts/) containing the JSON secret file from the host machine onto a target directory `/secrets` on the container file system.

Add the `-v "${SECRETS_DIR}":/secrets` option to any `docker run` commands that require a database connection.

Additionally, append the location of the JSON secret file using the `--secretfile` option for most Urbanair CLI commands.

A typical Docker run command might look like this:

```bash
docker run -v "${SECRETS_DIR}":/secrets ... --secretfile /secrets/.db_secrets_docker.json
```

If you don't use the `--secretfile` option, you may need to add an environment variable that informs the Docker container about the secrets file by adding `-e DB_SECRET_FILE=".db_secrets_docker.json"`.
