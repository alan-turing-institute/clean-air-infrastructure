"""
Static data source tables
"""
from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base
from .connector import Connector
from ..loggers import get_logger


class StaticTableConnector(Connector):
    """
    Base class to manage interactions with the tables in postgresql databases by reflection
    """
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.logger = get_logger(__name__, kwargs.get("verbose", 0))

    def get_table_instance(self, table_name):
        """
        Get a table class
        """

        # produce our own MetaData object
        metadata = MetaData()
        metadata.reflect(self.engine, only=[table_name])
        Base = automap_base(metadata=metadata)
        Base.prepare()

        return getattr(Base.classes, table_name)
