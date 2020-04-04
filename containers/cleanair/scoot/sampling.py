import numpy as np
import matplotlib.pyplot as plt

def sample_n(model, test_inputs, num_samples=10):
    """
    Given the trained model this function samples from the posterior intensity and then samples from the Poisson
    to get estimated mean and variance for the counts.
    """
    samplesN = np.random.poisson(np.exp(model.predict_f_samples(test_inputs,num_samples)))
    samples_mean = np.mean(samplesN,axis=0)
    samples_var = np.var(samplesN,axis=0)
    
    return samples_mean, samples_var

 
def sample_intensity(model, test_inputs, num_samples: int = 10):
    """
    Samples from posterior intensity distribution
    """
    intensitiesN = np.exp(model.predict_f_samples(test_inputs, num_samples))
    intensities_mean = np.mean(intensitiesN,axis=0)
    intensities_var = np.var(intensitiesN,axis=0)
    return intensities_mean, intensities_var

def percentage_coverage(model, test_inputs, Ytest, quantile: int = 0.9, num_samples: int = 10, num_pertubations: int = 100, debug=False):
    """
    Computes percentage cover.

    model : model

    test_inputs : 
        Set of inputs to compute intensity on

    y_tes : 
        Correspending output of test_inputs

    quantile: float, default=0.9
        Credible interval 

    num_samples : 
        number of samples from intensity

    num_pertubations : int, optional
        number of samples from Poisson (counts) with given sample of intensity

    Notes
    ___

    See Virginia's pdf for details.
    
    """

    # TODO: shall we save the samples from the model to a file so we can easily see them again?
    
    # Number of times total counts were within 90th percentile
    coverage_events = 0
    
    # Loop over samples
    for i in range(num_samples):

        # Change seed
        np.random.seed(i)
        
        # Sample from latent function (intensity)
        intensity_sample = np.exp(model.predict_f_samples(test_inputs, 1))

        # Compute emprical distribution of counts
        empirical_count_distribution = np.random.poisson(intensity_sample[0, :, :], (num_pertubations, intensity_sample.shape[1], intensity_sample.shape[2]))
        
        # Total number of actual counts
        total_counts = np.sum(Ytest)
        total_emp_counts = np.sum(empirical_count_distribution, axis=1)
       
        # Compute upper and lower quantiles from the empirical distribution of counts
        remainder = 1 - quantile
        lower_q = np.quantile(total_emp_counts, remainder / 2)
        upper_q = np.quantile(total_emp_counts, 1 - remainder / 2)
    
        # Add 1 - if total counts are within quantile, 0 - otherwise
        coverage_events += int((total_counts < upper_q) & (total_counts > lower_q))
        # binary = int((total_counts < upper_q) & (total_counts > lower_q)) # this is kept for debugging (remove afterwards)

        if debug:
            print("Remainder:", remainder)
            print("lower:", lower_q)
            print("upper:", upper_q)
            print("total count:", total_counts)
            print("adding:", int((total_counts < upper_q) & (total_counts > lower_q)))
            print()
            plt.hist(total_emp_counts)
            plt.axvline(total_counts)
            plt.axvline(upper_q, color="green")
            plt.axvline(lower_q, color="red")
            plt.show()

    return coverage_events/num_samples
