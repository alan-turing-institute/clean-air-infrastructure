"""
OS Highway feature extraction
"""
from .static_features import StaticFeatures
from .feature_funcs import sum_length
from ..databases.tables import OSHighway


class OSHighwayFeatures(StaticFeatures):
    """Extract features for OSHighways"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        self.table = OSHighway
        # List of features to extract
        self.features = {
            "total_road_length": {"type": "geom",
                                  "feature_dict": {},
                                  "aggfunc": sum_length},
            "total_a_road_primary_length":  {"type": "geom",
                                             "feature_dict": {"route_hierarchy": ["A Road Primary"]},
                                             "aggfunc": sum_length},
            "total_a_road_length": {"type": "geom",
                                    "feature_dict": {"route_hierarchy": ["A Road"]},
                                    "aggfunc": sum_length},
            "total_b_road_length": {"type": "geom",
                                    "feature_dict": {"route_hierarchy": ["B Road", "B Road Primary"]},
                                    "aggfunc": sum_length},
            "total_length": {"type": "geom",
                             "feature_dict":  {"route_hierarchy": ["*"]},
                             "aggfunc": sum_length},
        }
