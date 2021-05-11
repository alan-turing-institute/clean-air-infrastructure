"""Functions for saving and loading models"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING
import json
import pickle
import pandas as pd
from ..loggers import get_logger
from ..mixins import InstanceMixin
from ..types import (
    DataConfig,
    FullDataConfig,
    ModelName,
    MRDGPParams,
    Source,
    SVGPParams,
    TargetDict,
    model_params_from_dict,
)

if TYPE_CHECKING:
    # turn off tensorflow warnings for gpflow
    import os
    import tensorflow as tf

    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
    import gpflow  # pylint: disable=wrong-import-position,wrong-import-order
    from pydantic import BaseModel

# pylint: disable=R0904
class FileManager:
    """Class for managing files for the urbanair project"""

    # instance filepaths
    INSTANCE_JSON = Path("instance.json")

    # data config / train test data
    DATASET = Path("dataset")
    DATA_CONFIG = DATASET / "data_config.json"
    DATA_CONFIG_FULL = DATASET / "data_config_full.json"
    TRAINING_DATA_PICKLE = DATASET / "training_dataset.pkl"
    TEST_DATA_PICKLE = DATASET / "test_dataset.pkl"

    # model filepaths
    MODEL = Path("model")
    MODEL_PARAMS = MODEL / "model_params.json"
    MODEL_ELBO_JSON = MODEL / "elbo.json"

    # forecasts / results / predictions
    RESULT = Path("result")
    PRED_FORECAST_PICKLE = RESULT / "pred_forecast.pkl"
    PRED_TRAINING_PICKLE = RESULT / "pred_training.pkl"

    def __init__(self, input_dir: Path) -> None:
        if not hasattr(self, "logger"):
            self.logger = get_logger("file_manager")
        input_dir.mkdir(parents=False, exist_ok=True)
        if not input_dir.is_dir():
            raise IOError(f"{input_dir} is not a directory")
        self.input_dir = input_dir

        # create subdirectories
        (self.input_dir / FileManager.DATASET).mkdir(exist_ok=True, parents=False)
        (self.input_dir / FileManager.MODEL).mkdir(exist_ok=True, parents=False)
        (self.input_dir / FileManager.RESULT).mkdir(exist_ok=True, parents=False)

    def __save_pickle(self, obj: Any, pickle_path: Path) -> None:
        """Save an object to a filepath by pickling.

        Args:
            obj: The object to be pickled.
            pickle_path: The filepath.

        Notes:
            Create the parent directory of the pickle if it doesn't exist
            but do not create any grandparent directories.
        """
        self.logger.debug("Saving object to pickle file at %s", pickle_path)
        with open(pickle_path, "wb") as pickle_file:
            pickle.dump(obj, pickle_file)

    def __load_pickle(self, pickle_path: Path) -> Any:
        """Load either training or test data from a pickled file"""
        self.logger.debug("Loading object from pickle file from %s", pickle_path)
        if not pickle_path.exists():
            raise FileNotFoundError(f"Could not find file at path {pickle_path}")

        with pickle_path.open("rb") as pickle_f:
            return pickle.load(pickle_f)

    def load_data_config(self, full: bool = False) -> Union[DataConfig, FullDataConfig]:
        """Load an existing configuration file"""
        self.logger.debug("Loading the data config from file")

        if full:
            config = self.input_dir / FileManager.DATA_CONFIG_FULL
        else:
            config = self.input_dir / FileManager.DATA_CONFIG

        if config.exists():
            with config.open("r") as config_f:
                if full:
                    return FullDataConfig(**json.load(config_f))

                return DataConfig(**json.load(config_f))

        if not full:
            message = "A data config does not exist. Run generate-config"
        else:
            message = "A full data config does not exist. Run generate-full-config"
        raise FileNotFoundError(message)

    def save_data_config(
        self, data_config: Union[DataConfig, FullDataConfig], full: bool = False
    ) -> None:
        """Save a data config to file"""
        self.logger.debug("Saving the data config to a file")
        if full:
            config = self.input_dir / FileManager.DATA_CONFIG_FULL
        else:
            config = self.input_dir / FileManager.DATA_CONFIG

        with config.open("w") as config_f:
            config_f.write(data_config.json(indent=4))

    def load_training_data(self) -> Dict[Source, pd.DataFrame]:
        """Load training data from either the CACHE or input_dir"""
        self.logger.debug("Loading the training data from a pickle")
        return self.__load_pickle(self.input_dir / FileManager.TRAINING_DATA_PICKLE)

    def load_test_data(self) -> Dict[Source, pd.DataFrame]:
        """Load test data from either the CACHE or input_dir"""
        self.logger.debug("Loading the test data from a pickle")
        return self.__load_pickle(self.input_dir / FileManager.TEST_DATA_PICKLE)

    def load_pred_training_from_pickle(self) -> TargetDict:
        """Load the predictions on the training set from a pickle"""
        self.logger.debug("Loading the predictions on the training set from a pickle")
        return self.__load_pickle(self.input_dir / FileManager.PRED_TRAINING_PICKLE)

    def load_forecast_from_pickle(self) -> TargetDict:
        """Load the predictions on the forecast set from a pickle"""
        self.logger.debug("Loading the prediction on the forecast period from a pickle")
        return self.__load_pickle(self.input_dir / FileManager.PRED_FORECAST_PICKLE)

    def save_training_data(self, training_data: Dict[Source, pd.DataFrame]) -> None:
        """Save training data as a pickle"""
        self.logger.debug(
            "Saving the training data to a pickle. Sources are %s",
            list(training_data.keys()),
        )
        self.__save_pickle(
            training_data, self.input_dir / FileManager.TRAINING_DATA_PICKLE
        )

    def save_test_source_to_csv(self, test_df: pd.DataFrame, source: Source) -> None:
        """Save the test dataframe to csv. The dataframe should be for just one source"""
        filepath = self.input_dir / FileManager.DATASET / f"{source}_test.csv"
        test_df.to_csv(filepath, index=False)

    def load_test_source_from_csv(self, source: Source) -> pd.DataFrame:
        """Load a test dataframe from csv for a given source"""
        filepath = self.input_dir / FileManager.DATASET / f"{source}_test.csv"
        return pd.read_csv(filepath)

    def save_training_source_to_csv(
        self, training_df: pd.DataFrame, source: Source
    ) -> None:
        """Save the dataframe to csv. The dataframe should be for just one source"""
        filepath = self.input_dir / FileManager.DATASET / f"{source}_training.csv"
        training_df.to_csv(filepath, index=False)

    def load_training_source_from_csv(self, source: Source) -> pd.DataFrame:
        """Load a dataframe from csv for a given source"""
        filepath = self.input_dir / FileManager.DATASET / f"{source}_training.csv"
        return pd.read_csv(filepath)

    def save_test_data(self, test_data: Dict[Source, pd.DataFrame]) -> None:
        """Save test data as a pickle"""
        self.logger.debug(
            "Saving the test data to a pickle. Sources are %s", list(test_data.keys())
        )
        self.__save_pickle(test_data, self.input_dir / FileManager.TEST_DATA_PICKLE)

    def load_model(
        self,
        load_fn: Callable[[Path, ModelName], gpflow.models.GPModel],
        model_name: ModelName,
        compile_model: bool = True,
        tf_session: Optional[tf.compat.v1.Session] = None,
    ) -> gpflow.models.GPModel:
        """Load a model from the cache.

        Args:
            load_fn: Loads a gpflow model from a filepath. See `cleanair.utils.tf1.load_gpflow1_model_from_file`.
            model_name: Name of the model.

        Keyword args:
            compile_model: If true compile the GPflow model.
            tf_session: Optional[tf.compat.v1.Session] = None,

        Returns:
            A gpflow model.
        """
        self.logger.debug("Loading a model from a file")
        # use the load function to get the model from the filepath
        export_dir = self.input_dir / FileManager.MODEL
        model = load_fn(
            export_dir, model_name, compile_model=compile_model, tf_session=tf_session,
        )
        return model

    def save_model(
        self,
        model: gpflow.models.GPModel,
        save_fn: Callable[[gpflow.models.GPModel, Path, ModelName], None],
        model_name: ModelName,
    ) -> None:
        """Save a model to file.

        Args:
            model: A gpflow model.
            save_fn: A callable function that takes two arguments (model, filepath) and writes the model to a file.
            model_name: Name of the model.
        """
        self.logger.debug("Saving model to file")
        export_dir = self.input_dir / FileManager.MODEL
        save_fn(model, export_dir, model_name)

    def load_model_params(
        self, model_name: ModelName
    ) -> Union[MRDGPParams, SVGPParams]:
        """Load the model params from a json file"""
        self.logger.debug(
            "Loading model parameters from a json file for %s", model_name
        )
        params_fp = self.input_dir / FileManager.MODEL_PARAMS
        with open(params_fp, "r") as params_file:
            params_dict = json.load(params_file)
        return model_params_from_dict(model_name, params_dict)

    def save_model_params(self, model_params: BaseModel) -> None:
        """Load the model params from a json file"""
        self.logger.debug("Saving model params to a json file")
        params_fp = self.input_dir / FileManager.MODEL_PARAMS
        with open(params_fp, "w") as params_file:
            json.dump(model_params.dict(), params_file, indent=4)

    def save_forecast_to_pickle(self, y_pred: TargetDict) -> None:
        """Save the results dataframe to a file"""
        self.logger.debug("Saving the forecasts to a pickle")
        self.__save_pickle(y_pred, self.input_dir / FileManager.PRED_FORECAST_PICKLE)

    def save_pred_training_to_pickle(self, y_pred: TargetDict) -> None:
        """Save the training predictions to a pickled file"""
        self.logger.debug("Saving the predictions on the training set to a pickle")
        self.__save_pickle(y_pred, self.input_dir / FileManager.PRED_TRAINING_PICKLE)

    def __save_result_to_csv(
        self, result_df: pd.DataFrame, source: Source, filename: str
    ) -> None:
        """Save a result to file."""
        result_fp = self.input_dir / FileManager.RESULT
        result_df.to_csv(result_fp / f"{source}_{filename}.csv", index=False)

    def save_forecast_to_csv(self, forecast_df: pd.DataFrame, source: Source) -> None:
        """Save the forecast dataframe to a csv.

        Args:
            forecast_df: DataFrame of forecasts for a given source.
            source: Source predicted at, e.g. laqn, hexgrid.
        """
        self.logger.info(
            "Saving a forecast for %s to csv. Dataframe has %s rows.",
            source,
            len(forecast_df),
        )
        self.__save_result_to_csv(forecast_df, source, "pred_forecast")

    def save_pred_training_to_csv(
        self, result_df: pd.DataFrame, source: Source
    ) -> None:
        """Save the predictions on the training set to a csv for a given source.

        Args:
            result_df: DataFrame of predictions for a given source on the training set.
            source: Source predicted at, e.g. laqn, hexgrid.
        """
        self.logger.info(
            "Saving predictions on training set for %s to csv. Dataframe has %s rows.",
            source,
            len(result_df),
        )
        self.__save_result_to_csv(result_df, source, "pred_training")

    def __load_result_from_csv(self, source: Source, filename: str) -> pd.DataFrame:
        """Load a result (either training or test) from csv."""
        result_fp = self.input_dir / FileManager.RESULT / f"{source}_{filename}.csv"
        return pd.read_csv(result_fp)

    def load_forecast_from_csv(self, source: Source) -> pd.DataFrame:
        """Load the forecasts for a single source as csv.

        Args:
            source: Source predicted at, e.g. laqn, hexgrid.
        """
        self.logger.info("Loading the forecasts for %s from csv.", source)
        return self.__load_result_from_csv(source, "pred_forecast")

    def load_pred_training_from_csv(self, source: Source) -> pd.DataFrame:
        """Load the predictions on the training set for a given source from csv.

        Args:
            source: Source predicted at, e.g. laqn, hexgrid.
        """
        self.logger.info(
            "Loading the prediction on the training set for %s from csv.", source
        )
        return self.__load_result_from_csv(source, "pred_training")

    def save_elbo(self, elbo: List[float]) -> None:
        """Save a list of floats that record the ELBO"""
        self.logger.info("Saving the ELBO to file")
        elbo_fp = self.input_dir / FileManager.MODEL_ELBO_JSON
        with open(elbo_fp, "w") as elbo_file:
            json.dump(elbo, elbo_file)

    def load_elbo(self) -> List[float]:
        """Load the list of ELBO floats from json file"""
        self.logger.info("Reading the ELBO from json file")
        elbo_fp = self.input_dir / FileManager.MODEL_ELBO_JSON
        with open(elbo_fp, "r") as elbo_file:
            return json.load(elbo_file)

    def write_instance_to_json(self, instance: InstanceMixin) -> None:
        """Writes an instance to a json file"""
        with open(self.input_dir / self.INSTANCE_JSON, "w") as json_file:
            json.dump(instance.dict(), json_file)

    def read_instance_from_json(self) -> InstanceMixin:
        """Reads a dictionary containing the instance from a json file"""
        with open(self.input_dir / self.INSTANCE_JSON, "r") as json_file:
            instance_dict: Dict = json.load(json_file)
            model_name = instance_dict.get("model_name")
            model_params = model_params_from_dict(
                model_name, instance_dict.get("model_params")
            )
            fit_start_time = datetime.fromisoformat(instance_dict.get("fit_start_time"))
            data_config_dict = instance_dict.get("data_config")
            data_config = FullDataConfig(**data_config_dict)
            instance = InstanceMixin(
                data_config=data_config,
                model_name=model_name,
                model_params=model_params,
                cluster_id=instance_dict.get("cluster_id"),
                fit_start_time=fit_start_time,
                git_hash=instance_dict.get("git_hash"),
                preprocessing=instance_dict.get("preprocessing"),
                tag=instance_dict.get("tag"),
            )
            return instance
