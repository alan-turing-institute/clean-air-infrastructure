# Installation

First, we recommend creating a conda environment called `urbanair`.
Our packages work with *python 3.8 or later*, but we recommend python 3.10.

> Please take care to install all packages from the *conda-forge* channel!

```bash
# create the environment and activate
conda create -n urbanairdata
conda activate urbanairdata
# set the conda     -forge channel as the top priority
conda config --env --add channels conda-forge
conda config --env --set channel_priority strict
# now install python, ecCodes, geopandas, plus any other libraries
conda install python=3.10 geopandas=0.10.2 eccodes==2.26.0
```

We strongly recommend [installing geopandas](https://geopandas.org/en/stable/getting_started/install.html)
if you intend to handle the geospatial datasets.

If you experience installation problems, why not try our [docker images](#what-about-docker)?

To contribute to the cleanair package, please also see the [developer guide](developer.md).

## Install cleanair

To install the `cleanair_type` package with the requirements, follow these steps. All the `cleanair` packages use the ***cleanair_type*** type package for integrity.

```
pip install -e containers/cleanair_types
```

To install the `cleanair_data` package with the requirements:

```
pip install -e containers/cleanair_data
```

> If you are using an Apple M1 (ARM) processor you may experience unexpected problems, for example installing [psycopg-binary](https://www.psycopg.org/psycopg3/docs/basic/install.html#binary-installation). Our [docker images](#what-about-docker) offer a quick alternative!

## Install the developer dependencies

This line will install all the python packages needed for testing and linting:

```
pip install -r containers/cleanair/cleanair_data/requirements.txt
```

## What about docker?

You can build our docker files using the normal docker commands.
For example:

```bash
docker build -t cleanair:latest -f containers/dockerfiles/cleanair.Dockerfile containers
```

If you have difficulties with the system setup [ask an active contributor](contributors.md) for help.
