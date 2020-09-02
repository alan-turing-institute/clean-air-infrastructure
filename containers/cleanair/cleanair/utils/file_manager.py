"""Functions for saving and loading models."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Dict, Union, Optional, TYPE_CHECKING
import json
import pickle
import pandas as pd
from ..loggers import get_logger
from ..types import (
    DataConfig,
    FullDataConfig,
    ModelName,
    MRDGPParams,
    Source,
    SVGPParams,
    TargetDict,
)

if TYPE_CHECKING:
    import gpflow
    import tensorflow as tf
    from pydantic import BaseModel


class FileManager:
    """Class for managing files for the urbanair project."""

    # data config / train test data
    DATASET = Path("dataset")
    DATA_CONFIG = DATASET / "data_config.json"
    DATA_CONFIG_FULL = DATASET / "data_config_full.json"
    TRAINING_DATA_PICKLE = DATASET / "training_dataset.pkl"
    TEST_DATA_PICKLE = DATASET / "test_dataset.pkl"

    # model filepaths
    MODEL = Path("model")
    MODEL_PARAMS = MODEL / "model_params.json"

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
        """Load either training or test data from a pickled file."""
        self.logger.debug("Loading object from pickle file from %s", pickle_path)
        if not pickle_path.exists():
            raise FileNotFoundError(f"Could not find file at path {pickle_path}")

        with pickle_path.open("rb") as pickle_f:
            return pickle.load(pickle_f)

    def load_data_config(self, full: bool = False) -> Union[DataConfig, FullDataConfig]:
        """Load an existing configuration file"""
        self.logger.info("Loading the data config from file.")

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
        """Save a data config to file."""
        self.logger.info("Saving the data config to a file.")
        if full:
            config = self.input_dir / FileManager.DATA_CONFIG_FULL
        else:
            config = self.input_dir / FileManager.DATA_CONFIG

        with config.open("w") as config_f:
            config_f.write(data_config.json(indent=4))

    def load_training_data(self) -> Dict[Source, pd.DataFrame]:
        """Load training data from either the CACHE or input_dir"""
        self.logger.info("Loading the training data from a pickle.")
        return self.__load_pickle(self.input_dir / FileManager.TRAINING_DATA_PICKLE)

    def load_test_data(self) -> Dict[Source, pd.DataFrame]:
        """Load test data from either the CACHE or input_dir"""
        self.logger.info("Loading the test data from a pickle.")
        return self.__load_pickle(self.input_dir / FileManager.TEST_DATA_PICKLE)

    def load_pred_training_from_pickle(self) -> TargetDict:
        """Load the predictions on the training set from a pickle."""
        self.logger.info("Loading the predictions on the training set from a pickle.")
        return self.__load_pickle(self.input_dir / FileManager.PRED_TRAINING_PICKLE)

    def load_forecast_from_pickle(self) -> TargetDict:
        """Load the predictions on the forecast set from a pickle."""
        self.logger.info("Loading the prediction on the forecast period from a pickle.")
        return self.__load_pickle(self.input_dir / FileManager.PRED_FORECAST_PICKLE)

    def load_forecast_from_csv(self, source: Source) -> pd.DataFrame:
        """Load the forecasts for a single source as csv."""
        self.logger.info("Loading the forecasts for %s from csv.", source)
        result_fp = self.input_dir / FileManager.RESULT / f"{source}_pred_forecast.csv"
        return pd.read_csv(result_fp)

    def save_training_data(self, training_data: Dict[Source, pd.DataFrame]) -> None:
        """Save training data as a pickle."""
        self.logger.info(
            "Saving the training data to a pickle. Sources are %s",
            list(training_data.keys()),
        )
        self.__save_pickle(
            training_data, self.input_dir / FileManager.TRAINING_DATA_PICKLE
        )

    def save_test_source_to_csv(self, test_df: pd.DataFrame, source: Source) -> None:
        """Save the test dataframe to csv. The dataframe should be for just one source."""
        filepath = self.input_dir / FileManager.DATASET / f"{source}_test.csv"
        test_df.to_csv(filepath, index=False)

    def load_test_source_from_csv(self, source: Source) -> pd.DataFrame:
        """Load a test dataframe from csv for a given source."""
        filepath = self.input_dir / FileManager.DATASET / f"{source}_test.csv"
        return pd.read_csv(filepath)

    def save_training_source_to_csv(
        self, training_df: pd.DataFrame, source: Source
    ) -> None:
        """Save the dataframe to csv. The dataframe should be for just one source."""
        filepath = self.input_dir / FileManager.DATASET / f"{source}_training.csv"
        training_df.to_csv(filepath, index=False)

    def load_training_source_from_csv(self, source: Source) -> pd.DataFrame:
        """Load a dataframe from csv for a given source."""
        filepath = self.input_dir / FileManager.DATASET / f"{source}_training.csv"
        return pd.read_csv(filepath)

    def save_test_data(self, test_data: Dict[Source, pd.DataFrame]) -> None:
        """Save test data as a pickle."""
        self.logger.info(
            "Saving the test data to a pickle. Sources are %s", list(test_data.keys())
        )
        self.__save_pickle(test_data, self.input_dir / FileManager.TEST_DATA_PICKLE)

    def load_pred_training_from_csv(self, source: Source) -> pd.DataFrame:
        """Load the training predictions for a single source from csv."""
        self.logger.info(
            "Loading predictions on the training set on %s from csv", source
        )
        result_fp = self.input_dir / FileManager.RESULT / f"{source}_pred_training.csv"
        return pd.read_csv(result_fp)

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

    def save_training_pred_to_csv(
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

    def load_model(
        self,
        load_fn: Callable[[Path], gpflow.models.GPModel],
        compile_model: bool = True,
        model_name: str = "model",
        tf_session: Optional[tf.compat.v1.Session] = None,
    ) -> gpflow.models.GPModel:
        """Load a model from the cache.

        Args:
            load_fn: Loads a gpflow model from a filepath. See `cleanair.utils.tf1.load_gpflow1_model_from_file`.

        Keyword args:
            compile_model: If true compile the GPflow model.
            model_name: Name of the model.
            tf_session: Optional[tf.compat.v1.Session] = None,

        Returns:
            A gpflow model.
        """
        self.logger.info("Loading a model from a file.")
        # use the load function to get the model from the filepath
        export_dir = self.input_dir / FileManager.MODEL
        model = load_fn(
            export_dir,
            compile_model=compile_model,
            model_name=model_name,
            tf_session=tf_session,
        )
        return model

    def save_model(
        self,
        model: gpflow.models.GPModel,
        save_fn: Optional[Callable[[gpflow.models.GPModel, Path], None]],
        model_name: Optional[str] = "model",
    ) -> None:
        """Save a model to file.

        Args:
            model: A gpflow model.
            save_fn: A callable function that takes two arguments (model, filepath) and writes the model to a file.

        Keyword args:
            model_name: Name of the model.
        """
        self.logger.info("Saving model to file.")
        export_dir = self.input_dir / FileManager.MODEL
        save_fn(model, export_dir, model_name=model_name)

    def load_model_params(
        self, model_name: ModelName
    ) -> Union[MRDGPParams, SVGPParams]:
        """Load the model params from a json file."""
        self.logger.info("Loading model parameters from a json file for %s", model_name)
        params_fp = self.input_dir / FileManager.MODEL_PARAMS
        with open(params_fp, "r") as params_file:
            params_dict = json.load(params_file)
        if model_name == ModelName.svgp:
            return SVGPParams(**params_dict)
        if model_name == ModelName.mrdgp:
            return MRDGPParams(**params_dict)
        raise ValueError("Must pass a valid model name.")

    def save_model_params(self, model_params: BaseModel) -> None:
        """Load the model params from a json file."""
        self.logger.info("Saving model params to a json file.")
        params_fp = self.input_dir / FileManager.MODEL_PARAMS
        with open(params_fp, "w") as params_file:
            json.dump(model_params.dict(), params_file, indent=4)

    def save_forecast_to_pickle(self, y_pred: TargetDict) -> None:
        """Save the results dataframe to a file."""
        self.logger.info("Saving the forecasts to a pickle.")
        self.__save_pickle(y_pred, self.input_dir / FileManager.PRED_FORECAST_PICKLE)

    def save_training_pred_to_pickle(self, y_pred: TargetDict) -> None:
        """Save the training predictions to a pickled file."""
        self.logger.info("Saving the predictions on the training set to a pickle.")
        self.__save_pickle(y_pred, self.input_dir / FileManager.PRED_TRAINING_PICKLE)
