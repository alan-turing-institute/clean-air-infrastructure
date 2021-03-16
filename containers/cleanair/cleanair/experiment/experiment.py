"""Experiments summerise multiple instances."""

from abc import abstractmethod
from datetime import datetime
import json
from logging import Logger
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import tensorflow as tf

from ..databases import get_columns_of_table
from ..databases.mixins import ResultTableMixin
from ..databases.mixins import (
    DataTableMixin,
    InstanceTableMixin,
    ModelTableMixin,
)
from ..loggers import get_logger
from ..mixins import InstanceMixin
from ..types import ExperimentConfig, ExperimentName
from ..utils import FileManager


class ExperimentMixin:
    """An experiment contains multiple instances.

    Attributes:
        name: Name of the experiment
        experiment_root: Root directory of experiments
    """

    # pylint: disable=invalid-name

    EXPERIMENT_CONFIG_JSON_FILENAME = "experiment_config.json"

    def __init__(
        self,
        name: ExperimentName,
        experiment_root: Path,
        logger: Logger = get_logger("experiment"),
    ):
        # super().__init__(**kwargs)
        self.name = name

        # create directory for saving files if it doesn't exist
        self.experiment_root = experiment_root
        self.experiment_root.mkdir(parents=False, exist_ok=True)
        (self.experiment_root / self.name.value).mkdir(parents=False, exist_ok=True)
        self._experiment_config_json_fp = (
            self.experiment_root
            / name.value
            / ExperimentMixin.EXPERIMENT_CONFIG_JSON_FILENAME
        )
        self.logger = logger

        # dictionaries to manage the experiment
        self._instances: Dict[str, InstanceMixin] = dict()
        self._file_managers: Dict[str, FileManager] = dict()

    def add_instance(
        self, instance: InstanceMixin, file_manager: Optional[FileManager] = None
    ) -> None:
        """Add a new instance to the experiment"""
        # add instance to dictionary of instances
        self._instances[instance.instance_id] = instance
        # create a new file manager for the instance
        if not file_manager:
            file_manager = self.create_file_manager_from_instance_id(
                instance.instance_id
            )
        self._file_managers[instance.instance_id] = file_manager

    def get_experiment_config(self) -> ExperimentConfig:
        """Get the experiment settings"""
        return ExperimentConfig(
            name=self.name, instance_id_list=self.get_instance_ids(),
        )

    def get_instance(self, instance_id: str) -> InstanceMixin:
        """Get an instance from the lookup table"""
        return self._instances[instance_id]

    def get_instance_ids(self) -> List[str]:
        """Get a list of instance ids for this experiment"""
        return list(self._instances.keys())

    def get_file_manager(self, instance_id: str) -> FileManager:
        """Get the file manager for the given instance"""
        return self._file_managers[instance_id]

    def get_num_instances(self) -> int:
        """Get the number of instances in the experiment"""
        return len(self._instances)

    def create_file_manager_from_instance_id(self, instance_id: str) -> FileManager:
        """Create a file manager from an instance id"""
        return FileManager(self.experiment_root / self.name.value / instance_id)

    def add_instances_from_file(self, instance_id_list: List[str]) -> None:
        """Read all instances from json files using file managers"""
        for instance_id in instance_id_list:
            file_manager = self.create_file_manager_from_instance_id(instance_id)
            instance = file_manager.read_instance_from_json()
            self.add_instance(instance, file_manager=file_manager)

    def read_experiment_config_from_json(self) -> ExperimentConfig:
        """Read the experiment config from a json file"""
        with open(self._experiment_config_json_fp, "r") as json_file:
            config_dict: Dict = json.load(json_file)
        return ExperimentConfig(**config_dict)

    def write_experiment_config_to_json(self) -> None:
        """Writes a json file that describes the experiment"""
        with open(self._experiment_config_json_fp, "w") as json_file:
            json.dump(self.get_experiment_config().dict(), json_file)


