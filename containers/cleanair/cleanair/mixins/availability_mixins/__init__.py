"""Mixins for checking what data is available and what is missing in database tables"""

from .satellite_availability import SatelliteAvailabilityMixin
from .static_feature_availability import StaticFeatureAvailabilityMixin

__all__ = ["SatelliteAvailabilityMixin", "StaticFeatureAvailabilityMixin"]
