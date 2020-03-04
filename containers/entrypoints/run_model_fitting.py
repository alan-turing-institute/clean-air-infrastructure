"""
Model fitting
"""
import logging
from cleanair.loggers import get_log_level
from cleanair.parsers import ModelFitParser
from cleanair.parsers import get_data_config_from_kwargs
from cleanair.experiment import ProductionInstance, LaqnTestInstance


def main():
    """
    Run model fitting
    """
    # Read command line arguments
    parser = ModelFitParser(description="Run model fitting")

    # Parse and interpret arguments
    kwargs = parser.parse_kwargs()

    # Set logging
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # Read the data config
    data_config = get_data_config_from_kwargs(kwargs)

    # get big dictionary of experiment config
    xp_config = kwargs.copy()
    xp_config.update(dict(
        restore=False, model_state_fp=xp_config["model_dir"], save_model_state=False
    ))
    # create a production instance from data and experiment configs
    instance = ProductionInstance(
        model_name=kwargs["model_name"],
        experiment_config=xp_config,
        data_config=data_config,
    )
    # create a simple laqn test instance with an SVGP
    # instance = LaqnTestInstance(secretfile=kwargs["secretfile"])

    # get instance Ids
    logging.info("Instance id: %s", instance.instance_id)
    logging.info("Model param id: %s", instance.param_id)
    logging.info("Data id: %s", instance.data_id)
    logging.info("Github hash: %s", instance.hash)

    # run the instance
    instance.run()

if __name__ == "__main__":
    main()
