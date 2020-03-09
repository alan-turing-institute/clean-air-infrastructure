"""
The instance to run in production.
"""

from .runnable import RunnableInstance

class ProductionInstance(RunnableInstance):

    DEFAULT_DATA_CONFIG = dict(
        RunnableInstance.DEFAULT_DATA_CONFIG,
        include_satellite=True,
        tag="production",
        # ToDo: include grid in prediction
        pred_sources=["laqn"],
    )

    DEFAULT_MODEL_PARAMS = dict()   # ToDo: add default model params for DeepGp
    
    DEFAULT_MODEL_NAME = "mr_dgp"

    def __init__(self, data_config=None, experiment_config=None, model_params=None, **kwargs):
        # ToDo: check that version is master and tag is production
        if "tag" in kwargs and kwargs["tag"] != "production":
            raise AttributeError("The tag must be 'production' when running a production instance. Change to a different instance if not running production code.")

        super().__init__(data_config=data_config, experiment_config=experiment_config, model_params=model_params, **kwargs)
