"""Experiment for training multiple models on multiple scoot detectors."""

from cleanair.databases import DBWriter
from cleanair.databases.tables import TrafficInstanceTable, TrafficModelTable
from cleanair.mixins import ScootQueryMixin
from .experiment import ExperimentMixin

class ScootExperiment(DBWriter, ScootQueryMixin, ExperimentMixin):
    """Experiment for scoot modelling."""

    @property
    def instance_table(self) -> TrafficInstanceTable:
        """Traffic instance table."""
        return TrafficInstanceTable

    @property
    def model_table(self) -> TrafficModelTable:
        """Traffic model table."""
        return TrafficModelTable

    def update_remote_tables(self):
        """Update the instance, data and model tables."""
        ExperimentMixin.update_remote_tables(self)
