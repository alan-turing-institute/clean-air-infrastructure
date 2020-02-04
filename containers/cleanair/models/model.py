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
        raise NotImplementedError

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
