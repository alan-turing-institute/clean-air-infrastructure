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
    def __get_default_model_params(self):
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
    def fit(self, X, Y, **kwargs):
        """
        Fit the model to some training data.

        Parameters
        ___

        X : dict
            Keys are sources. Values are numpy arrays.

        Y : dict
            Keys are sources. Values are a dict of pollutants and numpys.

        Examples
        ___

        >>> X = {
            'laqn' : np.array,
            'satellite' : np.array
        }
        >>> Y = {
            'laqn' : {
                'NO2' : np.array,
                'PM10' : np.array
            },
            'satellite' : {
                'NO2' : np.array,
                'PM10' : np.array
            }
        }
        >>> model.fit(X, Y)
        """

    @abstractmethod
    def predict(self, X, **kwargs):
        """
        Predict using the model.

        Parameters
        ___

        X : dict
            Keys are sources. Values are numpy arrays.

        Returns
        ___

        Y : dict
            Keys are sources.
            Values are dicts of pollutants for keys and dict for values.

        Examples
        ___

        >>> Y = model.predict(X)
        >>> json.dumps(Y)
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
