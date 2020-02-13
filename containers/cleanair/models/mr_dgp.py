"""
Multi-resolution DGP (LAQN + Satellite)
"""
import logging
import os
import numpy as np
import gpflow
from scipy.cluster.vq import kmeans2
import tensorflow as tf

from ..loggers import get_logger
from .model import Model


class MR_DGP(Model):
    """
    MR-DGP for air quality.
    """
    def __inti__(model_params=None, log=True, batch_size=100, disable_tf_warnings=True, **kwargs):
        super().__init__(**kwargs)

    def get_default_model_params(self):
        """
        The default model parameters of MR-DGP if none are supplied.

        Returns
        ___

        dict
            Dictionary of parameters.
        """
        return {
            'restore': False,
            'train': True
        }

        
    def setup_model(self, x_array, y_array, inducing_locations, num_input_dimensions):
        #TODO: number of inducing locations should be a model parameter?
        print(x_array)
        pass

    def fit(self, x_train, y_train, refresh=10, save_model_state=True):
        pass

    def predict(self, x_test, species=['NO2']):
        return None


