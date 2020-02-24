"""
The interface for London air quality models.
"""

from abc import ABC, abstractmethod
import numpy as np
from ..metrics.evaluate import pop_kwarg


class Model(ABC):
    """
    A base class for models.
    All other air quality models should extend this class.
    """

    def __init__(self, model_params=None, experiment_config=None, tasks=None, **kwargs):
        """
        Initialise a model with parameters and settings.

        Parameters
        ___

        model_params : dict, optional
            Parameters to run the model.
            You may wish to pass parameters for the optimizer, kernel, etc.

        experiment_config: dict, optional
            Filepaths, modelname and other settings for execution.

        tasks : list, optional
            The name of the tasks (pollutants) we are modelling.
            Default is ['NO2'].

        Other Parameters
        ___

        log : bool, optional
            Print logs. Default is True.

        batch_size : int, optional
            Default is 100.

        refresh : bool, optional
            How often to print out the ELBO.
        """
        # get the parameters for training the model
        self.model_params = dict() if model_params is None else model_params

        # get filepaths and other configs
        default_config = dict(name="model", restore=False, model_state_fp="./", save_model_state=False)
        self.experiment_config = default_config if experiment_config is None else experiment_config

        # get the tasks we will be predicting at
        self.tasks = ["NO2"] if tasks is None else tasks
        if self.tasks != ["NO2"]:
            raise NotImplementedError(
                "Multiple pollutants not supported. Use only NO2."
            )
        # other misc arguments
        self.log = pop_kwarg(kwargs, "log", True)
        self.model = None
        self.minimum_param_keys = []
        self.epoch = 0
        self.logger = None
        self.batch_size = pop_kwarg(kwargs, "batchsize", 100)
        self.refresh = pop_kwarg(kwargs, "refresh", 10)

    @abstractmethod
    def get_default_model_params(self):
        """
        The default model parameters if none are supplied.

        Returns
        ___

        dict
            Dictionary of parameters.
        """

    def check_model_params_are_valid(self):
        """
        Check the model parameters are valid for the model.

        Parameters
        ___

        model_params : dict
            A dictionary of model parameters.

        Raises
        ___
        KeyError
            If the model parameters are not sufficient.
        """
        min_keys = set(self.minimum_param_keys)
        actual_keys = set(self.model_params.keys())
        diff = min_keys - actual_keys
        # if the set of minimial keys is NOT a subset of the parameters
        if len(diff) > 0:
            error_message = "Model parameters are not sufficient."
            error_message += " You must also supply {d}.".format(d=diff)
            raise KeyError(error_message)

    @abstractmethod
    def fit(self, x_train, y_train):
        """
        Fit the model to some training data.

        Parameters
        ___

        x_train : dict
            Keys are sources. Values are numpy arrays.

        y_train : dict
            Keys are sources. Values are a dict of pollutants and numpys.

        Examples
        ___

        >>> x_train = {
            'laqn' : x_laqn,
            'satellite' : x_satellite
        }
        >>> y_train = {
            'laqn' : {
                'NO2' : y_laqn_no2,
                'PM10' : y_laqn_pm10
            },
            'satellite' : {
                'NO2' : y_satellite_no2,
                'PM10' : y_satellite_pm10
            }
        }
        >>> model.fit(x_train, y_train)

        Notes
        ___

        Every value (e.g. `x_laqn`, `y_satellite_no2`, etc) is a numpy array.
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
    def predict(self, x_test):
        """
        Predict using the model.

        Parameters
        ___

        x_test : dict
            Keys are sources. Values are numpy arrays.

        Returns
        ___

        y_pred : dict
            Keys are sources.
            Values are dicts of pollutants for keys and dict for values.

        Examples
        ___

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
        Model.check_test_set_is_valid(x_test)

    @staticmethod
    def check_training_set_is_valid(x_train, y_train):
        """
        Check the format of x_train and y_train dictionaries are correct.

        Parameters
        ___

        x_train : dict
            Dictionary containing X training data.

        y_train : dict
            Dictionary containing Y training data.

        Raises
        ___

        KeyError
            If there are no keys in x_train or y_train.

        ValueError
            If the shape of x_train or y_train are incorrect.
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
    def check_test_set_is_valid(x_test):
        """
        Check the format of x_test dictionary is correct.
        """
        for source in x_test:
            # no data error
            if x_test[source].shape[0] == 0:
                raise ValueError('x_test has no data for {src}.'.format(src=source))

    def elbo_logger(self, logger_arg):
        """
        Log optimisation progress.

        Parameters
        ___

        logger_arg : unknown
            Argument passed as a callback from GPFlow optimiser.
        """
        if (self.epoch % self.refresh) == 0:
            session = self.model.enquire_session()
            objective = self.model.objective.eval(session=session)
            if self.log:
                self.logger.info(
                    "Model fitting. Iteration: %s, ELBO: %s, Arg: %s",
                    self.epoch,
                    objective,
                    logger_arg,
                )
        self.epoch += 1

    def batch_predict(self, x_array, predict_fn):
        """
        Split up prediction into indepedent batches.

        Parameters
        ___

        x_array : np.array
            N x D numpy array of locations to predict at.

        predict_fn : function
            model spefic function to predict at.

        Returns
        ___

        y_mean : np.array
            N x D numpy array of means.

        y_var : np.array
            N x D numpy array of variances.
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

    def predict_srcs(self, x_test, predict_fn):
        """
        Predict using the model at the laqn sites for NO2.

        Parameters
        ___

        x_test : dict
            See `Model.predict` for further details.

        Returns
        ___

        dict
            See `Model.predict` for further details.
            The shape for each pollutant will be (n, 1).
        """
        self.check_test_set_is_valid(x_test)
        y_dict = dict()

        for src, x_src in x_test.items():
            for pollutant in self.tasks:
                if self.log:
                    self.logger.info(
                        "Batch predicting for %s on %s", pollutant, src,
                    )
                y_mean, y_var = self.batch_predict(x_src, predict_fn)
                y_dict[src] = {pollutant: dict(mean=y_mean, var=y_var)}
        return y_dict

    @staticmethod
    def clean_data(x_array, y_array):
        """Remove nans and missing data for use in GPflow

        args:
            x_array: N x D numpy array,
            y_array: N x 1 numpy array
        """
        idx = ~np.isnan(y_array[:, 0])
        x_array = x_array[idx, :]
        y_array = y_array[idx, :]

        return x_array, y_array
