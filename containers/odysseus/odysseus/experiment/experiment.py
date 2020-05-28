"""
Experiments summerise multiple instances.
"""

import pandas as pd
from cleanair.databases import DBWriter
from .instance import TrafficInstance
from ..databases.tables import TrafficInstanceTable

class Experiment(DBWriter):
    """
    An experiment contains multiple instances.
    """

    def __init__(self, frame: pd.DataFrame = None, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)
        if frame:
            self._frame = pd.DataFrame(
                columns=[
                    "instance_id",
                    "model_name",
                    "param_id",
                    "data_id",
                    "cluster_id",
                    "tag",
                    "git_hash",
                    "fit_start_time",
                    "data_config",
                    "model_param",
                    "preprocessing",
                ]
            )
        else:
            self._frame = frame

    @property
    def frame(self):
        """Information about the instances"""
        return self._frame
    
    def add_instance(self, instance: TrafficInstance):
        """ToDo."""

    def update_remote_tables(self):
        """Update the instance, data and model tables."""
        site_records = self.frame.to_dict("records")
        self.commit_records(
            site_records, on_conflict="overwrite", table=TrafficInstanceTable,
        )
