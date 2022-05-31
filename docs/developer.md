# Developer guide

**Make sure you have [installed the packages](installation.md) before following this guide.**

This guide describes all the tools you need for developing & contributing to the codebase of the London Air Quality Project.
You may also like to read about the [codebase](codebase.md), [logging into Azure](datasets.md) and [the cheat sheet](cheat.md).

Make sure you have the development dependencies installed:

```bash
pip install -r containers/requirements.txt
```


## Contents
- [Setting up a test database with docker](#setting-up-a-test-database-with-dockersetting-up)
- [Testing](#testing)
- [Linting](#linting)
- [Documentation](#documentation)
- [Developer tools](#developer-tools)
- [Working on an issue](#working-on-an-issue)

***

## Setting up a test database with docker

*When running the python tests, do not use the "production" Azure database*.

Instead, follow these instructions to setup a PostgreSQL database that runs on a docker image.
You will need docker installed.

First build the docker image:

```bash
docker build -t database:latest -f ./containers/dockerfiles/test_database.dockerfile .
```

Now run the database using docker. Note that the port is `5432` and the docker image is tagged as `database`:

```
docker run --name database -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 database
```

### Create a secrets file

We are going to store the settings for the docker database in a JSON file.
First create a hidden directory to store our secrets inside:

```bash
mkdir "$(pwd)/.secrets"
```

Now create a variable `DB_SECRET_FILE` to store the `.db_secrets_docker.json` filepath:

```bash
export DB_SECRET_FILE="$(pwd)/.secrets/.db_secrets_docker.json"
```

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

### Create schema and roles

In your conda environment, run the following command to setup the database schema and assign user roles:

```bash
python containers/entrypoints/setup/configure_db_roles.py -s $DB_SECRET_FILE -c configuration/database_role_config/local_database_config.yaml
```

### Insert static datasets

First [create a SAS token](sas_token.md) and store in the `SAS_TOKEN` variable.
Now download and insert all static data into the database:

```bash
python containers/entrypoints/setup/insert_static_datasets.py insert -t $SAS_TOKEN -s $DB_SECRET_FILE -d rectgrid_100 street_canyon hexgrid london_boundary oshighway_roadlink scoot_detector urban_village
```


### (Not recommended) UKMAP

`UKMAP` is extremly large and will take ~1h to download and insert.
We therefore do not run tests against `UKMAP`.

If you would also like to add `UKMAP` to the database run:

```bash
python containers/entrypoints/setup/insert_static_datasets.py insert -t $SAS_TOKEN -s $DB_SECRET_FILE -d ukmap
```

***

## Testing

We use [pytest](https://docs.pytest.org/en/7.1.x/) for running unit tests of our code.
Each function and class you write should have a test.
You can use [parameterized fixtures](https://docs.pytest.org/en/7.1.x/parametrize.html) to test your function on a wide range of inputs.

Our tests assume you have setup the docker database from the previous section.

> You will need to pass the `DB_SECRET_FILE` variable that points to the [Docker JSON secrets file](#create-a-secrets-file).

Check the docker test database is configured correctly by running:
```bash
pytest containers/tests/test_database_init --secretfile $DB_SECRET_FILE
```

To run the tests in the `cleanair` package:

```bash
pytest containers/tests/test_cleanair --secretfile $DB_SECRET_FILE
```

To run the tests in the `urbanair` API package:

```bash
pytest containers/tests/test_urbanair --secretfile $DB_SECRET_FILE
```

***

## Linting

To keep our code tidy and consistent, we use three linters:

1. [black](https://github.com/psf/black) for formatting code
2. [pylint](https://github.com/PyCQA/pylint) for syntax and potential run-time errors
3. [mypy](https://github.com/python/mypy) for type hinting

If you make changes to the codebase and want to merge your changes into the main branch, the continuous integration (CI) checks will not pass until your code conforms with our linting standards.
Here are some of the more common commands you should run:

```bash
# run black for code formatting
black */

# linting for cleanair package without the mrdgp module
pylint --rcfile=.pylintrc --ignore=mr_dgp,cleanair.egg-info containers/cleanair/*

# type hint the cleanair package
mypy --config-file .mypy.ini containers/cleanair
```

See the `.travis.yml` file for all linting commands that we run during CI.


***

## Documentation
Before being accepted into master all code should have well written documentation.

**Please use [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)**

Please also add documentation about setup and usage instructions into the `docs` directory.

We would like to move towards adding [type hints](https://docs.python.org/3.7/library/typing.html) so you may optionally add types to your code. In which case you do not need to include types in your google style docstrings.

Adding and updating existing documentation is highly encouraged.

*** 

## Developer tools

Here are some useful non-python tools that may be useful for working with the database, Azure, Docker and Kubernetes:

- [PG Admin](https://www.pgadmin.org/download/) for viewing and querying PostgreSQL databases.
- [Lens](https://k8slens.dev/) for interacting with the Kubernetes cluster.
- [Visual Studio Code](https://code.visualstudio.com/) is an IDE with lots of extensions for Docker, python, GitHub, etc.

***
## Working on an issue
The general workflow for contributing to the project is to first choose and issue (or create one) to work on and assign yourself to the issues.

You can find issues that need work on by searching by the `Needs assignment` label. If you decide to move onto something else or wonder what you've got yourself into please unassign yourself, leave a comment about why you dropped the issue (e.g. got bored, blocked by something etc) and re-add the `Needs assignment` label.

You are encouraged to open a pull request earlier rather than later (either a `draft pull request` or add `WIP` to the title) so others know what you are working on.

How you label branches is optional, but we encourage using `iss_<issue-number>_<description_of_issue>` where `<issue-number>` is the github issue number and `<description_of_issue>` is a very short description of the issue. For example `iss_928_add_api_docs`.