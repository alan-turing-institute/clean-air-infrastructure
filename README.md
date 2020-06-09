# UrbanAir API - Repurposed as London Busyness COVID-19
[![Build Status](https://dev.azure.com/alan-turing-institute/clean-air-infrastructure/_apis/build/status/alan-turing-institute.clean-air-infrastructure?branchName=master)](https://dev.azure.com/alan-turing-institute/clean-air-infrastructure/_build/latest?definitionId=1&branchName=master)
[![Build Status](https://travis-ci.com/alan-turing-institute/clean-air-infrastructure.svg?token=zxQwzfsqCyEouTqXAVUn&branch=master)](https://travis-ci.com/alan-turing-institute/clean-air-infrastructure)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Azure Infrastructure for the [Clean Air project](https://www.turing.ac.uk/research/research-projects/london-air-quality). 

Provides 48h high-resolution air pollution forecasts over London via the [UrbanAir-API](https://urbanair.turing.ac.uk/apidocs/).

Currently repurposed to assess `busyness` in London during the COVID-19 pandemic - providing busyness data via the [ip-whitelisted API](https://urbanair.turing.ac.uk/apidocs/).


# Contributors :dancers:

A list of key developers on the project. A good place to start if you wish to contribute.

| Name               | GitHub ID                                            | Email                     | Admin  |
| ------------------ | -----------------------------------------------------| ------------------------- | ------ |
| Oscar Giles        | [@OscartGiles](https://github.com/OscartGiles)       | <ogiles@turing.ac.uk>     | Infrastructure, Prod Database, Kubernetes Cluster
| Oliver Hamelijnck  | [@defaultobject](https://github.com/defaultobject)   | <ohamelijnck@turing.ac.uk>|      
| Chance Haycock     | [@chancehaycock](https://github.com/chancehaycock)   | <chaycock@turing.ac.uk>   |
| Christy Nakou      | [@ChristyNou](https://github.com/ChristyNou)        | <cnakou@turing.ac.uk>     | 
| Patrick O'Hara     | [@PatrickOHara](https://github.com/PatrickOHara)     | <pohara@turing.ac.uk>     | 
| David Perez-Suarez | [@dpshelio](https://github.com/dpshelio)             | <d.perez-suarez@ucl.ac.uk>|
| James Robinson     | [@jemrobinson](https://github.com/jemrobinson)       | <jrobinson@turing.ac.uk>  | 
| Tim Spain          | [@timspainUCL](https://github.com/timspainUCL)       | <t.spain@ucl.ac.uk>       |


# Contents

### Setting up a development environment
- [Azure account](#azure-account)
- [Non-infrastructure dependencies](#non-infrastructure-dependencies)
- [Infrastructure dependencies](#infrastructure-dependencies)
- [Login to Azure](#login-to-azure)
- [Configure a local database](#configure-a-local-database) 
- [Insert static datasets into local database](#static-data-insert)
- [Configure schema and database roles](#create-schema-and-roles)


### Accessing Production database
- [Access CleanAir Production Database](#access-cleanair-production-database)
- [Connect with psql](#connect-using-psql)
- [Create a production secretfile](#create-secret-file-to-connect-using-CleanAir-package)

### Entry points
- [Running Entry points](#running-entry-points)
- [Entry point with local database](#entry-point-with-local-database)
- [Entry point with production database](#entry-point-with-production-database)

### UrbanAir Flask API
- [Running the UrbanAir API](#urbanAir-API)

### Developer guide
- [Style guide](#style-guide)
- [Running tests](#running-tests)
- [Writing tests](#writing-tests)

### Infrastructure

- [Infrastructure Deployment](#infrastructure-deployment)



---

# Contributing guide

## Azure account
To contribute to the Turing deployment of this project you will need to be on the Turing Institute's Azure active directory. In other words you will need a turing email address `<someone>@turing.ac.uk`. If you do not have one already contact an [infrastructure administrator](#contributors-:dancers:).

If you are deploying the CleanAir infrastrucure elsewhere you should have access to an Azure account (the cloud-computing platform where the infrastructure is deployed).


## Non-infrastructure dependencies 

To contribute as a non-infrastructure developer you will need the following:

- `Azure command line interface (CLI)` (for managing your Azure subscriptions)
- `Docker` (For building and testing images locally)
- `postgreSQL` (command-line tool for interacting with db)
- `CleanAir python packages` (install python packages)
- `GDAL` (For inserting static datasets)

The instructions below are to install the dependencies system-wide, however you can
follow the [instructions at the end if you wish to use an anaconda environment](#with-a-Conda-environment)
if you want to keep it all separated from your system.

Windows is not supported. However, you may use [Windows Subsystem for Linux 2](https://docs.microsoft.com/en-us/windows/wsl/install-win10) and then install dependencies with [conda](#with-a-conda-environment).

### Azure CLI
If you have not already installed the command line interface for `Azure`, please [`follow the procedure here`](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) to get started

<details>
<summary>Or follow a simpler option</summary>
Install it using on your own preferred environment with `pip install azure-cli`
</details>

### Docker
Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop)

### PostgreSQL

[PostgreSQL](https://www.postgresql.org/download) and [PostGIS](https://postgis.net/install).

```bash
brew install postgresql postgis
```

### GDAL

[GDAl](https://gdal.org/) can be installed using `brew` on a mac
```bash
brew install gdal
```

or any of the [binaries](https://gdal.org/download.html#binaries) provided for different platforms.


### Development tools
The following are optional as we can run everything on docker images. However, they are recommended for development/testing and required for setting up a local copy of the database. 

```bash
pip install -r containers/requirements.txt
```

### CleanAir Python packages
To run the CleanAir functionality locally (without a docker image) you can install the package with `pip`. 

For a basic install which will allow you to set up a local database run:

```bash
pip install -e 'containers/cleanair[<optional-dependencies>]'
```

Certain functionality requires optional dependencies. These can be installed by adding the following:

| Option keyword   | Functionality               |
| ------------------ | --------------------------- |
| models             | CleanAir GPFlow models      |
| traffic            | FBProphet Trafic Models     |
| dashboards         | Model fitting Dashboards    |

For getting started we recommend:

```bash
pip install -e 'containers/cleanair[models, traffic, dashboard]'
```

### UATraffic (London Busyness only)
All additional  functionality related to the London Busyness project requires:
```bash
pip install -e 'containers/odysseus'
```

### UrbanAir Flask API package
```bash
pip install -e 'containers/urbanair'
```

--- 

## Infrastructure dependencies
Cloud infrastructure developers will require the following in addition to the [non-infrastructure dependencies](#Non-infrastructure-development-:sparkles:).

### Infrastructure development
- `Access to the deployment Azure subscription`
- `Terraform` (for configuring the Azure infrastructure)
- `Travis Continuous Integration (CI) CLI` (for setting up automatic deployments)

### Azure subscription
You need to have access to the CleanAir Azure subscription to deploy infrastructure. If you need access contact an [infrastructure administrator](#contributors-:dancers:)

### Terraform 
The Azure infrastructure is managed with `Terraform`. To get started [download `Terraform` from their website](https://www.terraform.io). If using Mac OS, you can instead use `homebrew`:

```bash
brew install terraform
```

### Travis CI CLI
Ensure you have Ruby 1.9.3 or above installed:
```bash
brew install ruby
gem update --system
```

Then install the Travis CI CLI with:
```bash
gem install  travis -no-rdoc -no-ri
```

On some versions of OSX, this fails, so you may need the following alternative:
```
ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future gem install --user-install travis -v 1.8.13 --no-document
```

Verify with
```bash
travis version
```

If this fails ensure Gems user_dir is on the path:
```
cat << EOF >> ~/.bash_profile
export PATH="\$PATH:$(ruby -e 'puts Gem.user_dir')/bin"
EOF
```

### With a Conda environment

It's possible to set it up all with a conda environment, this way you can keep different
versions of software around in your machine. All the steps above can be done with:

```bash
# Non-infrastructure dependencies

conda create -n busyness python=3.7
conda activate busyness
conda install -c anaconda postgresql
conda install -c conda-forge gdal postgis uwsgi
pip install azure-cli
pip install azure-nspkg azure-mgmt-nspkg
# The following fails with: ERROR: azure-cli 2.6.0 has requirement azure-storage-blob<2.0.0,>=1.3.1, but you'll have azure-storage-blob 12.3.0 which is incompatible.
# but they install fine.
pip install -r containers/requirements.txt
pip install -e 'containers/cleanair[models, dashboard]'
pip install -e 'containers/odysseus'
pip install -e 'containers/urbanair'

## Infrastructure dependencies

# if you don't get rb-ffi and rb-json you'll need to install gcc_linux-64 and libgcc to build these in order to install travis.
conda install -c conda-forge terraform ruby rb-ffi rb-json
# At least on Linux you'll need to dissable IPV6 to make this version of gem to work.
gem install  travis -no-rdoc -no-ri
# Create a soft link of the executables installed by gem into a place seen within the conda env.
conda_env=$(conda info --json | grep -w "active_prefix" | awk '{print $2}'| sed -e 's/,//' -e 's/"//g')
ln -s $(find $conda_env -iname 'travis' | grep bin) $conda_env/bin/
```


## Login to Azure

To start working with `Azure`, you must first login to your account from the terminal:
```bash
az login
```

### Infrastructure developers:

Infrastructure developers should additionally check which `Azure` subscriptions you have access to by running
```bash
az account list --output table --refresh
```

Then set your default subscription to the Clean Air project (if you cannot see it in the output generated from the last line you do not have access):
```bash
az account set --subscription "CleanAir"
```

If you don't have access this is ok. You only need it to deploy and manage infrastructure. 

## Configure a local database
In production we use a managed [PostgreSQL database](https://docs.microsoft.com/en-us/azure/postgresql/). However, it is useful to have a local copy to run tests and for development. To set up a local version start a local postgres server:

```bash 
brew services start postgresql   
```

<details>
<summary> If you installed the database using conda </summary>

Set it up the server and users first with:

```bash
initdb -D mylocal_db
pg_ctl -D mylocal_db -l logfile start
createdb --owner=${USER} myinner_db
```

When you want to work in this environment again you'll need to run:
```bash
pg_ctl -D mylocal_db -l logfile start
```

You can stop it with:
```bash
pg_ctl -D mylocal_db stop
```
</details>

### Create a local secrets file
We store database credentials in json files. **For production databases you should never store database passwords in these files - for more information see the production database section**. 

```bash
mkdir -p .secrets
echo '{
    "username": "postgres",
    "password": "''",
    "host": "localhost",
    "port": 5432,
    "db_name": "cleanair_test_db",
    "ssl_mode": "prefer"
}' >> .secrets/.db_secrets_offline.json
```

N.B In some cases your default username may be your OS user. Change the username in the file above if this is the case.

```bash
createdb cleanair_test_db
```

### Create Schema and roles

We must now setup the database schema. This also creates a number of roles on the database.

Create a variable with the location of your secrets file

```bash
SECRETS=$(pwd)/.secrets/.db_secrets_offline.json
```

```bash
python containers/entrypoints/setup/configure_db_roles.py -s $SECRETS -c configuration/database_role_config/local_database_config.yaml   
```

### Static data insert

The database requires a number of static datasets. We can now insert `static data` into our local database. You will need a [SAS token](https://docs.microsoft.com/en-us/azure/storage/common/storage-sas-overview) to access static data files stored on Azure. 

If you have access Azure you can log in to Azure from the [command line](#login-to-Azure) and run the following to obtain a SAS token:

```bash
SAS_TOKEN=$(python containers/entrypoints/setup/insert_static_datasets.py generate)
```

By default the SAS token will last for 1 hour. If you need a longer expiry time pass `--days` and `--hours` arguments to the program above. N.B. It's better to use short expiry dates where possible. 

Otherwise you must request a SAS token from an [infrastructure developer](#contributors-:dancers:) and set it as a variable:

```bash
SAS_TOKEN=<SAS_TOKEN>
```

You can then download and insert all static data into the database by running the following:

```bash
python containers/entrypoints/setup/insert_static_datasets.py insert -t $SAS_TOKEN -s $SECRETS -d rectgrid_100 street_canyon hexgrid london_boundary oshighway_roadlink scoot_detector urban_village
```

If you would also like to add `UKMAP` to the database run:

```bash
python containers/entrypoints/setup/insert_static_datasets.py insert -t $SAS_TOKEN -s $SECRETS -d ukmap
```

`UKMAP` is extremly large and will take ~1h to download and insert. We therefore do not run tests against `UKMAP` at the moment. 

N.B SAS tokens will expire after a short length of time, after which you will need to request a new one. 



### Check the database configuration

You can check everything configured correctly by running:

```bash
pytest containers/tests/test_database_init --secretfile $SECRETS
```


# Access CleanAir Production Database

To access the production database you will need an Azure account and be given access by one of the [database adminstrators](#contributors-:dancers:). You should discuss what your access requirements are (e.g. do you need write access).To access the database first [login to Azure](#login-to-Azure) from the terminal. 

You can then request an access token. The token will be valid for between 5 minutes and 1 hour. Set the token as an environment variable:

```bash
export PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)
```

## Connect using psql

Once your IP has been whitelisted (ask the [database adminstrators](#contributors-:dancers:)), you will be able to
access the database using psql:

```bash
psql "host=cleanair-inputs-server.postgres.database.azure.com port=5432 dbname=cleanair_inputs_db user=<your-turing-credentials>@cleanair-inputs-server sslmode=require"
```
replacing `<your-turing-credentials>` with your turing credentials (e.g. `jblogs@turing.ac.uk`).

## Create secret file to connect using CleanAir package

To connect to the database using the CleanAir package you will need to create another secret file:

```bash
echo '{
    "username": "<your-turing-credentials>@cleanair-inputs-server",
    "host": "cleanair-inputs-server.postgres.database.azure.com",
    "port": 5432,
    "db_name": "cleanair_inputs_db",
    "ssl_mode": "require"
}' >> .secrets/db_secrets_ad.json
```

Make sure you then replace `<your-turing-credentials>` with your full Turing username (e.g.`jblogs@turing.ac.uk@cleanair-inputs-server`).

# Running entry points

The directory [containers/entrypoints](containers/entrypoints) contains Python scripts which are then built into Docker images in  [containers/dockerfiles](containers/dockerfiles). You can run them locally. 


These are scripts which collect and insert data into the database. To see what arguments they take you can call any  of the files with the argument `-h`, for example:

```bash 
python containers/entrypoints/inputs/input_laqn_readings.py -h
```

### Entry point with local database

The entrypoints will need to connect to a database. To do so you can pass one or more of the following arguments:

1. `--secretfile`: Full path to one of the secret .json files you created in the `.secrets` directory.

2. `--secret-dict`: A set of parameters to override the values in `--secretfile`. For example you could alter the port and ssl parameters as `--secret-dict port=5411 ssl_mode=prefer`

### Entry point with production database

You will notice that the `db_secrets_ad.json` file we created does not contain a password. To run an entrypoint against a production database you must run:

```bash
az login
```
```bash
export PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)
```

When you run an entrypoint script the CleanAir package will read the `PGPASSWORD` environment variable. This will also take precedence over any value provided in the`--secret-dict` argument. 

### Docker entry point
To run an entry point from a docker file we first need to build a docker image. Here shown for the satellite input entry point:

```bash
docker build -t input_satellite:local -f containers/dockerfiles/input_satellite_readings.Dockerfile containers  
```

To run we need to set a few more environment variables. The first is the directory with secret files in:

```bash
SECRET_DIR=$(pwd)/.secrets
```

Now get a new token:

```bash
export PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)
```

Finally you can run the docker image, passing PGPASSWORD as an environment variable
(:warning: this writes data into the online database)

```bash
docker run -e PGPASSWORD -v $SECRET_DIR:/secrets input_satellite:local -s 'db_secrets_ad.json' -k <copernicus-key>
```

Here we also provided the copernicus api key which is stored in the `cleanair-secrets`
[Azure's keyvault](https://portal.azure.com/#blade/HubsExtension/BrowseResource/resourceType/Microsoft.KeyVault%2Fvaults).

If you want to run that example with the local database you can do so by:

```bash
COPERNICUS_KEY=$(az keyvault secret show --vault-name cleanair-secrets --name satellite-copernicus-key -o tsv --query value)
# OSX or Windows: change "localhost" to host.docker.internal on your db_secrets_offline.json
docker run -e PGPASSWORD -v $SECRET_DIR:/secrets input_satellite:local -s 'db_secrets_offline.json' -k $COPERNICUS_KEY
# Linux:
docker run --network host -e PGPASSWORD -v $SECRET_DIR:/secrets input_satellite:local -s 'db_secrets_offline.json' -k $COPERNICUS_KEY
```


# UrbanAir API

The UrbanAir RESTFUL API is a [Flask](https://flask.palletsprojects.com/en/1.1.x/quickstart/) application. To run it in locally you must configure the following steps:

### Configure CleanAir database secrets
Ensure you have configured a secrets file for the CleanAir database as documented [above](#create-secret-file-to-connect-using-CleanAir-package). You will also need to set the [`PGPASSWORD` environment variable](#entry-point-with-production-database)

```bash
export DATABASE_SECRETFILE=$(pwd)/.secrets/.db_secrets_ad.json
```

### Enable Flask development server

```bash
export FLASK_ENV=development 
```

You can now run the API

```bash
python containers/urbanair/wsgi.py
```

# Developer guide

## Style guide

### Writing Documentation
Before being accepted into master all code should have well writen documentation. 

**Please use [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)**

We would like to move towards adding [type hints](https://docs.python.org/3.7/library/typing.html) so you may optionally add types to your code. In which case you do not need to include types in your google style docstrings. 

Adding and updating existing documentation is highly encouraged.

### Gitmoji
We like [gitmoji](https://gitmoji.carloscuesta.me/) for an emoji guide to our commit messages. You might consider (entirly optional) to use the [gitmoji-cli](https://github.com/carloscuesta/gitmoji-cli) as a hook when writing commit messages. 

### Working on an issue

The general workflow for contributing to the project is to first choose and issue (or create one) to work on and assign yourself to the issues. 

You can find issues that need work on by searching by the `Needs assignment` label. If you decide to move onto something else or wonder what you've got yourself into please unassign yourself, leave a comment about why you dropped the issue (e.g. got bored, blocked by something etc) and re-add the `Needs assignment` label.

You are encouraged to open a pull request earlier rather than later (either a `draft pull request` or add `WIP` to the title) so others know what you are working on. 

How you label branches is optional, but we encourage using `iss_<issue-number>_<description_of_issue>` where `<issue-number>` is the github issue number and `<description_of_issue>` is a very short description of the issue. For example `iss_928_add_api_docs`.

## Running tests

Tests should be written where possible before code is accepted into master. Contributing tests to existing code is highly desirable. Tests will also be run on travis (see the [travis configuration](.travis.yml)).

All tests can be found in the [`containers/tests/`](containers/tests) directory. We already ran some tests to check our local database was set up. 

To run the full test suite against the local database run

```bash
SECRETS=$(pwd)/.secrets/.db_secrets_offline.json
```

```bash
pytest containers --secretfile $SECRETS
```

## Writing tests

The following shows an example test:

```python
def test_scoot_reading_empty(secretfile, connection):

    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )

    with conn.dbcnxn.open_session() as session:
        assert session.query(ScootReading).count() == 0
```

It uses the `DBWriter` class to  connect to the database. In general when interacting with a database we write a class which inherits from either `DBWriter` or `DBReader`. Both classes take a `secretfile` as an argument which provides database connection secrets.

**Critically, we also pass a special `connection` fixture when initialising any class that interacts with the database**. 

This fixture ensures that all interactions with the database take place within a `transaction`. At the end of the test the transaction is rolled back leaving the database in the same state it was in before the test was run, even if `commit` is called on the database. 


# Infrastructure Deployment
:skull: **The following steps are needed to setup the Clean Air cloud infrastructure. Only infrastrucure administrator should deploy**

## Login to Travis CLI
Login to Travis with your github credentials, making sure you are in the Clean Air repository (Travis automatically detects your repository):

```bash
travis login --pro
```

Create an Azure service principal using the documentation for the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli) or with [Powershell](https://docs.microsoft.com/en-us/powershell/azure/create-azure-service-principal-azureps), ensuring that you keep track of the `NAME`, `ID` and `PASSWORD/SECRET` for the service principal, as these will be needed later.


## Setup Terraform with Python  
`Terraform` uses a backend to keep track of the infrastructure state.
We keep the backend in `Azure` storage so that everyone has a synchronised version of the state.

<details>
<summary> You can download the `tfstate` file with `az` though you won't need it.</summary>

```bash
cd terraform
az storage blob download -c terraformbackend -f terraform.tfstate -n terraform.tfstate --account-name terraformstorage924roouq --auth-mode key
```

</details>


To enable this, we have to create an initial `Terraform` configuration by running (from the root directory):

```bash
python cleanair_setup/initialise_terraform.py -i $AWS_KEY_ID -k $AWS_KEY -n $SERVICE_PRINCIPAL_NAME -s $SERVICE_PRINCIPAL_ID -p $SERVICE_PRINCIPAL_PASSWORD
```

Where `AWS_KEY_ID` and `AWS_KEY` are the secure key information needed to access TfL's SCOOT data on Amazon Web Services.

```bash
AWS_KEY=$(az keyvault secret show --vault-name terraform-configuration --name scoot-aws-key -o tsv --query value)
AWS_KEY_ID=$(az keyvault secret show --vault-name terraform-configuration --name scoot-aws-key-id -o tsv --query value)
```

And `SERVICE_PRINCIPAL`'s  `NAME`, `ID` and `PASSWORD` are also available in the `terraform-configuration` keyvault.

```bash
SERVICE_PRINCIPAL_NAME=$(az keyvault secret show --vault-name terraform-configuration --name azure-service-principal-name -o tsv --query value)
SERVICE_PRINCIPAL_ID=$(az keyvault secret show --vault-name terraform-configuration --name azure-service-principal-id -o tsv --query value)
SERVICE_PRINCIPAL_PASSWORD=$(az keyvault secret show --vault-name terraform-configuration --name azure-service-principal-password -o tsv --query value)
```

This will only need to be run once (by anyone), but it's not a problem if you run it multiple times.


## Building the Clean Air infrastructure with Terraform
To build the `Terraform` infrastructure go to the `terraform` directory

```bash
cd terraform
```

and run:

```bash
terraform init
```

If you want to, you can look at the `backend_config.tf` file, which should contain various details of your `Azure` subscription.
**NB. It is important that this file is in `.gitignore` . Do not push this file to the remote repository**

Then run:
```bash
terraform plan
```

which creates an execution plan. Check this matches your expectations. If you are happy then run:
```bash
terraform apply
```

to set up the Clean Air infrastructure on `Azure` using `Terraform`. You should be able to see this on the `Azure` portal.



## Creating A Record for cleanair API (DO THIS BEFORE RUNNING AZURE PIPELINES)
Terraform created a DNS Zone in the kubernetes cluster resource group (`RG_CLEANAIR_KUBERNETES_CLUSTER`). Navigate to the DNS Zone on the Azure portal and copy the four nameservers in the “NS” record. Send the nameserver to Turing IT Services. Ask them to add the subdomain’s DNS record as an NS record for `urbanair` in the `turing.ac.uk` DNS zone record.

1. When viewing the DNS zone on the Azure Portal, click `+ Record set`
2. In the Name field, enter `urbanair`.
3. Set Alias record set to “Yes” and this will bring up some new options.
4. We can now set up Azure pipelines. Once the cleanair api has been deployed on kubernetes you can update the alias record to point to the ip address of the cleanair-api on the cluster.


## Initialising the input databases
Terraform will now have created a number of databases. We need to add the datasets to the database.
This is done using Docker images from the Azure container registry.
You will need the username, password and server name for the Azure container registry.
All of these will be stored as secrets in the `RG_CLEANAIR_INFRASTRUCTURE > cleanair-secrets` Azure KeyVault.

<!-- ## Using Travis (old)
These Docker images are built by Travis whenever commits are made to the GitHub repository.
Add `ACR_PASSWORD`, `ACR_SERVER` and `ACR_USERNAME` as Travis secrets.

To run the next steps we need to ensure that Travis runs a build in order to add the Docker images to the Azure container registry created by Terraform.
Either push to the GitHub repository, or rerun the last build by going to https://travis-ci.com/alan-turing-institute/clean-air-infrastructure/ and clicking on the `Restart build` button.
This will build all of the Docker images and add them to the registry. -->

## Setting up Azure pipelines
These Docker images are built by an Azure pipeline whenever commits are made to the master branch of the GitHub repository.
Ensure that you have configured Azure pipelines to [use this GitHub repository](https://docs.microsoft.com/en-us/azure/devops/pipelines/get-started/pipelines-get-started).
You will need to add Service Connections to GitHub and to Azure (the Azure one should be called `cleanair-scn`).
Currently a pipeline is set up [here](https://dev.azure.com/alan-turing-institute/clean-air-infrastructure/_build).

To run the next steps we need to ensure that this pipeline runs a build in order to add the Docker images to the Azure container registry created by Terraform.
Either push to the GitHub repository, or rerun the last build by going to [the Azure pipeline page](https://dev.azure.com/alan-turing-institute/clean-air-infrastructure/_build) and clicking `Run pipeline` on the right-hand context menu.
This will build all of the Docker images and add them to the registry.

Now go to Azure and update the A-record to point to the ip address of the cleanair-api on the cluster.

## Add static datasets
To add static datasets follow the [Static data insert](#static-data-insert) instructions but use the production database credentials

## Adding live datasets
The live datasets (like LAQN or AQE) are populated using regular jobs that create an Azure container instance and add the most recent data to the database.
These are run automatically through Kubernetes and the Azure pipeline above is used to keep track of which version of the code to use.

## Kubernetes deployment with GPU support

The [azure pipeline](#setting-up-azure-pipelines) will deploy the cleanair helm chart to the azure kubernetes cluster we deployed with terraform. If you deployed GPU enabled machines on Azure (current default in the terraform script) then you need to install the nvidia device plugin daemonset. The manifest for this is [adapted from the Azure docs](https://docs.microsoft.com/en-us/azure/aks/gpu-cluster). However, as our GPU machines have [taints](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/#:~:text=Taints%20are%20the%20opposite%20%E2%80%93%20they,not%20scheduled%20onto%20inappropriate%20nodes.) applied we have to add tolerations to the manifest, otherwise the nodes will block the daemonset. To install the custom manifest run,


```bash
kubectl apply -f kubernetes/gpu_resources/nvidia-device-plugin-ds.yaml
```

<!-- 
## Configure certificates

https://cert-manager.io/docs/tutorials/acme/ingress/

## Uninstalling a failed helm install (warning - this will uninstall everything from the cleanair namespace on the cluster)

If the first helm install fails you may need to manually remove certmanager resources from the cluster with


```bash
helm uninstall cleanair --namespace cleanair
```

```bash
kubectl get -n cleanair crd
kubectl delete -n cert-manager crd --all
kubectl delete namespaces cleanair
```

Cluster roles may not be removed. Remove them with:
```bash
kubectl get clusterrole  | grep 'cert-manager'|awk '{print $1}'| xargs kubectl delete clusterrole
kubectl get role --namespace kube-system  | grep 'cert-manager'|awk '{print $1}'| xargs kubectl delete role --namespace kube-system
kubectl get clusterrolebindings | grep 'cert-manager'|awk '{print $1}'|xargs kubectl delete clusterrolebindings
kubectl get mutatingwebhookconfigurations | grep 'cert-manager'|awk '{print $1}'|xargs kubectl delete mutatingwebhookconfigurations
kubectl get validatingwebhookconfigurations  | grep 'cert-manager'|awk '{print $1}'|xargs kubectl delete validatingwebhookconfigurations
kubectl get rolebindings --namespace kube-system | grep 'cert-manager'|awk '{print $1}'|xargs kubectl delete rolebindings --namespace kube-system
kubectl get clusterrole  | grep 'nginx'|awk '{print $1}'| xargs kubectl delete clusterrole
kubectl get clusterrolebindings | grep 'nginx'|awk '{print $1}'|xargs kubectl delete clusterrolebindings

```

If helm wont install the chart after this check all api services are working:

```bash
kubectl get apiservice
```

Deleteing the failed api service may resolve this issue:

```bash
kubectl delete apiservice v1beta1.metrics.k8s.io
```


Follow theses instructions https://cert-manager.io/docs/tutorials/acme/ingress/ -->

<!-- We tell this job which version of the container to run by using GitHub webhooks which keep track of changes to the master branch.

### Setting up webhooks in the GitHub repository
- Run `python cleanair_setup/get_github_keys.py` to get the SSH keys and webhook settings for each of the relevant servers
- In GitHub go to `clean-air-infrastructure > Settings > Deploy keys` and click on `Add deploy key`
- Paste the key into `Key` and give it a memorable title (like `laqn-cleanair`)

### Enable webhooks in GitHub
- In GitHub go to `clean-air-infrastructure > Settings > Webhooks` and click on `Add webhook`
- Set the `Payload URL` to the value given by `get_github_keys.py`
- Set the `Content type` to `application/json` (not required but preferred)
- Select `Let me select individual events` and tick `Pull requests` only -->

## Removing Terraform infrastructure
To destroy all the resources created by `Terraform` run:
```
terraform destroy
```

You can check everything was removed on the Azure portal.
Then login to TravisCI and delete the Azure Container repo environment variables.



<!-- Open the file and replace the <> with the secret values which can be found in the keyvault in the `RG_CLEANAIR_INFRASTRUCTURE` Azure resource group.

## Build and run docker images locally
**AQE - Download AQE data**
```bash
docker build -t cleanairdocker.azurecr.io/aqe -f containers/dockerfiles/add_aqe_readings.Dockerfile containers && docker run -v /<repo-dir>/clean-air-infrastructure/terraform/.secrets:/secrets cleanairdocker.azurecr.io/aqe
```

**LAQN - Download LAQN data**
```bash
docker build -t cleanairdocker.azurecr.io/laqn -f containers/dockerfiles/add_laqn_readings.Dockerfile containers && docker run -v /<repo-dir>/clean-air-infrastructure/terraform/.secrets:/secrets cleanairdocker.azurecr.io/laqn
```

**UKMAP feature extraction**
```bash
docker build -t cleanairdocker.azurecr.io/ukmap -f containers/dockerfiles/extract_ukmap_features.Dockerfile containers && docker run -v <repo-dir>/clean-air-infrastructure/terraform/.secrets:/secrets cleanairdocker.azurecr.io/ukmap
```

**OSHighway feature extraction**
```
docker build -t cleanairdocker.azurecr.io/osh -f containers/dockerfiles/extract_oshighway_features.Dockerfile containers && docker run -v /<repo-dir>/clean-air-infrastructure/terraform/.secrets:/secrets cleanairdocker.azurecr.io/osh
```

**Model fitting**
```bash
docker build -t cleanairdocker.azurecr.io/mf -f containers/dockerfiles/run_model_fitting.Dockerfile containers && docker run -v /<repo-dir>/clean-air-infrastructure/terraform/.secrets:/secrets cleanairdocker.azurecr.io/mf
``` -->

<!-- ## The cleanair parser

A `CleanAirParser` class has been created for interacting with `run_model_fitting.py`. Run the following command to see available options:

```bash
python run_model_fitting.py -h
```

By passing no arguments, `run_model_fitting.py` will read data from the DB and write the results to the DB using the default data_config.
Reading and writing data/results is all made possible through the command line. Different arguments are available for `run_dashboard.py`. -->

<!-- ### Parser config

If you frequently run model fitting locally, then you may wish to store some of your common settings into the `parser_config.json` file. For example, if you always want to `return_y` and `predict_training`, then your parser config file would look like:

```json
{
    "return_y": true,
    "predict_training": true 
}
```

By passing the `-c` flag, the parser will use the json file to overwrite the default parser values. -->

<!-- ## Running with local database

### Install postgres and upload static datasets

It is possible to test code without the Azure infrastructure. This can be achieved by creating databases on your local machine. Ensure you install the following:

- Install postgres and start it running
```bash
brew install postgresql postgis
brew services start postgres
```

- Create a database called 'cleanair_inputs_db'. In a terminal run:
```bash
psql postgres
```

and then create the database:
```bash
CREATE DATABASE cleanair_inputs_db;
```

- Create a local secrets file following the instructions above

- Follow all instructions above as per cloud until add static datasets.

- Download static data and insert into the database:
```
python cleanair_setup/insert_static_datasets.py -l terraform/.secrets/.db_secrets.json
``` -->


<!-- ## Dashboard

The dashboard lets you see the predictions and validation scores of a model fit on the LAQN sensors. To run the dashboard you must have a [mapbox API key](https://account.mapbox.com/auth/signup/) and sign up to their account.

Once you have the key, use the following command to place the key in the .secrets folder:

```bash
echo "API_KEY" > terraform/.secrets/.mapbox_token
```

At the moment you can only run the dashboard locally:
```bash
python run_dashboard.py
```

By default the dashboard will try to load a model fit from the DB, but you can pass command line arguments to load a locally stored model fit.
 -->

<!-- 
## Configure Kubernetes Cluster:

### Local cluster
You can set up a local cluster on your machine. To do this install [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/)

To start the cluster run:
```
minikube start --vm-driver=virtualbox
```

Start the cluster dashboard with:
```
minikube dashboard
```

Next follow these instruction to [install helm](https://helm.sh/docs/using_helm/).

### Adding secrets
The cluster requires secrets in order to pull images from the azure container repository and to connect to databases. When terraform provisioned the azure infrastructure it creates a folder called `.secrets/` which contains a number of files. We need to add these to the Kubernetes cluster.

The ACR login details are in a file called .regcred_secret.json
```
kubectl create secret docker-registry regcred --docker-server=<servername> --docker-username=<username>--docker-password=<password> --docker-email=<your-email>
```

Next create a secret for each database secret file:
```
kubectl create secret generic secrets --from-file=<path_to_aws_secret>aws_secrets.json --from-file=<path_to_db_secret>/db_secrets.json
```


### Configure the cluster with Helm
Go to the `/kubernetes` directory and run:

```
helm install kubernetes/cleanair
```

Now you to the minikube dashboard and you can see everything that was installed.

## How to create a new model

Look at the `model.py`. You will need to extend the `Model` class (or an existing model) using your new model class you are about to create. The `Model` class contains information about the shapes and the expected parameters/returns of functions for a model. We recommend you read this file closely before implementing your model.

The `SVGP` class is an example of a `Model` that uses only laqn data and some features. We recommend you look through this class before implementing your model.

All model parameters should be contained within the `model_params` dictionary. -->
