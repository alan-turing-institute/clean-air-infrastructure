"""
Functions for sampling from gpflow models.
"""

import numpy as np


def sample_n(model, test_inputs, num_samples=10):
    """
    Given the trained model this function samples from the posterior intensity and then samples from the Poisson
    to get estimated mean and variance for the counts.
    """
    samplesN = np.random.poisson(
        np.exp(model.predict_f_samples(test_inputs, num_samples))
    )
    samples_mean = np.mean(samplesN, axis=0)
    samples_var = np.var(samplesN, axis=0)

    return samples_mean, samples_var


def sample_intensity(model, test_inputs, num_samples: int = 10):
    """
    Samples from posterior intensity distribution
    """
    intensitiesN = np.exp(model.predict_f_samples(test_inputs, num_samples))
    intensities_mean = np.mean(intensitiesN, axis=0)
    intensities_var = np.var(intensitiesN, axis=0)
    return intensities_mean, intensities_var