class SetupExperimentMixin(ExperimentMixin):
    """Setup an experiment by loading datasets or creating model parameters"""

    def __init__(self, name: ExperimentName, experiment_root: Path):
        super().__init__(name, experiment_root)
        self._test_dataset: Dict[str, Any] = dict()
        self._training_dataset: Dict[str, Any] = dict()
        self._data_config_lookup: Dict[str, Any] = dict()

    @abstractmethod
    def load_training_dataset(self, data_id: str) -> Any:
        """Use the data id to load the dataset"""

    @abstractmethod
    def load_test_dataset(self, data_id: str) -> Any:
        """Use the data id to load a test dataset"""

    def add_instance(
        self, instance: InstanceMixin, file_manager: Optional[FileManager] = None
    ) -> None:
        """Add the instance and create a lookup from data id to data config"""
        super().add_instance(instance, file_manager=file_manager)
        self._data_config_lookup[instance.data_id] = instance.data_config

    def __is_data_id_in_instances(self, data_id: str) -> bool:
        """Does the data id belond to an instance"""
        for _, instance in self._instances.items():
            if instance.data_id == data_id:
                return True
        return False

    def add_training_dataset(self, data_id: str, dataset: Tuple[Any, Any]) -> None:
        """Add a training dataset"""
        valid_data_id = self.__is_data_id_in_instances(data_id)
        if not valid_data_id:
            raise ValueError(
                "There are no instances in the experiment with data id:" + data_id
            )
        self._training_dataset[data_id] = dataset

    def add_test_dataset(self, data_id: str, dataset: Any) -> None:
        """Add a test dataset"""
        valid_data_id = self.__is_data_id_in_instances(data_id)
        if not valid_data_id:
            raise ValueError(
                "There are no instances in the experiment with data id:" + data_id
            )
        self._test_dataset[data_id] = dataset

    def load_datasets(self) -> None:
        """Load the datasets"""
        # TODO check uniqueness of data id
        data_id_list: List[str] = [
            instance.data_id for _, instance in self._instances.items()
        ]
        for data_id in data_id_list:
            training_dataset = self.load_training_dataset(data_id)
            test_dataset = self.load_test_dataset(data_id)
            self.add_training_dataset(data_id, training_dataset)
            self.add_test_dataset(data_id, test_dataset)

    def get_training_dataset(self, data_id: str) -> None:
        """Get a training dataset"""
        return self._training_dataset[data_id]

    def get_test_dataset(self, data_id: str) -> None:
        """Get a test dataset"""
        return self._test_dataset[data_id]


class RunnableExperimentMixin(SetupExperimentMixin):
    """Run the experiment"""

    @abstractmethod
    def save_result(self, instance_id) -> None:
        """Save the result of the instance"""

    @abstractmethod
    def load_model(self, instance_id: str) -> Any:
        """Load the model using the instance id"""

    @abstractmethod
    def train_model(self, instance_id: str) -> None:
        """Train the model"""

    @abstractmethod
    def predict_on_training_set(self, instance_id: str) -> Any:
        """Predict on the training set"""

    @abstractmethod
    def predict_on_test_set(self, instance_id: str) -> Any:
        """Predict on the test set"""

    def run_experiment(self) -> None:
        """Run the experiment"""
        # make sure to load the datasets first
        for instance_id, instance in self._instances.items():
            instance.fit_start_time = datetime.now()
            # tf.compat.v1.reset_default_graph()
            with tf.compat.v1.Graph().as_default():
                with tf.compat.v1.Session().as_default() as session:
                    # session.reset(graph)
                    self.load_model(instance_id)
                    self.train_model(instance_id)
                    self.predict_on_training_set(instance_id)
                    self.predict_on_test_set(instance_id)
                    self.save_result(instance_id)
                    session.close()


class UpdateExperimentMixin(ExperimentMixin):
    """An experiment that can write to databases"""

    @property
    @abstractmethod
    def data_table(self) -> DataTableMixin:
        """The data config table."""

    @property
    @abstractmethod
    def instance_table(self) -> InstanceTableMixin:
        """The instance table."""

    @property
    @abstractmethod
    def model_table(self) -> ModelTableMixin:
        """The modelling table."""

    @property
    @abstractmethod
    def result_table(self) -> ResultTableMixin:
        """The modelling table."""

    def update_remote_tables(self):
        """Update the instance, data and model tables."""
        # TODO would be nice to have an experiment table too
        # convert pydantic models to dictionaries

        self.logger.info("Writing instances, data config and model params to database")

        # get column names for each table
        data_config_cols = get_columns_of_table(self.data_table)
        instance_cols = get_columns_of_table(self.instance_table)
        model_cols = get_columns_of_table(self.model_table)

        # keep list or records to insert into DB
        data_config_records = list()
        instance_records = list()
        model_records = list()
        data_ids = set()
        param_ids = set()
        instance_ids = set()

        # add records to list
        for instance_id, instance in self._instances.items():
            instance_dict = instance.dict()
            if instance.data_id not in data_ids:
                data_ids.add(instance.data_id)
                data_config_records.append(
                    {key: instance_dict[key] for key in data_config_cols}
                )
            if instance.param_id not in param_ids:
                param_ids.add(instance.param_id)
                model_records.append({key: instance_dict[key] for key in model_cols})
            if instance_id not in instance_ids:
                instance_ids.add(instance_id)
                instance_records.append(
                    {key: instance_dict[key] for key in instance_cols}
                )

        # write records to the database
        self.commit_records(
            data_config_records, on_conflict="overwrite", table=self.data_table,
        )
        self.commit_records(
            model_records, on_conflict="overwrite", table=self.model_table,
        )
        self.commit_records(
            instance_records, on_conflict="overwrite", table=self.instance_table,
        )

    @abstractmethod
    def update_result_tables(self):
        """Update the result tables"""
