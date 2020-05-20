"""
Experiments summerise multiple instances.
"""

import pandas as pd
from cleanair.databases import DBWriter

class Experiment(DBWriter):
    """
    An experiment contains multiple instances.
    """

    def __init__(self, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)
        self._dataframe = pd.DataFrame(
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

    @property
    def dataframe(self):
        """Information about the instances"""
        return self._dataframe
    
    def add_instance(self, instance: TrafficInstance):
        """ToDo."""

    def update_remote_tables(self):
        """Update the instance, data and model tables."""
