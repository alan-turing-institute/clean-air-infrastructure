"""Declarative base class and table initialisation"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DDL, event

Base = declarative_base()  # pylint: disable=invalid-name
# SCHEMA_NAMES = [
#     "dynamic_data",
#     "dynamic_features",
#     "interest_points",
#     "model_features",
#     "model_results",
#     "processed_data",
#     "static_data",
#     "static_features",
# ]
# EXTENSIONS = ["postgis", "uuid-ossp"]


# SCHEMA_EVENTS = [
#     event.listen(
#         Base.metadata,
#         "before_create",
#         DDL("CREATE SCHEMA IF NOT EXISTS {}".format(schema)),
#     )
#     for schema in SCHEMA_NAMES
# ]

# EXTENTION_EVENTS = [
#     event.listen(
#         Base.metadata,
#         "before_create",
#         DDL("CREATE EXTENTION IF NOT EXISTS {}".format(extension)),
#     )
#     for extension in EXTENSIONS
# ]