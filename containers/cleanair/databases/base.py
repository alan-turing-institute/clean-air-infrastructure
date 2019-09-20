"""Declarative base class and table initialisation"""
from sqlalchemy import DDL, event
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()  # pylint: disable=invalid-name
SCHEMA_NAMES = ['datasources', 'buffers', 'modelfits']
EVENTS = [event.listen(Base.metadata, 'before_create',
                       DDL("CREATE SCHEMA IF NOT EXISTS {}".format(schema))) for schema in SCHEMA_NAMES]
