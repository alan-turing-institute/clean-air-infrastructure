"""
Classes for traffic instances.
"""
import logging
from cleanair.instance import Instance
from .tables import TrafficInstanceTable, TrafficModelTable, TrafficDataTable

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

    def update_model_table(self, model_param):
        """
        Update the traffic model table.
        """
        logging.info("Updating the model table.")
        records = [dict(
            model_name=self.model_name,
            param_id=self.param_id,
            model_param=model_param,
        )]
        with self.dbcnxn.open_session() as session:
            self.commit_records(session, records, on_conflict="ignore", table=TrafficModelTable)

    def update_data_table(self, data_config):
        """
        Update the data config table for traffic.
        """
        logging.info("Updating the traffic data table.")
        records = [dict(
            data_id=self.data_id,
            data_config=data_config
        )]
        with self.dbcnxn.open_session() as session:
            self.commit_records(session, records, on_conflict="ignore", table=TrafficDataTable)
