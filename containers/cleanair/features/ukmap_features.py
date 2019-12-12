"""
UKMAP feature extraction
"""
from .static_features import StaticFeatures
from .feature_funcs import sum_area, max_
from ..databases.tables import UKMap


class UKMapFeatures(StaticFeatures):
    """Extract features for UKMap"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        self.table = UKMap
        # List of features to extract
        self.features = {
            "building_height": {"type": "value", "feature_dict": {"calculated_height_of_building": ["*"]},
                                "aggfunc": max_},
            "flat": {"type": "geom", "feature_dict": {"feature_type": ["Vegetated", "Water"]}, 'aggfunc': sum_area},
            "grass": {"type": "geom", "feature_dict": {"feature_type": ["Vegetated"]}, 'aggfunc': sum_area},
            "hospitals": {"type": "geom", "feature_dict": {"landuse": ["Hospitals"]}, 'aggfunc': sum_area},
            "museums": {"type": "geom", "feature_dict": {"landuse": ["Museum"]}, 'aggfunc': sum_area},
            "park": {"type": "geom", "feature_dict": {"feature_type": ["Vegetated"],
                                                      "landuse": ["Recreational open space"]}, 'aggfunc': sum_area},
            "water": {"type": "geom", "feature_dict": {"feature_type": ["Water"]}, 'aggfunc': sum_area},
        }
