"""Functions for saving and loading models."""

from __future__ import annotations
from typing import Any, Dict, Union, Optional, TYPE_CHECKING
import json
import pickle
import typer
from ...loggers import red
from ...types import (
    BaseConfig, FullConfig, MRDGPParams, Source, SVGPParams, TargetDict
)
from .state import (
    state,
    DATA_CACHE,
    DATA_CONFIG,
    DATA_CONFIG_FULL,
    FORECAST_RESULT_PICKLE,
    MODEL_PARAMS,
    MODEL_TRAINING_PICKLE,
    MODEL_PREDICTION_PICKLE,
    RESULT_CACHE,
    TRAINING_RESULT_PICKLE,
)

if TYPE_CHECKING:
    from pathlib import Path
    import pandas as pd
    from pydantic import BaseModel


class FileManager():
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

    def load_data_config(self, full: bool = False) -> Union[BaseConfig, FullConfig]:
        """Load an existing configuration file"""

        if full:
            config = DATA_CONFIG_FULL
        else:
            config = DATA_CONFIG

        config = self.input_dir.joinpath(config.parts[-1])

        if config.exists():
            with config.open("r") as config_f:
                if full:
                    return FullConfig(**json.load(config_f))

                return BaseConfig(**json.load(config_f))

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

    def save_forecast_to_csv(
        self, forecast_df: pd.DataFrame, source: Source
    ) -> None:
        """Save the forecast dataframe to a csv.

        Args:
            forecast_df: DataFrame of forecasts for a given source.
            source: Source predicted at, e.g. laqn, hexgrid.
        """
        result_fp = self.input_dir.joinpath(*RESULT_CACHE.parts[-1:])
        forecast_df.to_csv(result_fp / f"{source.value}_forecast.csv")


    def save_training_result_to_csv(self, result_df: pd.DataFrame, source: Source) -> None:
        """Save the predictions on the training set to a csv for a given source.

        Args:
            result_df: DataFrame of predictions for a given source on the training set.
            source: Source predicted at, e.g. laqn, hexgrid.
        """
        result_fp = self.input_dir.joinpath(*RESULT_CACHE.parts[-1:])
        result_df.to_csv(result_fp / f"{source.value}_training_results.csv")

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
        params_fp = self.input_dir.joinpath(*MODEL_PARAMS.parts[-1:])
        with open(params_fp, "w") as params_file:
            json.dump(model_params.dict(), params_file, indent=4)

    def save_forecast_to_pickle(self, y_pred: TargetDict) -> None:
        """Save the results dataframe to a file."""
        self.__save_pickle(y_pred, FORECAST_RESULT_PICKLE)

    def save_training_result_to_pickle(self, y_pred: TargetDict) -> None:
        """Save the training results to a pickled file."""
        self.__save_pickle(y_pred, TRAINING_RESULT_PICKLE)
