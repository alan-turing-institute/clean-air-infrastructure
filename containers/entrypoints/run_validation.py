
import os
import tensorflow as tf
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import logging
from cleanair.instance import ValidationInstance
from cleanair.parsers import ModelValidationParser

def main():
    parser = ModelValidationParser(description="Run validation")

    kwargs = parser.parse_all()

    model_params = ValidationInstance.DEFAULT_MODEL_PARAMS
    model_params.update(parser.model_args)

    instance = ValidationInstance(data_config=parser.data_args, experiment_config=parser.experiment_args, model_params=model_params, **kwargs)

    instance.run()

if __name__ == "__main__":
    main()
