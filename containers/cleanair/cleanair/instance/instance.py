"""
Instances of models and data.
"""
from __future__ import annotations
import abc
from ..databases import DBWriter
from ..utils.hashing import hash_fn, instance_id_from_hash, get_git_hash


class Instance(DBWriter):
    """
    An instance is one model trained and fitted on some data.

    Attributes:
        instance_id: Uniquely identifies this instance.
        model_name: Name of the model for this instance.
        param_id: Uniquely identifies a parameter setting of the model.
            See `Instance.hash_param()`.
        data_id: Uniquely identifies a data configuration.
            See `Instance.hash_data()`.
        cluster_id: The id of the machine used to run the model.
        tag: Name of the instance type, e.g. 'production', 'test', 'validation'.
        git_hash: Git hash of the code version.
        fit_start_time: Datetime when the model started fitting.
            See `Instance.hash()`.
        secretfile: Path to secretfile.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        model_name: str,
        param_id: str,
        data_id: str,
        cluster_id: str,
        tag: str,
        fit_start_time: str,
        git_hash: str = None,
        secretfile: str = None,
        **kwargs,
    ):
        """
        The instance id is created using the model_name, param_id, data_id and git_hash.
        """
        # if the database is not available try and use local files
        super().__init__(secretfile=secretfile, **kwargs)

        self._model_name = model_name
        self._param_id = param_id
        self._data_id = data_id
        self._cluster_id = cluster_id
        self._tag = tag
        self._git_hash = git_hash if git_hash else get_git_hash()
        self._fit_start_time = fit_start_time
        self._instance_id = self.hash()

    @property
    def model_name(self) -> str:
        """Name of the model."""
        return self._model_name

    @model_name.setter
    def model_name(self, value: str):
        self._model_name = value
        self._instance_id = self.hash()

    @property
    def param_id(self) -> str:
        """Parameter id of the model."""
        return self._param_id

    @param_id.setter
    def param_id(self, value: str):
        self._param_id = value
        self._instance_id = self.hash()

    @property
    def data_id(self) -> str:
        """Data id of configuration of input data."""
        return self._data_id

    @data_id.setter
    def data_id(self, value: str):
        self._data_id = value
        self._instance_id = self.hash()

    @property
    def instance_id(self) -> str:
        """A unique id created by hashing the model_name, param_id, data_id and git_hash"""
        return instance_id_from_hash(
            self.model_name, self.param_id, self.data_id, self.git_hash
        )

    @property
    def git_hash(self) -> str:
        """
        A hash of the code version.
        Note there must exist a .git directory if you do not pass a git hash in the init.
        """
        return self._git_hash

    @git_hash.setter
    def git_hash(self, value: str):
        self._git_hash = value
        self._instance_id = self.hash()

    @property
    def tag(self) -> str:
        """A tag to categorise the instance."""
        return self._tag

    @tag.setter
    def tag(self, value: str):
        self._tag = value
        self._instance_id = self.hash()

    @property
    def cluster_id(self) -> str:
        """The id of the machine this instance was executed on."""
        return self._cluster_id

    @cluster_id.setter
    def cluster_id(self, value: str):
        self._cluster_id = value
        self._instance_id = self.hash()

    @property
    def fit_start_time(self) -> str:
        """The datetime when the model started fitting."""
        return self._fit_start_time

    @fit_start_time.setter
    def fit_start_time(self, value: str):
        self._fit_start_time = value
        self._instance_id = self.hash()

    def hash(self) -> str:
        """Hash the model name, param id, data id and git hash return a unique id."""
        hash_string = self.model_name + str(self.param_id)
        hash_string += self.git_hash + str(self.data_id)
        return hash_fn(hash_string)

    def to_dict(self) -> dict:
        """Returns a dictionary of the attributes of the Instance.

        Returns:
            Contains instance id, param id, data id, cluster id, fit start time,
                tag, git hash and model name as keys. Values are all strings.
        """
        return dict(
            instance_id=self.instance_id,
            param_id=self.param_id,
            data_id=self.data_id,
            cluster_id=self.cluster_id,
            fit_start_time=self.fit_start_time,
            tag=self.tag,
            git_hash=self.git_hash,
            model_name=self.model_name,
        )

    @abc.abstractmethod
    def update_remote_tables(self):
        """
        Update the instance table in the database.
        """
