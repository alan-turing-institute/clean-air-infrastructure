# Researcher guide

*The following steps provide useful tools for researchers to use, for example setting up jupyter notebooks and running models using a GPU.*

## Setup notebook

First install jupyter with conda (you can also use pip).

```bash
pip install jupyter
```

You can start the notebook:

```bash
jupyter notebook
```

Alternatively you may wish to use jupyter lab which offers more features on top of the normal notebooks.

```bash
jupyter lab
```

This will require some additional steps for [adding jupyter lab extensions for plotly](https://plotly.com/python/getting-started/#jupyterlab-support-python-35).

For some notebooks you may also want to a mapbox for visualising spatial data. To do this you will need a [mapbox access token](https://docs.mapbox.com/help/how-mapbox-works/access-tokens/) which you can store inside your `.env` file (see below).

### Environment variables

To access the database, the notebooks need access to the `PGPASSWORD` environment variable.
It is also recommended to set the `DB_SECRET_FILE` variable.
We will create a `.env` file within you notebook directory `path/to/notebook` where you will be storing environment variables.

> **Note**: if you are using a shared system or scientific cluster, **do not follow these steps and do not store your password in a file**.

Run the below command to create a `.env` file, replacing `path/to/secretfile` with the path to your `db_secrets`.

```bash
echo '
DB_SECRET_FILE="path/to/secretfile"
PGPASSWORD=
' > path/to/notebook/.env
```

To set the `PGPASSWORD`, run the following command.
This will create a new password using the azure cli and replace the line in `.env` that contains `PGPASSWORD` with the new password.
Remember to replace `path/to/notebook` with the path to your notebook directory.

```bash
sed -i '' "s/.*PGPASSWORD.*/PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)/g" path/to/notebook/.env
```

If you need to store other environment variables and access them in your notebook, simply add them to the `.env` file.

To access the environment variables, include the following lines at the top of your jupyter notebook:

```python
%load_ext dotenv
%dotenv
```

You can now access the value of these variables as follows:

```python
secretfile = os.getenv("DB_SECRET_FILE", None)
```

Remember that the `PGPASSWORD` token will only be valid for ~1h.

## Training models

To train a model on your local machine you can run a model fitting entrypoint:

```bash
python containers/entrypoints/model_fitting/model_fitting.py --secretfile $SECRETS
```

You can adjust the model parameters and data settings by changing the command line arguments.
Use the `--help` flag to see available options.

## GPU support with Docker

For GPU support we strongly recommend using our docker image to run the entrypoint.
This docker image extends the tensorflow 1.15 GPU dockerfile for python 3.6 with gpflow 1.5 installed.

You can build our custom GPU dockerfile with the following command:

```bash
docker build --build-arg git_hash=$(git show -s --format=%H) -t cleanairdocker.azurecr.io/mf -f containers/dockerfiles/model_fitting.Dockerfile containers
```

To run the latest version of this entrypoint:

```bash
docker run -it -e PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv) --rm -v $(pwd)/.secrets:/secrets cleanairdocker.azurecr.io/mf:latest --secretfile /secrets/.db_secrets_ad.json
```

## Singularity for HPC

Many scientific clusters will give you access to [Singularity](https://singularity.lbl.gov/).
This software means you can [import and run Docker images](https://singularity.lbl.gov/docs-docker) without having Docker installed or being a superuser.
Scientific clusters are often a pain to setup, so we strongly recommend using Singularity & Docker to avoid a painful experience.

First login to your HPC and ensure singularity is installed:

```bash
singularity --version
```

Now we will need to pull the Docker image from our Docker container registry on Azure.
Since our docker images are private you will need to login to the container registry.
1. Go to [portal.azure.com](https://portal.azure.com).
2. Search for the `CleanAirDocker` container registry.
3. Go to `Access keys`.
4. The username is `CleanAirDocker`. Copy the password.

```bash
singularity pull --docker-login docker://cleanairdocker.azurecr.io/mf:latest
```

Then build the singularity image to a `.sif` file.
We recommend you store all of your singularity images in a directory called `containers`.

```bash
singularity build --docker-login containers/model_fitting.sif docker://cleanairdocker.azurecr.io/mf:latest
```

To test everything has built correctly, spawn a shell and run python:

```bash
singularity shell containers/model_fitting.sif
python
```

Then try importing tensorflow and cleanair:

```python
import tensorflow as tf
tf.__version__
import cleanair
cleanair.__version__
```

Finally your can run the singularity image, passing any arguments you see fit:

```bash
singularity run containers/model_fitting.sif --secretfile $SECRETS
```