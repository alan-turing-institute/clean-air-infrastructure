"""Shared arguments"""
from .instance_options import (
    ClusterIdOption,
    TagOption,
)
from .shared_args import (
    UpTo,
    UpTo_callback,
    NHours,
    NDays,
    NDays_callback,
    CopernicusKey,
    Web,
    InputDir,
    InsertMethod,
    AWSId,
    AWSKey,
    ValidInsertMethods,
    ValidFeatureSources,
    ValidDynamicFeatureSources,
    Sources,
    ValidSources,
    Species,
)

__all__ = [
    "UpTo",
    "UpTo_callback",
    "NHours",
    "NDays",
    "NDays_callback",
    "CopernicusKey",
    "Web",
    "InputDir",
    "InsertMethod",
    "ValidInsertMethods",
    "ValidFeatureSources",
    "ValidDynamicFeatureSources",
    "Sources",
    "ValidSources",
    "Species",
    "ClusterIdOption",
    "TagOption",
]
