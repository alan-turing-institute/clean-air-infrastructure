
import os
import logging
import tensorflow as tf
from cleanair.instance import ValidationInstance, LaqnTestInstance
from cleanair.parsers import ModelValidationParser
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

def main():
    parser = ModelValidationParser(description="Run validation")

    kwargs = parser.parse_all()

    # get the right instance class
    instance_classes = dict(
        test=LaqnTestInstance,
        validation=ValidationInstance,
    )
    instance_cls = instance_classes[kwargs.get("tag")]

    # ToDo: remove hard-coded satellite setting
    logging.warning("Turing off satellite data until it is fixed.")
    parser.data_args["include_satellite"] = True

    # setup model parameters
    model_params = instance_cls.DEFAULT_MODEL_PARAMS
    
    model_params = {
        "jitter": 1e-5,
        "likelihood_variance": 0.1,
        "minibatch_size": 100,
        "n_inducing_points": 200,
        "maxiter": 1000,
        "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
    }

    model_params.update(parser.model_args)

    instance = instance_cls(data_config=parser.data_args, experiment_config=parser.experiment_args, model_params=model_params, **kwargs)

    instance.run()

    logging.info("Instance id is %s - use this id to read results from DB.", instance.instance_id)

if __name__ == "__main__":
    main()
