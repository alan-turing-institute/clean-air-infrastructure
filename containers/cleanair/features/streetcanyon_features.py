"""
UKMAP feature extraction
"""
from sqlalchemy import func, literal, or_
from .static_features import StaticFeatures
from .feature_funcs import sum_area, min_
from ..databases.tables import StreetCanyon


class StreetCanyonFeatures(StaticFeatures):
    """Extract features for StreetCanyon"""
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        self.table = StreetCanyon
        # List of features to extract
        self.features = {
            "min_ratio_avg": {"type": "value", "feature_dict": {"ratio_avg": ["*"]}, 'aggfunc': min_},
        }
    