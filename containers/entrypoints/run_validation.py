
import os
import tensorflow as tf
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import logging
from cleanair.instance import ValidationInstance, LaqnTestInstance
from cleanair.parsers import ModelValidationParser

def main():
    parser = ModelValidationParser(description="Run validation")

    kwargs = parser.parse_all()

    # get the right instance class
    instance_classes = dict(
        test=LaqnTestInstance,
        validation=ValidationInstance,
    )
    instance_cls = instance_classes[kwargs.get("tag")]

    # setup model parameters
    model_params = instance_cls.DEFAULT_MODEL_PARAMS
    model_params.update(parser.model_args)

    instance = instance_cls(data_config=parser.data_args, experiment_config=parser.experiment_args, model_params=model_params, **kwargs)

    instance.run()

if __name__ == "__main__":
    main()
