# Experiment for air quality

An experiment runs multiple models on multiple datasets.

TL;DR:

```bash
urbanair experiment setup NAME
urbanair experiment run NAME    # no DB connection required
urbanair experiment update NAME
```

To see the names of experiments you can use the `--help` option.

For each of the above commands, you can optionally pass an `--experiment-root`: a path to a directory storing all of your experiments.

For running on clusters with `slurm`, you can run experiments in different batches instead of the standard `run` command:

```bash
urbanair experiment batch NAME BATCH_START BATCH_SIZE
```

`BATCH_START` is the index in the list of instances to start at.
`BATCH_SIZE` is the number of instances to run in this batch.

***

## Adjusting model parameters

The params module is where default parameters for the models are stored.
Each model has a module with constants (e.g. `SVGP_NUM_INDUCING_POINTS`) and functions that create a model params object with those constants (e.g. `default_svgp_model_params()`).
There are also some default parameters that are shared between models.

The most common use case is to adjust a small subset of the default model parameters.
For example, to adjust the number of inducing points for the SVGP:

```python
from cleanair.params import default_svgp_model_params
model_params = default_svgp_model_params(num_inducing_points=1500)
```

Alternatively, you can create the default parameters first, then edit afterwards:
```python
model_params = default_svgp_model_params()
model_params.num_inducing_points = 1500
```

***

## Adjusting data config

Similarly to adjusting model parameters, one can change the settings of the dataset such as the static/dynamic features, dates for training, length of training period, etc.
For example, to change the static features for a dataset with only LAQN data:

```python
from cleanair.experiment import default_laqn_data_config
from cleanair.types import FeatureNames

# NOTE this is note a full data config
data_config = default_laqn_data_config()
data_config.static_features = [
    FeatureNames.total_a_road_length, FeatureNames.water, FeatureNames.park
]
```

***

## How to create a new experiment

Now that you can create and adjust model parameters and data config, you can create new experiments in two steps:

1. Add a function `example_experiment` to `generate_air_quality_experiment.py`.
    - The function should take `secretfile` as a parameter.
    - Returns a list of instances.

```python
def example_experiment(secretfile: str) -> List[InstanceMixin]:
    # adjust your model params and data config as you desire
    data_config = default_laqn_data_config()
    model_params = default_svgp_model_params(num_inducing_points=1500)
    data_config.static_features = [
        FeatureNames.total_a_road_length,
        FeatureNames.water,
        FeatureNames.park,
    ]
    ...
    # TODO create a list of instances from the above settings
    instance_list = [...]
    ...
    return instance_list
```

2. Add the function name to `ExperimentName`. This lets us call the experiment from the command line interface:
```python
# inside cleanair.types.experiment_types.py
class ExperimentName(BaseModel):    # this class already exists
    ...
    # add your experiment name here...
    example_experiment = "example_experiment"
```

***

## File structure

We strongly recommend using the functions provided in `Experiment` and `FileManager` classes to access any data.
For each instance, the experiment class defines a `FileManager` class.
Using the `get_file_manager(INSTANCE_ID)` method of any `Experiment` class, you can read and write the dataset, model and result files.
However, if you do need access to a specific file, the file structure is explained below.

The `EXPERIMENT_ROOT` is where all of your experiments are stored.
If you are using the default cache, then you can get the experiment root:

```bash
export EXPERIMENT_ROOT="$(urbanair config path)/experiment_cache"
echo $EXPERIMENT_ROOT
```

`NAME` is the name of one experiment.
Inside `experiment_config.json` you will find a list of instance ids.
This list of instance ids is used to read and write from the `INSTANCE_ID` directory.

```bash
EXPERIMENT_ROOT/
    NAME/
        experiment_config.json
        INSTANCE_ID/
            dataset/
                data_config.json
                training_dataset.pkl
                test_dataset.pkl
            instance.json
            model/
                model_params.json
                elbo.json
            result/
                pred_forecast.pkl
                pred_training.pkl
```            

