"""
Model fitting
"""
import logging
import os
import tensorflow as tf

# stop tf warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from cleanair.loggers import get_log_level
from cleanair.parsers import ProductionParser
from cleanair.experiment import ProductionInstance

def main():
    """
    Run model fitting
    """
    # Read command line arguments
    parser = ProductionParser(description="Run model fitting")
    kwargs, data_args, xp_config, model_args = parser.parse_all()

    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # update data config with parsed arguments
    data_config = ProductionInstance.DEFAULT_DATA_CONFIG
    data_config.update(data_args)

    # update model parameters with parsed args
    model_params = ProductionInstance.DEFAULT_MODEL_PARAMS
    model_params.update(model_args)

    # create the instance
    instance = ProductionInstance(
        data_config=data_config,
        experiment_config=xp_config,
        model_params=model_params,
        **kwargs
    )
    # setup, fit, predict, and update
    instance.run()

if __name__ == "__main__":
    main()
