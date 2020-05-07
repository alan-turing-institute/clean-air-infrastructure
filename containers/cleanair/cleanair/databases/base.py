"""Declarative base class and table initialisation"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DDL, event

Base = declarative_base()  # pylint: disable=invalid-name
SCHEMA_NAMES = [