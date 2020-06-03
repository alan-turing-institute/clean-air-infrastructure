"""Air quality instance."""

from .instance import Instance
from ..databases.tables import AirQualityInstanceTable

class AirQualityInstance(Instance):
    """A model instance on air quality data."""

    def update_remote_tables(self):
        """Write instance to the air quality instance table."""
        records = [self.to_dict()]
        self.commit_records(records, on_conflict="ignore", table=AirQualityInstanceTable)