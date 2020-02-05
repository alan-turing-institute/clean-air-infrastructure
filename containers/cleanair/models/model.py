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
        if set(self.minimum_param_keys) != set(self.model_params.keys()):
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
            'laqn' : np.array,
            'satellite' : np.array
        }
        >>> y_train = {
            'laqn' : {
                'NO2' : np.array,
                'PM10' : np.array
            },
            'satellite' : {
                'NO2' : np.array,
                'PM10' : np.array
            }
        }
        >>> model.fit(x_train, y_train)
        """
        Model.__check_training_set_is_valid(x_train, y_train)

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
        Model.__check_test_set_is_valid(x_test)
        
    @staticmethod
    def __check_training_set_is_valid(x_train, y_train):
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
        """
        if 'laqn' not in x_train:
            raise KeyError("'laqn' must be a key in x_train")
        if 'laqn' not in y_train:
            raise KeyError("'laqn' must be a key in y_train")
        # check the shape of numpy arrays
        for source in y_train:
            for pollutant in y_train[source]:
                if y_train[source][pollutant].shape[1] != 1:
                    raise ValueError(
                        """
                        The shape of {p} numpy array for source {s} must be Nx1. The shape you gave was Nx{k}
                        """.format(p=pollutant, s=source, k=y_train[source][pollutant].shape[1])
                    )
                # ToDo: check x_train[source] against y_train

    @staticmethod
    def __check_test_set_is_valid(x_test):
        """
        Check the format of x_test dictionary is correct.
        """
        # ToDo: implemention
        
        raise NotImplementedError()
