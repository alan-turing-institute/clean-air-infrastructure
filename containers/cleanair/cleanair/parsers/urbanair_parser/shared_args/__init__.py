"""Shared arguments"""

from .instance_options import ClusterId, Tag
from .model_options import MaxIter
from .shared_args import (
    UpTo,
    UpTo_callback,
    NHours,
    NDays,
    NDays_callback,
    CopernicusKey,
    Web,
    InsertMethod,
    AWSId,
    AWSKey,
    ValidInsertMethods,
    ValidFeatureSources,
    Sources,
    ValidSources,
    Species,
)

__all__ = [
    "ClusterId",
    "Tag",
    "UpTo",
    "UpTo_callback",
    "NHours",
    "NDays",
    "NDays_callback",
    "CopernicusKey",
    "Web",
    "InsertMethod",
    "ValidInsertMethods",
    "ValidFeatureSources",
    "Sources",
    "ValidSources",
    "Species",
    "MaxIter",
]
