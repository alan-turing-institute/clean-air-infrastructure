"""
Instances of models and data.
"""
import hashlib
import git
from ...models import SVGP, MRDGP

class Instance():
    """
    An instance is one model trained and fitted on some data.
    """

    MODELS = {
        'svgp': SVGP,
        'mr_dgp': MRDGP,
    }

    def __init__(self, **kwargs):
        """

        Parameters
        ___

        model_name : str, optional
            Name of the model for this instance.

        param_id : str, optional
            Uniquely identifies a parameter setting of the model.
            See `Instance.hash_param()`.

        data_id : str, optional
            Uniquely identifies a data configuration.
            See `Instance.hash_data()`.

        cluster_id : str, optional
            The id of the machine used to run the model.

        tag : str, optional
            Name of the instance type, e.g. 'production', 'test', 'validation'.

        hash : str, optional
            Git hash of the code version.

        fit_start_time : str, optional
            Datetime when the model started fitting.

        instance_id : str, optional
            Uniquely identifies this instance.
            See `Instance.hash_instance()`.

        Other Parameters
        ___

        kwargs : dict, optional
            Further arguments to pass, e.g. model_params, data_config.

        """
        self._model_name = kwargs.get("model_name", None)
        self._param_id = kwargs.get("param_id", None)
        self._data_id = kwargs.get("data_id", None)
        self._cluster_id = kwargs.get("cluster_id", None)
        self._tag = kwargs.get("tag", None)
        self._git_hash = kwargs.get("git_hash", git.Repo(search_parent_directories=True).head.object.hexsha)
        self._fit_start_time = kwargs.get("fit_start_time", None)
        self._instance_id = kwargs.get("instance_id", self.__hash__())

    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self, value):
        self._model_name = value
        self.instance_id = None     # this will update in setter

    @property
    def param_id(self):
        return self._param_id

    @param_id.setter
    def param_id(self, value):
        self._param_id = value
        self.instance_id = None     # this will update in setter

    @property
    def data_id(self):
        return self._data_id

    @data_id.setter
    def data_id(self, value):
        self._data_id = value
        self.instance_id = None     # this will update in setter

    @property
    def instance_id(self):
        return self._instance_id

    @instance_id.setter
    def instance_id(self, value):
        hash_value = self.__hash__()
        if not value or value == hash_value:
            self._instance_id = hash_value
        else:
            raise ValueError("The instance id you passed does not match the hash of the instance.")

    @property
    def git_hash(self):
        return self._git_hash

    @git_hash.setter
    def git_hash(self, value):
        self._git_hash = value
        self.instance_id = None     # this will update in setter

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, value):
        self._tag = value
        self.instance_id = None     # this will update in setter

    @property
    def cluster_id(self):
        return self._cluster_id

    @cluster_id.setter
    def cluster_id(self, value):
        self._cluster_id = value
        self.instance_id = None     # this will update in setter

    @property
    def fit_start_time(self):
        return self._fit_start_time

    @fit_start_time.setter
    def fit_start_time(self, value):
        self._fit_start_time = value
        self.instance_id = None     # this will update in setter

    def __hash__(self):
        hash_string = self.model_name + str(self.param_id) 
        hash_string += self.git_hash + str(self.data_id)
        return Instance.hash_fn(hash_string)

    @staticmethod
    def hash_fn(hash_string):
        sha_fn = hashlib.sha256()
        sha_fn.update(bytearray(hash_string, "utf-8"))
        return sha_fn.hexdigest()
