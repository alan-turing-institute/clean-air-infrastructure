# Installation

First, we recommend creating a conda (or pyenv) environment called `urbanair`:

```
conda create -n urbanair python=3.7.8 --channel conda-forge
```

To contribute to the cleanair package, please also see the [developer guide](developer.md).

## Install cleanair

To install the `cleanair` package with the basic requirements:

```
pip install -e containers/cleanair
```

If you need to install the modelling software (Tensorflow and GPflow):

```
pip install -e "containers/cleanair[models]"
```

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
