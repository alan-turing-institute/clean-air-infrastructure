"""
Instances of models and data.
"""
import json
import hashlib
import git
from ...models import SVGP, MRDGP
from ...databases import DBWriter

class Instance():
    """
    An instance is one model trained and fitted on some data.
    """

    DEFAULT_DATA_CONFIG = {
        "train_start_date": "2020-01-29T00:00:00",
        "train_end_date": "2020-01-30T00:00:00",
        "pred_start_date": "2020-01-30T00:00:00",
        "pred_end_date": "2020-01-31T00:00:00",
        "include_satellite": True,
        "include_prediction_y": False,
        "train_sources": ["laqn"],
        "pred_sources": ["laqn"],
        "train_interest_points": "all",
        "train_satellite_interest_points": "all",
        "pred_interest_points": "all",
        "species": ["NO2"],
        "features": [
            "value_1000_total_a_road_length",
            "value_500_total_a_road_length",
            "value_500_total_a_road_primary_length",
            "value_500_total_b_road_length",
        ],
        "norm_by": "laqn",
        "tag": "production",
    }
    DEFAULT_MODEL_PARAMS = {
        "jitter": 1e-5,
        "likelihood_variance": 0.1,
        "minibatch_size": 100,
        "n_inducing_points": 200,
        "restore": False,
        "train": True,
        "model_state_fp": None,
        "maxiter": 100,
        "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
    }
    MODELS = {
        'svgp': SVGP,
        'mr_dgp': MRDGP,
    }

    DEFAULT_MODEL_NAME = "svgp"

    def __init__(self, **kwargs):
        # get the name of the model to run
        self.model_name = kwargs["model_name"] if "model_name" in kwargs else self.__class__.DEFAULT_MODEL_NAME

        # not a valid model
        if self.model_name not in self.__class__.MODELS:
            raise KeyError("{name} is not a valid model.".format(name=self.model_name))

        # set parameter id
        if "param_id" in kwargs:
            self.param_id = kwargs["param_id"]
        elif "model_params" in kwargs:
            self.param_id = self.hash_params(kwargs["model_params"])
        else:
            self.param_id = self.hash_params(self.__class__.DEFAULT_MODEL_PARAMS)

        # set data id
        if "data_id" in kwargs:
            self.data_id = kwargs["data_id"]
        elif "data_config" in kwargs:
            self.data_id = self.hash_data(kwargs["data_config"])
        else:
            self.data_id = self.hash_data(self.__class__.DEFAULT_DATA_CONFIG)

        # set cluster id
        self.cluster_id = kwargs["cluster_id"] if "cluster_id" in kwargs else "unassigned"

        # passing a tag
        self.tag = kwargs["tag"] if "tag" in kwargs else "unassigned"

        # creating the github hash
        self.hash = git.Repo(search_parent_directories=True).head.object.hexsha

        # get the instance id
        self.instance_id = self.hash_instance()

    def hash_instance(self):
        hash_string = self.model_name + str(self.param_id) + self.tag
        hash_string += str(self.data_id) + str(self.cluster_id)
        return Instance.hash_fn(hash_string)

    def hash_params(self, model_params):
        hash_string = json.dumps(model_params)
        return Instance.hash_fn(hash_string)

    def hash_data(self, data_config):
        hash_string = json.dumps(data_config)
        return Instance.hash_fn(hash_string)

    @staticmethod
    def hash_fn(hash_string):
        sha_fn = hashlib.sha256()
        sha_fn.update(bytearray(hash_string, "utf-8"))
        return sha_fn.hexdigest()



class WritableInstance(Instance, DBWriter):
    """
    Adds functionality for reading and writing to the DB.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def update_table(self):
        """
        Update the instance table and (if necessary) data and model tables.
        """
        raise NotImplementedError()



