# Installation

First, we recommend creating a conda environment called `urbanair`.
Our packages work with *python 3.8 or later*, but we recommend python 3.10.

> Please take care to install all packages from the *conda-forge* channel!
```bash
# create the environment and activate
conda create -n urbanair python=3.10
conda activate urbanair
# set the conda-forge channel as the top priority
conda config --env --add channels conda-forge
conda config --env --set channel_priority strict
# now install python, geopandas, plus any other libraries
conda install python=3.10 geopandas=0.10.2
```

We strongly recommend [installing geopandas](https://geopandas.org/en/stable/getting_started/install.html)
if you intend to handle the geospatial datasets.

If you experience installation problems, why not try our [docker images](#what-about-docker)?

To contribute to the cleanair package, please also see the [developer guide](developer.md).

## Install cleanair

To install the `cleanair` package with the basic requirements:

```
pip install -e containers/cleanair
```

> If you are using an Apple M1 (ARM) processor you may experience unexpected problems, for example installing [psycopg-binary](https://www.psycopg.org/psycopg3/docs/basic/install.html#binary-installation). Our [docker images](#what-about-docker) offer a quick alternative!

## Install the developer dependencies

This line will install all the python packages needed for testing and linting:

```
pip install -r containers/requirements.txt
```

## Install urbanair

`urbanair` is the API package we created to query results from the air quality model.
It depends upon the cleanair package being installed.
Install with pip:

```
pip install -e containers/urbanair
```

## What about docker?

You can build our docker files using the normal docker commands.
For example:

```bash
docker build -t cleanair:latest -f containers/dockerfiles/cleanair.Dockerfile containers
```

Alternatively you can pull the docker images from our Azure container registry.
[Ask an active contributor](contributors.md) for help.
