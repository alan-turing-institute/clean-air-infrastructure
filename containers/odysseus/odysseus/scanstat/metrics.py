"""Contains all functionality required to calculate likelihood metrics of
a space-time region. The ratio is computed for all searched space-time regions."""

import numpy as np


def ebp(baseline_count: float, actual_count: float) -> float:
    """Simple Expression for the Expectation-Based Poisson (EBP)
    likelihood ratio.

    Args:
        baseline_count: Sum of baseline counts in space-time region S
        actual_count: Sum of actual counts in space-time region S
    Returns:
        likelihood ratio score
    """

    if actual_count < 0 or baseline_count < 0:
        raise ValueError("Negative count value passed in scan")

    # F(S) defaults to 1
    if baseline_count == 0:
        return 1.0
    if actual_count > baseline_count:
        return np.power((actual_count / baseline_count), actual_count) * np.exp(
            baseline_count - actual_count
        )
    return 1.0


def ebp_asym(baseline_count: float, actual_count: float) -> float:

    """Extension to the original EBP likelihood ratio which also assigns
    meaningful scores to space-time regions whose actual activity is
    QUIETER than what is expected. If this is the case, this represented
    with a negative score. Note that this metric is centred about 0, whereas
    the original EBP (`ebp`) has a minimum value of 1.
    Args:
        baseline_count: Sum of baseline counts in space-time region S
        actual_count: Sum of actual counts in space-time region S
    Returns:
        Asymmetric likelihood ratio score
    """

    if actual_count < 0 or baseline_count < 0:
        raise ValueError("Negative count value passed in scan")

    if baseline_count == 0:
        return 0.0
    if actual_count >= baseline_count:
        return (
            np.power((actual_count / baseline_count), actual_count)
            * np.exp(baseline_count - actual_count)
            - 1
        )
    return 1 - np.power((actual_count / baseline_count), actual_count) * np.exp(
        baseline_count - actual_count
    )


def kulldorf(
    baseline_count_in: float,
    baseline_count_total: float,
    actual_count_in: float,
    actual_count_total: float,
) -> float:

    """Implementation of the original Kulldorf Spatial Scan metric.
    This differs to the `ebp` metric as it takes into account a region's score
    inside AND outside the region of interest. i.e. this metric aims to find
    space-time regions which have the largest score inside it and the smallest
    score outside of it. Depending on the application, this metric is sometimes
    better at finding smaller high-scoring regions.
    Args:
        baseline_count_in: Sum of baseline predictions INSIDE the search region
        baseline_count_total: Sum of baseline predictions over the whole space-time domain
                              For a given scan, this is clearly constant
        actual_count_in: Sum of actual counts INSIDE the search region
        actual_count_total: Sum of actual countsover the whole space-time domain
                              For a given scan, this is clearly constant
    Returns:
        Kulldorf Metric for space-time region.
    """

    if (
        actual_count_in < 0
        or baseline_count_in < 0
        or baseline_count_total < 0
        or actual_count_total < 0
    ):
        raise ValueError("Negative count value passed in scan")

    actual_count_out = actual_count_total - actual_count_in
    baseline_count_out = baseline_count_total - baseline_count_in

    if baseline_count_in == 0 or baseline_count_out == 0:
        return 1.0
    if (actual_count_in / baseline_count_in) > (actual_count_out / baseline_count_out):
        return (
            np.power(actual_count_in / baseline_count_in, actual_count_in)
            * np.power(actual_count_out / baseline_count_out, actual_count_out)
            * np.power(actual_count_total / baseline_count_total, -actual_count_total)
        )
    return 1.0
