"""
Model fitting
"""
import logging
from cleanair.loggers import get_log_level
from cleanair.parsers import ModelFitParser
from cleanair.experiment import ProductionInstance

def main():
    """
    Run model fitting
    """
    # Read command line arguments
    parser = ModelFitParser(description="Run model fitting")
    kwargs, data_args, xp_config, model_args = parser.parse_all()

    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # update data config with parsed arguments
    data_config = ProductionInstance.DEFAULT_DATA_CONFIG
    data_config.update(data_args)

    # update mode parameters with parsed args
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

    # get instance Ids
    logging.info("Instance id: %s", instance.instance_id)
    logging.info("Model param id: %s", instance.param_id)
    logging.info("Data id: %s", instance.data_id)
    logging.info("Github hash: %s", instance.git_hash)

    # run the instance
    instance.run()

if __name__ == "__main__":
    main()
