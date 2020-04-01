import numpy as np


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

# THIS IS BUGGY
## Computes percentage cover (see Virginia's pdf for details)
def percentage_coverage(model,test_inputs,Ytest,quantile:int = 0.95, num_samples:int = 10,num_pertubations: int = 100):
    # Number of times total counts were within 90th percentile
    coverage_events = 0
    
    # Loop over pertubations
    for i in range(num_pertubations):

        # Change seed
        np.random.seed(i)
        
        # Sample from latent function (intensity)
        intensity_sample = np.exp(model.predict_f_samples(test_inputs,num_samples))
        # Compute emprical distribution of counts
        empirical_count_distribution = np.random.poisson(intensity_sample)
        
        # Total number of actual counts
        total_counts = np.sum(Ytest)
       
        # Compute upper and lower quantiles from the empirical distribution of counts
        upper_q = np.quantile(np.sum(samples[:,:,0],axis=1),quantile)
        lower_q = np.quantile(np.sum(samples[:,:,0],axis=1),1-quantile)
    
        # Add 1 - if total counts are within quantile, 0 - otherwise
        coverage_events += int((total_counts < upper_q) & (total_counts > lower_q))
        binary = int((total_counts < upper_q) & (total_counts > lower_q)) # this is kept for debugging (remove afterwards)

    return empirical_count_distribution, binary, total_counts, upper_q, lower_q # this is kept for debugging (remove afterwards)
    return coverage_events/num_pertubations # this should be the output after debugging
