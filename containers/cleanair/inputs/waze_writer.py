"""
Waze
"""
import datetime
import os
import time
from dateutil import rrule
from sqlalchemy import Table
from sqlalchemy.exc import IntegrityError
import pandas
from ..databases import DBWriter
from ..databases.tables import ScootReading
from ..loggers import get_logger, green
from ..mixins import DateRangeMixin
from ..timestamps import datetime_from_unix, unix_from_str, utcstr_from_datetime

# import logging
# import os
# import json
# import urllib.request
# import sys
# import shutil
# import time
# import datetime

class WazeWriter(DBWriter):
    """
    Class to get data from waze via the waze API
    """

    def __init__(self, endpoint, **kwargs):

        # Inititalise parent class
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)
            
        self.endpoint = endpoint 

    def request_data(self):
        """
        Request waze data
        """

        try:
            raw_data = self.get_response(self.endpiint, timeout=5.0).json()
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed: %s", endpoint, error)
            return None
        except (TypeError, KeyError):
            return None

    def update_remote_tables(self):
        """
        Update the waze data table with the new data
        """
        self.logger.info("Starting %s readings update...", green("waze"))

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Load readings for all sites and update the database accordingly
      
            self.logger.info("Requesting waze data")

            # Get all readings for each site between its start and end dates and update the database
            waze_data = self.request_data()
            waze_data_processed = self.process_data()

            # site_records = [].build_entry(site_reading) for site_reading in site_readings]

            # Commit the records to the database
            self.add_records(session, site_records)
            session.commit()

            # Commit changes
            self.logger.info("Committing %s records to database table %s",
                             green(len(site_readings)),
                             green(LAQNReading.__tablename__))
            session.commit()

        self.logger.info("Finished %s readings update", green("LAQN"))