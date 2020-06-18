"""
Mixins for adding functionality
"""
from .db_connection_mixin import DBConnectionMixin
from .api_request_mixin import APIRequestMixin
from .database_query_mixin import DBQueryMixin, ScootQueryMixin
from .date_range_mixin import DateRangeMixin, DateGeneratorMixin
from .instance_query_mixin import InstanceQueryMixin
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
    "InstanceQueryMixin",
    "ScootQueryMixin",
    "SecretFileParserMixin",
    "SourcesMixin",
    "VerbosityMixin",
    "WebMixin",
]
