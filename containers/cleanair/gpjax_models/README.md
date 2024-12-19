# Installation

First, we recommend creating a conda environment called `urbanair`.
Our packages work with *python 3.10 or later*, but we recommend python 3.11.

> Please take care to install all packages from the *conda-forge* channel!

```bash
# create the environment and activate
conda create -n gpjax_models
conda activate gpjax_models
pip install numpy>=2.0.0

```

# Installation

```bash
pip install -e containers/cleanair/cleanair_types 

pip install -e containers/cleanair/gpjax_models

pip install -r containers/cleanair/gpjax_models/requirements.txt

```

# Running the MRDGP models

```bash

urbanair_jax model fit  train-mrdgp <DATA_DIR>

```

# Running the SVGP models only LAQN

```bash

urbanair_jax model fit  train-svgp_laqn <DATA_DIR>

```

# Running the SVGP models only Satellite models

```bash

urbanair_jax model fit  train-svgp_sat <DATA_DIR>

```
