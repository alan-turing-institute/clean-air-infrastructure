"""Traffic instance."""

from cleanair.databases.tables import TrafficInstanceTable
from cleanair.instance import Instance

class TrafficInstance(Instance):
    """Traffic instance."""

    def update_remote_tables(self):
        """Write instance to the traffic modelling instance table."""
        records = [self.to_dict()]
        self.commit_records(
            records, on_conflict="ignore", table=TrafficInstanceTable
        )
