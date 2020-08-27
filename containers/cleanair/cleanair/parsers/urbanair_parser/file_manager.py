"""Functions for saving and loading models."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Dict, Union, Optional, TYPE_CHECKING
import json
import pickle
import typer
import pandas as pd
from ...loggers import red
from ...types import (
    DataConfig,
    FullDataConfig,
    MRDGPParams,
    Source,
    SVGPParams,
    TargetDict,
)
from .state import (
    state,
    DATA_CACHE,
    DATA_CONFIG,
    DATA_CONFIG_FULL,
    FORECAST_RESULT_PICKLE,
    MODEL_CACHE,
    MODEL_PARAMS,
    MODEL_TRAINING_PICKLE,
    MODEL_PREDICTION_PICKLE,
    RESULT_CACHE,
    TRAINING_RESULT_PICKLE,
)

if TYPE_CHECKING:
    import gpflow
    import tensorflow as tf
    from pydantic import BaseModel


class FileManager:
    """Class for managing files for the urbanair project."""

    def __init__(self, input_dir: Optional[Path] = None) -> None:
        if not input_dir:
            self.input_dir = DATA_CACHE
        elif not input_dir.is_dir():
            state["logger"].warning(f"{input_dir} is not a directory")
            raise typer.Abort()
        else:
            self.input_dir = input_dir

    def __save_pickle(self, obj: Any, pickle_path: Path) -> None:
        """Save an object to a filepath by pickling.

        Args:
            obj: The object to be pickled.
            pickle_path: The filepath.

        Notes:
            Create the parent directory of the pickle if it doesn't exist
            but do not create any grandparent directories.
        """
        pickle_path = self.input_dir.joinpath(*pickle_path.parts[-2:])
        if not pickle_path.parent.exists():
            pickle_path.parent.mkdir(parents=False)

        with open(pickle_path, "wb") as pickle_file:
            pickle.dump(obj, pickle_file)

    def __load_pickle(self, pickle_path: Path) -> Any:
        """Load either training or test data from a pickled file."""
        data_fp = self.input_dir.joinpath(*pickle_path.parts[-2:])

        if not data_fp.exists():
            state["logger"].warning("Data not found. Download and resave cache")
            raise typer.Abort()

        with data_fp.open("rb") as pickle_f:
            return pickle.load(pickle_f)

    def load_data_config(self, full: bool = False) -> Union[DataConfig, FullDataConfig]:
        """Load an existing configuration file"""

        if full:
            config = DATA_CONFIG_FULL
        else:
            config = DATA_CONFIG
        # TODO check that this is the correct FP
        config = self.input_dir.joinpath(config.parts[-1])

        if config.exists():
            with config.open("r") as config_f:
                if full:
                    return FullDataConfig(**json.load(config_f))

                return DataConfig(**json.load(config_f))

        if not full:
            typer.echo(f"{red(f'A model config does not exist. Run generate-config')}")
        else:
            typer.echo(
                f"{red(f'A full model config does not exist. Run generate-full-config')}"
            )
        raise typer.Abort()

    def load_training_data(self) -> Dict[Source, pd.DataFrame]:
        """Load training data from either the CACHE or input_dir"""
        return self.__load_pickle(MODEL_TRAINING_PICKLE)

    def load_test_data(self) -> Dict[Source, pd.DataFrame]:
        """Load test data from either the CACHE or input_dir"""
        return self.__load_pickle(MODEL_PREDICTION_PICKLE)

    def load_training_pred_from_pickle(self) -> TargetDict:
        """Load the predictions on the training set from a pickle."""
        return self.__load_pickle(TRAINING_RESULT_PICKLE)

    def load_forecast_from_pickle(self) -> TargetDict:
        """Load the predictions on the forecast set from a pickle."""
        return self.__load_pickle(FORECAST_RESULT_PICKLE)

    def load_forecast_from_csv(self, source: Source) -> pd.DataFrame:
        """Load the forecasts for a single source as csv."""
        result_fp = self.input_dir.joinpath(
            *RESULT_CACHE.parts[-1:], f"{source.value}_forecast.csv"
        )
        return pd.read_csv(result_fp)

    def load_training_pred_from_csv(self, source: Source) -> pd.DataFrame:
        """Load the training predictions for a single source from csv."""
        result_fp = self.input_dir.joinpath(
            *RESULT_CACHE.parts[-1:], f"{source.value}_training_pred.csv"
        )
        return pd.read_csv(result_fp)

    def __save_result_to_csv(
        self, result_df: pd.DataFrame, source: Source, filename: str
    ) -> None:
        """Save a result to file."""
        result_fp = self.input_dir.joinpath(*RESULT_CACHE.parts[-1:])
        if not result_fp.exists():
            result_fp.mkdir(parents=False, exist_ok=True)
        result_df.to_csv(result_fp / f"{source.value}_{filename}.csv", index=False)

    def save_forecast_to_csv(self, forecast_df: pd.DataFrame, source: Source) -> None:
        """Save the forecast dataframe to a csv.

        Args:
            forecast_df: DataFrame of forecasts for a given source.
            source: Source predicted at, e.g. laqn, hexgrid.
        """
        self.__save_result_to_csv(forecast_df, source, "forecast")

    def save_training_pred_to_csv(
        self, result_df: pd.DataFrame, source: Source
    ) -> None:
        """Save the predictions on the training set to a csv for a given source.

        Args:
            result_df: DataFrame of predictions for a given source on the training set.
            source: Source predicted at, e.g. laqn, hexgrid.
        """
        self.__save_result_to_csv(result_df, source, "training_pred")

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
        # use the load function to get the model from the filepath
        export_dir = self.input_dir.joinpath(*MODEL_CACHE.parts[-1:])
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
        export_dir = self.input_dir.joinpath(*MODEL_CACHE.parts[-1:])
        Path(export_dir).mkdir(exist_ok=True)
        save_fn(model, export_dir, model_name=model_name)

    def load_model_params(self, model_name: str) -> Union[MRDGPParams, SVGPParams]:
        """Load the model params from a json file."""
        params_fp = self.input_dir.joinpath(*MODEL_PARAMS.parts[-2:])
        with open(params_fp, "r") as params_file:
            params_dict = json.load(params_file)
        if model_name == "svgp":
            return SVGPParams(**params_dict)
        if model_name == "mrdgp":
            return MRDGPParams(**params_dict)
        raise ValueError("Must pass a valid model name.")

    def save_model_params(self, model_params: BaseModel) -> None:
        """Load the model params from a json file."""
        params_fp = self.input_dir.joinpath(*MODEL_PARAMS.parts[-2:])
        if not params_fp.parent.exists():
            params_fp.parent.mkdir(parents=False, exist_ok=True)
        with open(params_fp, "w") as params_file:
            json.dump(model_params.dict(), params_file, indent=4)

    def save_forecast_to_pickle(self, y_pred: TargetDict) -> None:
        """Save the results dataframe to a file."""
        self.__save_pickle(y_pred, FORECAST_RESULT_PICKLE)

    def save_training_pred_to_pickle(self, y_pred: TargetDict) -> None:
        """Save the training predictions to a pickled file."""
        self.__save_pickle(y_pred, TRAINING_RESULT_PICKLE)
