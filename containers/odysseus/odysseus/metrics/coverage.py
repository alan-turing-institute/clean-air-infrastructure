import numpy as np
import matplotlib.pyplot as plt


def percent_coverage(
    model,
    x_test,
    y_test,
    quantile: float = 0.9,
    num_samples: int = 1000,
    num_pertubations: int = 1000,
    debug=False,
):
    """
    Computes percentage coverage.

    model : model
        A gpflow model to sample from.

    x_test : np.array
        Set of inputs to compute intensity upon.

    y_test : np.array
        Correspending true values of x_test.

    quantile: float, optional
        Credible interval range. Must between 0 and 1 exclusive.

    num_samples : int, optional
        number of samples from intensity

    num_pertubations : int, optional
        number of samples from Poisson (counts) with given sample of intensity

    Notes
    ___

    See Virginia's pdf for details.
    """

    # TODO: shall we save the samples from the model to a file so we can easily see them again?

    # check on quantile
    assert quantile > 0 and quantile < 1

    # Number of times total counts were within 90th percentile
    coverage_events = 0

    # Loop over samples
    for i in range(num_samples):

        # Change seed
        np.random.seed(i)

        # Sample from latent function (intensity)
        intensity_sample = np.exp(model.predict_f_samples(x_test, 1))

        # Compute emprical distribution of counts
        empirical_count_distribution = np.random.poisson(
            intensity_sample[0, :, :],
            (num_pertubations, intensity_sample.shape[1], intensity_sample.shape[2]),
        )

        # Total number of actual counts
        total_counts = np.sum(y_test)
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

    return coverage_events / num_samples
