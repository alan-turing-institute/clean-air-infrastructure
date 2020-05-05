"""
Model fitting
"""
import logging
from cleanair.parsers import ProductionParser
from cleanair.instance import ProductionInstance

def main():
    """
    Run model fitting
    """
    # Read command line arguments
    parser = ProductionParser(description="Run model fitting")
    kwargs = parser.parse_all()

    # update data config with parsed arguments
    data_config = ProductionInstance.DEFAULT_DATA_CONFIG
    data_config.update(parser.data_args)

    # ToDo: remove hard-coded parameters, it is a temp fix
    data_config["include_satellite"] = True

    # update model parameters with parsed args
    model_params = ProductionInstance.DEFAULT_MODEL_PARAMS
    model_params.update(parser.model_args)

    # ToDo: remove hard-coded model parameters
    from cleanair.instance import ValidationInstance
    model_params = ValidationInstance.DEFAULT_MODEL_PARAMS

    # create the instance
    instance = ProductionInstance(
        data_config=data_config,
        experiment_config=parser.experiment_args,
        model_params=model_params,
        **kwargs
    )
    # setup, fit, predict, and update
    instance.run()

if __name__ == "__main__":
    main()
