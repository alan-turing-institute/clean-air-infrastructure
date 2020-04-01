"""Declarative base class and table initialisation"""
from sqlalchemy import DDL, event
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()  # pylint: disable=invalid-name
SCHEMA_NAMES = [
    "dynamic_data",
    "dynamic_features",
    "interest_points",
    "model_features",
    "model_results",
    "processed_data",
    "static_data",
    "static_features",
]
