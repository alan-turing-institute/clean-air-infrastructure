
import os
import logging
from cleanair.experiment import ValidationInstance
from cleanair.loggers import get_log_level
from cleanair.parsers import ValidationParser

def main():
    parser = ValidationParser(description="Run validation")

    kwargs, data_args, xp_config, model_args = parser.parse_all()

    # Set logging
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    model_params = ValidationInstance.DEFAULT_MODEL_PARAMS
    model_params.update(model_args)

    instance = ValidationInstance(data_config=data_args, experiment_config=xp_config, model_params=model_params, **kwargs)

    instance.run()

if __name__ == "__main__":
    main()
