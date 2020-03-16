
import os
import tensorflow as tf
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import logging
from cleanair.experiment import ValidationInstance
from cleanair.parsers import ModelValidationParser

def main():
    parser = ModelValidationParser(description="Run validation")

    kwargs, data_args, xp_config, model_args = parser.parse_all()

    model_params = ValidationInstance.DEFAULT_MODEL_PARAMS
    model_params.update(model_args)

    instance = ValidationInstance(data_config=data_args, experiment_config=xp_config, model_params=model_params, **kwargs)

    instance.run()

if __name__ == "__main__":
    main()
