"""
Instance for validation that allows more flexibility such as reading/writing from files.
"""

from .runnable import RunnableInstance

class ValidationInstance(RunnableInstance):

    DEFAULT_EXPERIMENT_CONFIG = {
        "model_name": "mr_dgp",
        "secretfile": "../../terraform/.secrets/db_secrets.json",
        "results_dir": "./",
        "model_dir": "./",
        "config_dir": "./",
        "local_read": False,
        "local_write": False,
        "predict_training": False,
        "predict_write": False,
        "no_db_write": False,
        "restore": False,
        "save_model_state": False,
    }

    def __init__(self, **kwargs):
        # get default experiment config
        experiment_config = self.__class__.DEFAULT_EXPERIMENT_CONFIG.copy()

        # update with passed config
        experiment_config.update(kwargs.pop("experiment_config", {}))

        # pass to super constructor
        super().__init__(experiment_config=experiment_config, **kwargs)

    def load_model_params(self):
        if self._param_id:    # check if param_id has been passed
            raise NotImplementedError("Coming soon: Cannot yet read model params from DB.")
