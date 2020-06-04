"""
Instances of models and data.
"""
import abc
import json
import logging
import hashlib
import git
from ..databases import DBWriter


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
    ):
        """
        The instance id is created using the model_name, param_id, data_id and git_hash.
        """
        # if the database is not available try and use local files
        super().__init__(secretfile=secretfile)

        self._model_name = model_name
        self._param_id = param_id
        self._data_id = data_id
        self._cluster_id = cluster_id
        self._tag = tag

        if git_hash:
            # get git hash from parameter
            self._git_hash = git_hash
        else:
            try:
                # get the hash of the git repository
                self._git_hash = git.Repo(
                    search_parent_directories=True
                ).head.object.hexsha
            except git.InvalidGitRepositoryError as error:
                # catch exception and set to empty string
                error_message = (
                    "Could not find a git repository in the parent directory."
                )
                error_message += "Setting git_hash to empty string."
                logging.error(error_message)
                logging.error(error.__traceback__)
                self._git_hash = ""

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
        return self._instance_id

    @instance_id.setter
    def instance_id(self, value: str):
        hash_value = self.hash()
        if not value or value == hash_value:
            self._instance_id = hash_value
        else:
            raise ValueError(
                "The instance id you passed does not match the hash of the instance."
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
        return Instance.hash_fn(hash_string)

    @staticmethod
    def hash_fn(hash_string: str) -> str:
        """Uses sha256 to hash the given string.

        Args:
            hash_string: The string to hash.

        Returns:
            The hash of the given string.
        """
        sha_fn = hashlib.sha256()
        sha_fn.update(bytearray(hash_string, "utf-8"))
        return sha_fn.hexdigest()

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

    @staticmethod
    def hash_dict(value: dict) -> str:
        """Dumps a dictionary to json string then hashes that string.

        Args:
            value: A dictionary to hash. Keys and values must be compliant with json types.

        Returns:
            The hash of dictionary.

        Notes:
            Any lists within the dictionary are sorted.
            This means the following two dictionaries `A` and `B` will be hashed to the same string:

            >>> A = dict(key=["a", "b"])
            >>> B = dict(key=["b", "a"])
        """
        # it is ESSENTIAL to sort by keys when creating hashes!
        sorted_values = value.copy()
        for key in sorted_values:
            if isinstance(sorted_values[key], list):
                sorted_values[key].sort()
        hash_string = json.dumps(sorted_values, sort_keys=True)
        return Instance.hash_fn(hash_string)
