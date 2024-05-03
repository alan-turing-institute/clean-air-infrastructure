## Installation of Cleanair JAX Package

First, we recommend creating a conda environment called `urbanair_jax`.
Our packages work with *python 3.10 or later*, but we recommend python 3.10.

> Please take care to install all packages from the *conda-forge* channel!

```bash
# create the environment and activate
conda create -n urbanair_jax python==3.11.4
conda activate urbanair_jax
```

All cleanair model packages depends on the `cleanair_types`

```

pip install -e containers/cleanair/cleanair_types

```

To contribute to the cleanair package, please also see the [developer guide](developer.md).

## Install cleanair GP JAX Model package

To install the `gpjax_models` package with the basic requirements:

```

pip install -e containers/cleanair/gpjax_models

```
