"""
Multi-resolution GPRN (LAQN + Satellite)
"""

import logging
import os
import numpy as np
import tensorflow as tf

import gpflow
from gpflow import settings
from gpflow.training import AdamOptimizer

from scipy.cluster.vq import kmeans2

from ..loggers import get_logger
from .model import Model

class MR_GPRN_MODEL(Model):
    """
    MR-DGP for air quality.
    """

    def __init__(
        self,
        model_params=None,
        log=True,
        batch_size=100,
        disable_tf_warnings=True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.batch_size = batch_size
        self.epoch = 0
        self.refresh = 10

        #TODO: can we move into parent class?
        # Ensure logging is available
        if log and not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # disable TF warnings
        if disable_tf_warnings:
            logging.disable(logging.WARNING)
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
            tf.logging.set_verbosity(tf.logging.ERROR)

        # check model parameters
        if model_params is None:
            self.model_params = self.get_default_model_params()
        else:
            self.model_params = model_params
            super().check_model_params_are_valid()
 
