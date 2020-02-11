"""
The interface for London air quality models.
"""

from abc import ABC, abstractmethod

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

    def __check_model_params_are_valid(self):
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
        # if the set of minimial keys is NOT a subset of the parameters
        if not set(self.minimum_param_keys).issubset(set(self.model_params.keys())):
            raise KeyError("""Model parameters are not sufficient. \n
        The minimal set of keys is: {min} \n
        You supplied the following keys: {params}
        """.format(min=self.minimum_param_keys, params=self.model_params.keys()))

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
        | `x_laqn`          | (NxSxD) |
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
            If 'laqn' is not in x_train and y_train.

        ValueError
            If the shape of x_train or y_train are incorrect.
        """
        if 'laqn' not in x_train:
            raise KeyError("'laqn' must be a key in x_train")
        if 'laqn' not in y_train:
            raise KeyError("'laqn' must be a key in y_train")
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

    @staticmethod
    def check_test_set_is_valid(x_test):
        """
        Check the format of x_test dictionary is correct.
        """
        for source in x_test:
            # no data error
            if x_test[source].shape[0] == 0:
                raise ValueError('x_test has no data for {src}.'.format(src=source))
