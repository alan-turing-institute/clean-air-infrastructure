"""Shared arguments"""

from .model_options import MaxIter
from .instance_options import (
    ClusterIdOption,
    TagOption,
)
from .shared_args import (
    AWSId,
    AWSKey,
    CopernicusKey,
    From,
    InputDir,
    InsertMethod,
    NDays_callback,
    NDays,
    NHours,
    ScootDetectors,
    Sources,
    Species,
    UpTo_callback,
    UpTo,
    ValidFeatureSources,
    ValidInsertMethods,
    ValidSources,
    Web,
)

__all__ = [
    "AWSId",
    "AWSKey",
    "CopernicusKey",
    "From",
    "InputDir",
    "InsertMethod",
    "NDays_callback",
    "NDays",
    "NHours",
    "MaxIter",
    "ScootDetectors",
    "Sources",
    "Species",
    "ClusterIdOption",
    "UpTo_callback",
    "UpTo",
    "TagOption",
    "ValidFeatureSources",
    "ValidInsertMethods",
    "ValidSources",
    "Web",
]
