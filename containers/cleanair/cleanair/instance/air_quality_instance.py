"""Air quality instance."""

from .instance import Instance

class AirQualityInstance(Instance):
    """A model instance on air quality data."""

    def update_remote_tables(self):
        """Write instance to the air quality instance table."""
        