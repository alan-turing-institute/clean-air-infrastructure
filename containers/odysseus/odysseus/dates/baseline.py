"""Types of baselines."""

from enum import Enum


class Baseline(str, Enum):
    """A baseline period."""

    prelockdown = "prelockdown"  # before lockdown started
    lockdown = "lockdown"  # during lockdown
    postlockdown = "postlockdown"  # after lockdown
    last3weeks = "last3weeks"  # the most recent 3 weeks before the forecast period


class BaselineUpto(Enum):
    """The last datetime (not inclusive) of the baseline period."""

    prelockdown = "2020-03-02"
    lockdown = "2020-04-20"
    postlockdown = "2020-07-20"
