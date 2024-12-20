# GPJax Models

This package provides implementations of various Gaussian Process models using JAX.

## Installation

1. Create and activate a conda environment:

```bash
conda create -n gpjax_models python=3.11
conda activate gpjax_models
```

> **Note**: All packages must be installed from the *conda-forge* channel. Python 3.10 or later is required, with 3.11 recommended.

2. Install dependencies:

```bash
pip install numpy>=2.0.0
pip install -e containers/cleanair/cleanair_types 
pip install -e containers/cleanair/gpjax_models
pip install -r containers/cleanair/gpjax_models/requirements.txt
```

## Usage

### MRDGP Models

Run single-mode training:

```bash
urbanair_jax model fit train-mrdgp --mode single <DATA_DIR>
```

Run sequential training:

```bash
urbanair_jax model fit train-mrdgp --mode sequential <DATA_DIR>
```

### SVGP Models

For LAQN data:

```bash
urbanair_jax model fit train-svgp_laqn <DATA_DIR>
```

Run sequential training:

```bash
urbanair_jax model fit train-svgp_laqn --sequential <DATA_DIR>
```

For Satellite data:

```bash
urbanair_jax model fit train-svgp_sat <DATA_DIR>
```
