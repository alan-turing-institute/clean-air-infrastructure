"""Module for interacting with the Azure Postgres database"""
from sqlalchemy import DDL, event
from sqlalchemy.ext.declarative import declarative_base
from .connector import Connector
from .static_tables import StaticTableConnector
from .updater import Updater

BASE = declarative_base()
SCHEMA_NAMES = ['datasources', 'buffers', 'modelfits']
EVENTS = [event.listen(BASE.metadata, 'before_create', DDL("CREATE SCHEMA IF NOT EXISTS {}".format(schema))) for schema in SCHEMA_NAMES]


__all__ = [
    "Connector",
    "StaticTableConnector",
    "Updater",
]
