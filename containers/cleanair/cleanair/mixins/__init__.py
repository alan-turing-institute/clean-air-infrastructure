"""
Mixins for adding functionality
"""
from .db_connection_mixin import DBConnectionMixin
from .api_request_mixin import APIRequestMixin
from .date_range_mixin import DateRangeMixin, DateGeneratorMixin
from .instance_mixins import InstanceMixin, ResultMixin, UpdateInstanceMixin
from .query_mixins import (
    DBQueryMixin,
    InstanceQueryMixin,
    ResultQueryMixin,
    ScootQueryMixin,
)
from .parser_mixins import (
    CopernicusMixin,
    DurationParserMixin,
    InsertMethodMixin,
    SecretFileParserMixin,
    VerbosityMixin,
    SourcesMixin,
    WebMixin,
)

__all__ = [
    "APIRequestMixin",
    "CopernicusMixin",
    "DateRangeMixin",
    "DateGeneratorMixin",
    "DBConnectionMixin",
    "DBQueryMixin",
    "DurationParserMixin",
    "InstanceMixin",
    "InstanceQueryMixin",
    "ResultMixin",
    "ResultQueryMixin",
    "ScootQueryMixin",
    "SecretFileParserMixin",
    "SourcesMixin",
    "UpdateInstanceMixin",
    "VerbosityMixin",
    "WebMixin",
]
