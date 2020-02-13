"""
The interface for London air quality models.
"""

from abc import ABC, abstractmethod
import numpy as np

class Model(ABC):
    """
    A base class for models.
    All other air quality models should extend this class.
    """

    def __init__(self, **kwargs):
        self.model = None
        self.minimum_param_keys = ['restore']
        if 'model_params' in kwargs:
            self.model_params = kwargs['model_params']
        else:
            self.model_params = dict(restore=False)

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
    def fit(self, x_train, y_train, **kwargs):
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
    def predict(self, x_test, **kwargs):
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
                    error_message = 'The shape of {p} numpy array for source {s} must be Nx1. '
                    error_message += 'The shape you gave was Nx{k}'
                    error_message.format(
                        p=pollutant,
                        s=source,
                        k=y_train[source][pollutant].shape[1]
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
                            y=y_train[source][pollutant].shape[0]
                        )
                    )
                # check that the shape of the satellite data is correct
                if source == 'satellite' and len(x_train[source].shape) != 3:
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

    def elbo_logger(self, x):
        """Log optimisation progress

        args:
            x: argument passed as a callback from GPFlow optimiser.
        """
        if (self.epoch % self.refresh) == 0:
            session = self.model.enquire_session()
            objective = self.model.objective.eval(session=session)
            if self.logger:
                self.logger.info(
                    "Model fitting. Iteration: %s, ELBO: %s", self.epoch, objective
                )

            print(self.epoch, ": ", objective)

        self.epoch += 1

    def batch_predict(self, x_test, predict_fn):
        """Split up prediction into indepedent batchs.
        args:
            x_test: N x D numpy array of locations to predict at
        """
        batch_size = self.batch_size

        # Ensure batch is less than the number of test points
        if x_test.shape[0] < batch_size:
            batch_size = x_test.shape[0]

        # Split up test points into equal batches
        num_batches = int(np.ceil(x_test.shape[0] / batch_size))

        ys_arr = []
        ys_var_arr = []
        i = 0

        for b in range(num_batches):
            if b % self.refresh == 0:
                print("Batch", b, "out of", num_batches)
            if b == num_batches - 1:
                # in last batch just use remaining of test points
                batch = x_test[i:, :]
            else:
                batch = x_test[i : i + batch_size, :]

            i = i + batch_size

            # predict for current batch
            ys, ys_var = predict_fn(batch)

            ys_arr.append(ys)
            ys_var_arr.append(ys_var)

        ys = np.concatenate(ys_arr, axis=0)
        ys_var = np.concatenate(ys_var_arr, axis=0)

        return ys, ys_var

    def predict_srcs(self, x_test, predict_fn, species=['NO2']):
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
        if species != ['NO2']:
            raise NotImplementedError("Multiple pollutants not supported. Use only NO2.")
        self.check_test_set_is_valid(x_test)
        y_dict = dict()

        for src, x_src in x_test.items():
            for pollutant in species:
                y_mean, y_var = self.batch_predict(x_src, predict_fn)
                y_dict[src] = {
                    pollutant: dict(
                        mean=y_mean,
                        var=y_var
                    )
                }
        return y_dict

    def clean_data(self, x_array, y_array):
        """Remove nans and missing data for use in GPflow

        args:
            x_array: N x D numpy array,
            y_array: N x 1 numpy array
        """
        idx = ~np.isnan(y_array[:, 0])
        x_array = x_array[idx, :]
        y_array = y_array[idx, :]

        return x_array, y_array
