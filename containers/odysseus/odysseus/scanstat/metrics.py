"""Contains all functionality required to calculate the likelihood ratio F(S)
of a space-time region S as per Expectation-Based Scan Statistic paper. The
ratio is computed for all space-time regions; if significantly larger than
expected, randomisation testing is used to infer the statistical signifiance
of the event"""

import numpy as np


def ebp(baseline_count: float, actual_count: float) -> float:
    """Simple Expression for the likelihood ratio
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

    """Extension to the original EBP likelihood ratio
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
