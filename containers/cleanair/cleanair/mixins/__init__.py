"""
Mixins for adding functionality
"""
from .db_connection_mixin import DBConnectionMixin
from .api_request_mixin import APIRequestMixin
<<<<<<< HEAD
from .database_query_mixin import DBQueryMixin, ScootQueryMixin
from .date_range_mixin import DateRangeMixin

# from .instance_tables_mixin import (
#     DataTableMixin,
#     InstanceTableMixin,
#     MetricsTableMixin,
#     ModelTableMixin,
#     ResultTableMixin,
# )
from .instance_query_mixin import InstanceQueryMixin
=======
from .date_range_mixin import DateRangeMixin, DateGeneratorMixin
from .instance_mixins import ResultMixin
from .query_mixins import (
    DBQueryMixin,
    InstanceQueryMixin,
    ResultQueryMixin,
    ScootQueryMixin,
)
>>>>>>> 5f4663cef950153802e4469b312b64d3e8697843
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
    "ResultMixin",
    "ResultQueryMixin",
    "ScootQueryMixin",
    "SecretFileParserMixin",
    "SourcesMixin",
    "VerbosityMixin",
    "WebMixin",
]
