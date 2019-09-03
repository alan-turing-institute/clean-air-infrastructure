"""Module for interacting with the Azure Postgres database"""
from .connector import Connector
from .updater import Updater
from .static_tables import StaticTableConnector

__all__ = [
    "Connector",
    "Updater",
    "StaticTableConnector"
]
