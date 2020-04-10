"""
Classes for traffic instances.
"""
import logging
from cleanair.instance import Instance
from .tables import TrafficInstanceTable

class TrafficInstance(Instance):
    """
    An instance of a traffic model.
    """

    def update_remote_tables(self):
        """
        Update the instance and model results tables.
        """
        # add a row to the instance table
        records = [self.to_dict()]
        logging.info("Inserting 1 record into the instance table.")
        with self.dbcnxn.open_session() as session:
            self.commit_records(session, records, on_conflict="ignore", table=TrafficInstanceTable)
