"""
The interface for London air quality models.
"""

from typing import Callable, List, Optional, Union
from abc import abstractmethod
import numpy as np
from nptyping import Float64, NDArray
from ..loggers import get_logger
from ..types import FeaturesDict, NDArrayTuple, Species, TargetDict, SVGPParams, MRDGPParams


class ModelMixin:
    """
    A base class for models.
    All other air quality models should extend this class.
    """

    def __init__(
        self,
        model_params: Union[MRDGPParams, SVGPParams],
        batch_size: int = 100,
        refresh: int = 10,
        tasks: Optional[List] = None,
        **kwargs
    ) -> None:
        """Initialise a model with parameters and settings.

        Keyword args:
            batch_size: Size of batch for prediction.
            model_params: Initialising parameters of the model, kernel and optimizer.
            refresh: How often to print out the ELBO.
            tasks: The name of the tasks (pollutants) we are modelling. Default is ['NO2'].
        """
        self.model_params = model_params

        # get the tasks we will be predicting at
        self.tasks = [Species.NO2] if tasks is None else tasks
        if len(self.tasks) > 1:
            raise NotImplementedError("Multiple pollutants not supported yet.")
        # other misc arguments
        self.model = None
        self.epoch = 0
        self.batch_size = batch_size
        self.refresh = refresh
        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @abstractmethod
    def fit(self, x_train: FeaturesDict, y_train: TargetDict) -> None:
        """
        Fit the model to some training data.

        Args:
            x_train: Keys are sources. Values are numpy arrays.
            y_train: Keys are sources. Values are a dict of pollutants and numpys.

        Examples:
            >>> x_train = {
                'laqn' : x_laqn,
                'satellite' : x_satellite
            }
            >>> y_train = {
                'laqn' : {
                    'NO2' : y_laqn_NO2,
                    'PM10' : y_laqn_pm10
                },
                'satellite' : {
                    'NO2' : y_satellite_NO2,
                    'PM10' : y_satellite_pm10
                }
            }
            >>> model.fit(x_train, y_train)

        Notes:
            Every value (e.g. `x_laqn`, `y_satellite_NO2`, etc) is a numpy array.
            The shapes are given in the table below:

            +-------------------+---------+
            | `x_laqn`          | (NxD) |
            +-------------------+---------+
            | `x_satellite`     | (MxSxD) |
            +-------------------+---------+
            | `y_laqn_*`        | (Nx1)   |
            +-------------------+---------+
            | `y_satellite_*`   | (Mx1)   |
            +-------------------+---------+

            where N is the number of laqn observations, D is the number of features,
            S is the discretization amount,
            M is the number of satellite observations, and * represents a pollutant name.
        """

    @abstractmethod
    def predict(self, x_test: FeaturesDict) -> TargetDict:
        """Predict using the model.

        Args:
            x_test: Keys are sources. Values are numpy arrays.

        Returns:
            y_pred: Keys are sources. Values are dicts of pollutants for keys and dict for values.

        Examples:
            >>> x_test = {
                'laqn' : np.array,
                'satellite' : np.array
            }
            >>> y_pred = model.predict(x_test)
            >>> json.dumps(y_pred)
            {
                'laqn' : {
                    'NO2' : {
                        'mean' : np.array,
                        'var' : np.array
                    },
                    'PM10' : {
                        'mean' : np.array,
                        'var' : np.array
                    }
                }
            }
        """
        ModelMixin.check_test_set_is_valid(x_test)

    @staticmethod
    def check_training_set_is_valid(x_train: FeaturesDict, y_train: TargetDict) -> None:
        """
        Check the format of x_train and y_train dictionaries are correct.

        Args:
            x_train: Dictionary containing X training data.
            y_train: Dictionary containing Y training data.

        Raises:
            KeyError: If there are no keys in x_train or y_train.
            ValueError: If the shape of x_train or y_train are incorrect.
        """
        if len(x_train) == 0:
            raise KeyError("x_train must have at least one data source.")
        if len(y_train) == 0:
            raise KeyError("y_train must have at least one data source.")
        # check the shape of numpy arrays
        for source in y_train:
            for pollutant in y_train[source]:
                # check that each pollutant has the right shape
                if y_train[source][pollutant].shape[1] != 1:
                    error_message = (
                        "The shape of {p} numpy array for source {s} must be Nx1. "
                    )
                    error_message += "The shape you gave was Nx{k}"
                    error_message.format(
                        p=pollutant, s=source, k=y_train[source][pollutant].shape[1]
                    )
                    raise ValueError(error_message)
                # check that the shape of x_train and y_train is the same
                if x_train[source].shape[0] != y_train[source][pollutant].shape[0]:
                    raise ValueError(
                        """
                        For {s} {p}, the number of rows in x_train and y_train do not match.
                        x_train has {x} rows, y_train has {y} rows.
                        """.format(
                            s=source,
                            p=pollutant,
                            x=x_train[source].shape[0],
                            y=y_train[source][pollutant].shape[0],
                        )
                    )
                # check that the shape of the satellite data is correct
                if source == "satellite" and len(x_train[source].shape) != 3:
                    error_message = "The shape of the satellite data must be (NxSxD)."
                    error_message += "The shape you provided was {shp}.".format(
                        shp=x_train[source].shape
                    )
                    raise ValueError(error_message)

    @staticmethod
    def check_test_set_is_valid(x_test: FeaturesDict) -> None:
        """Check the format of x_test dictionary is correct.

        Args:
            x_test: Features.

        Raises:
            ValueError: If x_test has no data for a source (laqn, satellite, ...)
        """
        for source in x_test:
            # no data error
            if x_test[source].shape[0] == 0:
                raise ValueError("x_test has no data for {src}.".format(src=source))

    def elbo_logger(self, logger_arg) -> None:
        """Log optimisation progress.

        Args:
            logger_arg: Argument passed as a callback from GPFlow optimiser.
        """
        if (self.epoch % self.refresh) == 0:
            session = self.model.enquire_session()
            objective = self.model.objective.eval(session=session)
            self.logger.info(
                "Model fitting. Iteration: %s, ELBO: %s, Arg: %s",
                self.epoch,
                objective,
                logger_arg,
            )
        self.epoch += 1

    def batch_predict(
        self,
        x_array: NDArray[Float64],
        predict_fn: Callable[[NDArray[Float64]], NDArrayTuple],
    ) -> NDArrayTuple:
        """Split up prediction into indepedent batches.

        Args:
            x_array: N x D numpy array of locations to predict at.
            predict_fn: Model specific function to predict at.

        Returns:
            y_mean: N x D numpy array of means.
            y_var: N x D numpy array of variances.
        """
        batch_size = self.batch_size

        # Ensure batch is less than the number of test points
        if x_array.shape[0] < batch_size:
            batch_size = x_array.shape[0]

        # Split up test points into equal batches
        num_batches = int(np.ceil(x_array.shape[0] / batch_size))

        ys_arr = []
        ys_var_arr = []
        index = 0

        for count in range(num_batches):
            if count == num_batches - 1:
                # in last batch just use remaining of test points
                batch = x_array[index:, :]
            else:
                batch = x_array[index : index + batch_size, :]

            index = index + batch_size

            # predict for current batch
            y_mean, y_var = predict_fn(batch)

            ys_arr.append(y_mean)
            ys_var_arr.append(y_var)

        y_mean = np.concatenate(ys_arr, axis=0)
        y_var = np.concatenate(ys_var_arr, axis=0)

        return y_mean, y_var

    def predict_srcs(
        self,
        x_test: FeaturesDict,
        predict_fn: Callable[[NDArray[Float64]], NDArrayTuple],
    ) -> TargetDict:
        """Predict using the model at the laqn sites for NO2.

        Args:
            x_test: Features dataset to predict upon. See `Model.predict` for further details.
            predict_fn: Model specific function for predicting.

        Returns:
            See `Model.predict` for further details. The shape for each pollutant will be (N, 1).
        """
        self.check_test_set_is_valid(x_test)
        y_dict = dict()

        for src, x_src in x_test.items():
            for pollutant in self.tasks:
                self.logger.info(
                    "Batch predicting for %s on %s", pollutant, src,
                )
                y_mean, y_var = self.batch_predict(x_src, predict_fn)
                y_dict[src] = {pollutant: dict(mean=y_mean, var=y_var)}
        return y_dict

    @staticmethod
    def clean_data(
        x_array: NDArray[Float64], y_array: NDArray[Float64]
    ) -> NDArrayTuple:
        """Remove nans and missing data for use in GPflow

        Args:
            x_array: N x D numpy array,
            y_array: N x 1 numpy array

        Returns:
            x_array: Feature array cleaned of NaNs.
            y_array: Target array cleaned of NaNs
        """
        idx = ~np.isnan(y_array[:, 0])
        x_array = x_array[idx, :]
        y_array = y_array[idx, :]

        return x_array, y_array
