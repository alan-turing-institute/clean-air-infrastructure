"""
Instances of models and data.
"""
import json
import hashlib
import git
from ..models import ModelData, SVGP, MRDGP
from ..databases import DBWriter
from ..metrics import pop_kwarg

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
        "model_type": "svgp",
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

    DIGEST_SIZE = 20

    def __init__(self, **kwargs):
        self.model_name = kwargs["model_name"]

        # set attributes
        attrs = ["parser_config", "model_data", "model_name", "model", "param_id", "data_id", "hash", "tag", "cluster_id"]
        for key in attrs:
            if key in kwargs:
                setattr(self, key, kwargs[key])

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

        # creating the instance id
        for key, value in kwargs.items():
            setattr(self, key, value)

        # creating the github hash
        self.hash = git.Repo(search_parent_directories=True).head.object.hexsha

        # get the instance id
        self.instance_id = self.hash_instance()

    def update_table(self):
        """
        Update the instance table and (if necessary) data and model tables.
        """
        raise NotImplementedError()

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
        sha_fn.digest_size = Instance.DIGEST_SIZE
        sha_fn.update(hash_string)
        return sha_fn.hexdigest()

class RunnableInstance(Instance):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # passing a model
        if not hasattr(self, "model") and not hasattr(self, "model_name"):
            raise AttributeError("Must pass a model or model_name to Instance.")

        if hasattr("model_name") and not hasattr(self, "model"):
            # not a valid model
            if getattr(self, "model_name") not in Instance.MODELS:
                raise KeyError("{name} is not a valid model.".format(name=getattr(self, "model_name")))
            # check if model params has been passed
            if "model_params" in kwargs:
                self.model = self.__class__.MODELS[getattr(self, "model_name")](
                    model_params=kwargs["model_params"]
                )
            # if no params, try and read params from the db using param_id
            else:
                raise NotImplementedError("Cannot yet read params from DB.")
        
        elif hasattr(self, "model") and not hasattr(self, "model_name"):
            self.model_name = self.model.experiment_config["model_name"]

        # load the model data object
        if not hasattr(self, "model_data"):
            data_config = self.__class__.DEFAULT_DATA_CONFIG
            data_config["tag"] = self.tag
            data_config["model_type"] = self.model_name
            self.model_data = ModelData(data_config=data_config)



class WritableInstance(Instance, DBWriter):
    """
    Adds functionality for reading and writing to the DB.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class ProductionInstance(WritableInstance, RunnableInstance):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
class LaqnTestInstance(RunnableInstance):
    """
    A quick test only on LAQN data that trains for 1 days and predicts for 1 day.
    """

    DEFAULT_DATA_CONFIG = {
        "train_start_date": "2020-01-29T00:00:00",
        "train_end_date": "2020-01-30T00:00:00",
        "pred_start_date": "2020-01-30T00:00:00",
        "pred_end_date": "2020-01-31T00:00:00",
        "include_satellite": False,
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
        "model_type": "svgp",
        "tag": "test",
    }

    DEFAULT_MODEL_PARAMS = {
        "jitter": 1e-5,
        "likelihood_variance": 0.1,
        "minibatch_size": 100,
        "n_inducing_points": 200,
        "restore": False,
        "train": True,
        "model_state_fp": None,
        "maxiter": 1,
        "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
    }

    def __init__(self, **kwargs):
        """
        Setup a quick test instance.

        Parameters
        ___

        secretfile : str
            Filepath to the secretfile.

        config_dir : str, optional
            Filepath to the directory of data.
        """
        # Get the model data
        super().__init__(
            model_data=ModelData(config=LaqnTestInstance.DEFAULT_DATA_CONFIG, **kwargs),
            model_name="svgp",
            tag="test",
            model=SVGP(
                model_params=LaqnTestInstance.DEFAULT_MODEL_PARAMS,
                tasks=self.model_data.config["species"],
            ),
            cluster_id="laptop",
            **kwargs,
        )
