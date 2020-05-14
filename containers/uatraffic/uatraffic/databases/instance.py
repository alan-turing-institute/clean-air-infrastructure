"""
Classes for traffic instances.
"""
import os
import logging
import pickle
from pathlib import Path
import gpflow
from cleanair.instance import Instance
from .tables import TrafficInstanceTable, TrafficModelTable

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
        if model_param:
            logging.info("Updating the model table.")
            records = [dict(
                model_name=self.model_name,
                param_id=self.param_id,
                model_param=model_param,
            )]
            with self.dbcnxn.open_session() as session:
                self.commit_records(session, records, on_conflict="ignore", table=TrafficModelTable)

    def save_model(self, model, folder, extension="h5"):
        """
        Save the model to the given folder.
        """
        # Create model copy
        model_copy = gpflow.utilities.deepcopy(model)

        # Save model to file
        Path(folder).mkdir(exist_ok=True, parents=True)
        filepath = os.path.join(folder, self.instance_id + "." + extension)
        pickle.dump(model_copy, open(filepath, "wb"))
